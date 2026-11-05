//! Capability-only Home -> authenticated HWC -> original Android launcher RPC.
//! The display loop performs bounded nonblocking I/O; Binder runs in HWC's worker.
use crate::state::{ClientState, TvCompositor};
use smithay::reexports::wayland_server::{
    self, Client, DataInit, Dispatch, DisplayHandle, GlobalDispatch, New, Resource,
};
use std::{
    collections::HashSet,
    io::{ErrorKind, Read, Write},
    os::unix::net::UnixStream,
    time::{Duration, Instant},
};

#[allow(
    dead_code,
    non_camel_case_types,
    non_upper_case_globals,
    non_snake_case,
    unused_imports,
    unused_variables
)]
mod protocol {
    use smithay::reexports::wayland_server;
    pub mod __interfaces {
        use smithay::reexports::wayland_server::backend as wayland_backend;
        wayland_scanner::generate_interfaces!(
            "../../runtime/aosp/protocols/archtv-launcher-v1.xml"
        );
    }
    use self::__interfaces::*;
    wayland_scanner::generate_server_code!("../../runtime/aosp/protocols/archtv-launcher-v1.xml");
}
use protocol::archtv_launcher_bridge_v1::{ArchtvLauncherBridgeV1, Request};

struct Pending {
    sequence: u32,
    local: u32,
    generation: u64,
    operation: u32,
    deadline: Instant,
    entries: Vec<[String; 3]>,
    seen: HashSet<String>,
    bytes: usize,
}
#[derive(Default)]
pub struct LauncherBroker {
    provider: Option<ArchtvLauncherBridgeV1>,
    home: Option<UnixStream>,
    generation: u64,
    input: Vec<u8>,
    output: Vec<u8>,
    offset: usize,
    sequence: u32,
    last_local: u32,
    pending: Option<Pending>,
}
fn component(value: &str) -> bool {
    value.len() <= 1024
        && !value.contains('\0')
        && value
            .split_once('/')
            .is_some_and(|(a, b)| !a.is_empty() && !b.is_empty() && !b.contains('/'))
}
impl LauncherBroker {
    pub fn attach_home(&mut self, stream: UnixStream) -> std::io::Result<()> {
        stream.set_nonblocking(true)?;
        self.home = Some(stream);
        self.generation = self
            .generation
            .checked_add(1)
            .ok_or_else(|| std::io::Error::other("Home generation exhausted"))?;
        self.input.clear();
        self.output.clear();
        self.offset = 0;
        self.last_local = 0;
        // An old Home's transmitted mutation may still complete. Do not retry
        // it for the replacement Home, or misdeliver its result to a new FD.
        Ok(())
    }
    fn disconnect_home(&mut self) {
        self.home = None;
        self.input.clear();
        self.output.clear();
        self.offset = 0;
    }
    fn respond(
        &mut self,
        generation: u64,
        id: u32,
        status: u32,
        message: &str,
        entries: Vec<[String; 3]>,
    ) {
        if generation != self.generation || self.home.is_none() {
            return;
        }
        if !self.output.is_empty() {
            self.disconnect_home();
            return;
        }
        let bytes = serde_json::to_vec(
            &serde_json::json!({"id":id,"status":status,"message":message,"entries":entries}),
        )
        .expect("bounded strings serialize");
        if bytes.len() > 2 * 1024 * 1024 {
            self.disconnect_home();
            return;
        }
        self.output
            .extend_from_slice(&(bytes.len() as u32).to_be_bytes());
        self.output.extend(bytes);
    }
    fn request(&mut self, bytes: &[u8]) -> Result<(), ()> {
        let value: serde_json::Value = serde_json::from_slice(bytes).map_err(|_| ())?;
        let object = value.as_object().ok_or(())?;
        let id =
            u32::try_from(object.get("id").and_then(|v| v.as_u64()).ok_or(())?).map_err(|_| ())?;
        if id == 0 || id <= self.last_local {
            return Err(());
        }
        self.last_local = id;
        let op = object.get("op").and_then(|v| v.as_str()).ok_or(())?;
        let (operation, target) = match op {
            "list" if object.len() == 2 => (1, ""),
            "launch" if object.len() == 3 => {
                let target = object.get("component").and_then(|v| v.as_str()).ok_or(())?;
                if !component(target) {
                    return Err(());
                }
                (2, target)
            }
            _ => return Err(()),
        };
        if self.pending.is_some() {
            self.respond(
                self.generation,
                id,
                3,
                "Launcher busy; request not sent",
                vec![],
            );
            return Ok(());
        }
        let Some(provider) = self.provider.as_ref().filter(|p| p.is_alive()) else {
            self.respond(
                self.generation,
                id,
                3,
                "Original launcher connection unavailable",
                vec![],
            );
            return Ok(());
        };
        let Some(sequence) = self.sequence.checked_add(1) else {
            return Err(());
        };
        self.sequence = sequence;
        provider.call(sequence, operation, target.to_string());
        self.pending = Some(Pending {
            sequence,
            local: id,
            generation: self.generation,
            operation,
            deadline: Instant::now() + Duration::from_secs(12),
            entries: vec![],
            seen: HashSet::new(),
            bytes: 0,
        });
        Ok(())
    }
    pub fn pump(&mut self) {
        if self
            .pending
            .as_ref()
            .is_some_and(|p| Instant::now() >= p.deadline)
        {
            let p = self.pending.take().unwrap();
            self.respond(
                p.generation,
                p.local,
                if p.operation == 2 { 4 } else { 3 },
                "Original launcher response deadline; do not retry a launch",
                vec![],
            );
        }
        // Bound every event-loop turn, including a misbehaving private client.
        for _ in 0..4 {
            let mut bytes = [0u8; 4096];
            let result = match self.home.as_mut() {
                Some(home) => home.read(&mut bytes),
                None => break,
            };
            match result {
                Ok(0) => {
                    self.disconnect_home();
                    break;
                }
                Ok(n) => self.input.extend_from_slice(&bytes[..n]),
                Err(e) if e.kind() == ErrorKind::WouldBlock => break,
                Err(e) if e.kind() == ErrorKind::Interrupted => continue,
                Err(_) => {
                    self.disconnect_home();
                    break;
                }
            }
            while self.input.len() >= 4 {
                let length = u32::from_be_bytes(self.input[..4].try_into().unwrap()) as usize;
                if length == 0 || length > 4096 {
                    self.disconnect_home();
                    break;
                }
                if self.input.len() < 4 + length {
                    break;
                }
                let packet = self.input[4..4 + length].to_vec();
                self.input.drain(..4 + length);
                if self.request(&packet).is_err() {
                    self.disconnect_home();
                    break;
                }
            }
            if self.input.len() > 4100 {
                self.disconnect_home();
                break;
            }
        }
        for _ in 0..4 {
            if self.output.is_empty() {
                break;
            }
            let result = match self.home.as_mut() {
                Some(home) => home.write(&self.output[self.offset..]),
                None => break,
            };
            match result {
                Ok(0) => {
                    self.disconnect_home();
                    break;
                }
                Ok(n) => {
                    self.offset += n;
                    if self.offset == self.output.len() {
                        self.output.clear();
                        self.offset = 0;
                    }
                }
                Err(e) if e.kind() == ErrorKind::WouldBlock => break,
                Err(e) if e.kind() == ErrorKind::Interrupted => continue,
                Err(_) => {
                    self.disconnect_home();
                    break;
                }
            }
        }
    }
    fn provider_gone(&mut self) {
        self.provider = None;
        if let Some(p) = self.pending.take() {
            self.respond(
                p.generation,
                p.local,
                if p.operation == 2 { 4 } else { 3 },
                "Original launcher disconnected; mutation effect may be unknown",
                vec![],
            );
        }
    }
}
impl GlobalDispatch<ArchtvLauncherBridgeV1, ()> for TvCompositor {
    fn can_view(client: Client, _: &()) -> bool {
        client
            .get_data::<ClientState>()
            .is_some_and(|s| s.is_android_display)
    }
    fn bind(
        state: &mut Self,
        _: &DisplayHandle,
        client: &Client,
        resource: New<ArchtvLauncherBridgeV1>,
        _: &(),
        init: &mut DataInit<'_, Self>,
    ) {
        let resource = init.init(resource, ());
        if !client
            .get_data::<ClientState>()
            .is_some_and(|s| s.is_android_display)
            || state
                .launcher
                .provider
                .as_ref()
                .is_some_and(|p| p.is_alive())
        {
            resource.post_error(0u32, "Unauthenticated or duplicate launcher provider");
            return;
        }
        state.launcher.provider = Some(resource);
        tracing::info!("ORIGINAL_LAUNCHER_PROVIDER_BOUND NOT_CATALOG_OR_APK_ACCEPTANCE");
    }
}
impl Dispatch<ArchtvLauncherBridgeV1, ()> for TvCompositor {
    fn request(
        state: &mut Self,
        _: &Client,
        resource: &ArchtvLauncherBridgeV1,
        request: Request,
        _: &(),
        _: &DisplayHandle,
        _: &mut DataInit<'_, Self>,
    ) {
        if state
            .launcher
            .provider
            .as_ref()
            .is_none_or(|p| p.id() != resource.id())
        {
            resource.post_error(0u32, "Wrong launcher provider");
            return;
        }
        let sequence = match &request {
            Request::Entry { sequence, .. } | Request::Complete { sequence, .. } => *sequence,
            Request::Destroy => {
                return;
            }
        };
        if sequence == 0 || sequence > state.launcher.sequence {
            resource.post_error(0u32, "Unknown launcher sequence");
            return;
        }
        // Late replies remain evidence of an expired request, never a new action.
        let Some(p) = state
            .launcher
            .pending
            .as_mut()
            .filter(|p| p.sequence == sequence)
        else {
            tracing::warn!(sequence, "LAUNCHER_LATE_REPLY_IGNORED");
            return;
        };
        match request {
            Request::Entry {
                component: target,
                label,
                category,
                ..
            } => {
                p.bytes += target.len() + label.len() + category.len() + 12;
                if p.operation != 1
                    || !component(&target)
                    || label.len() > 4096
                    || label.contains('\0')
                    || (category != "android.intent.category.LAUNCHER"
                        && category != "android.intent.category.LEANBACK_LAUNCHER")
                    || p.entries.len() >= 512
                    || p.bytes > 262144
                    || !p.seen.insert(target.clone())
                {
                    resource.post_error(0u32, "Invalid or oversized original catalog");
                    return;
                }
                p.entries.push([target, label, category]);
            }
            Request::Complete {
                status, message, ..
            } => {
                if status > 4 || message.len() > 4096 {
                    resource.post_error(0u32, "Invalid launcher completion");
                    return;
                }
                let p = state.launcher.pending.take().unwrap();
                tracing::info!(
                    sequence,
                    status,
                    operation = p.operation,
                    entries = p.entries.len(),
                    "ORIGINAL_LAUNCHER_RPC_COMPLETED NOT_PRESENTATION_ACCEPTANCE"
                );
                state.launcher.respond(
                    p.generation,
                    p.local,
                    status,
                    &message,
                    if status == 0 { p.entries } else { vec![] },
                );
            }
            Request::Destroy => {}
        }
    }
    fn destroyed(
        state: &mut Self,
        _: wayland_server::backend::ClientId,
        resource: &ArchtvLauncherBridgeV1,
        _: &(),
    ) {
        if state
            .launcher
            .provider
            .as_ref()
            .is_some_and(|p| p.id() == resource.id())
        {
            state.launcher.provider_gone();
        }
    }
}
pub fn initialize(dh: &DisplayHandle) {
    dh.create_global::<TvCompositor, ArchtvLauncherBridgeV1, _>(1, ());
}

#[cfg(test)]
mod tests {
    use super::*;
    fn attach(broker: &mut LauncherBroker) -> UnixStream {
        let (server, client) = UnixStream::pair().unwrap();
        broker.attach_home(server).unwrap();
        client
            .set_read_timeout(Some(Duration::from_secs(2)))
            .unwrap();
        client
    }
    fn send(client: &mut UnixStream, value: serde_json::Value) {
        let bytes = serde_json::to_vec(&value).unwrap();
        client
            .write_all(&(bytes.len() as u32).to_be_bytes())
            .unwrap();
        client.write_all(&bytes).unwrap();
    }
    fn reply(client: &mut UnixStream) -> serde_json::Value {
        let mut size = [0; 4];
        client.read_exact(&mut size).unwrap();
        let mut bytes = vec![0; u32::from_be_bytes(size) as usize];
        client.read_exact(&mut bytes).unwrap();
        serde_json::from_slice(&bytes).unwrap()
    }
    #[test]
    fn public_wayland_client_cannot_view_launcher_global() {
        let display = wayland_server::Display::<TvCompositor>::new().unwrap();
        let (socket, _peer) = UnixStream::pair().unwrap();
        let client = display
            .handle()
            .insert_client(socket, std::sync::Arc::new(ClientState::default()))
            .unwrap();
        assert!(!<TvCompositor as GlobalDispatch<
            ArchtvLauncherBridgeV1,
            (),
        >>::can_view(client, &()));
    }
    #[test]
    fn private_fragmented_request_reports_unavailable_not_success() {
        let mut broker = LauncherBroker::default();
        let mut client = attach(&mut broker);
        let bytes = serde_json::to_vec(&serde_json::json!({"id":1,"op":"list"})).unwrap();
        let length = (bytes.len() as u32).to_be_bytes();
        client.write_all(&length[..2]).unwrap();
        broker.pump();
        assert!(broker.output.is_empty());
        client.write_all(&length[2..]).unwrap();
        client.write_all(&bytes).unwrap();
        broker.pump();
        let value = reply(&mut client);
        assert_eq!(value["id"], 1);
        assert_eq!(value["status"], 3);
        assert_eq!(value["entries"], serde_json::json!([]));
    }
    #[test]
    fn private_replay_or_extra_authority_fields_disconnect() {
        let mut broker = LauncherBroker::default();
        let mut client = attach(&mut broker);
        send(&mut client, serde_json::json!({"id":1,"op":"list"}));
        broker.pump();
        let _ = reply(&mut client);
        send(&mut client, serde_json::json!({"id":1,"op":"list"}));
        broker.pump();
        assert!(broker.home.is_none());
        let mut client = attach(&mut broker);
        send(
            &mut client,
            serde_json::json!({"id":1,"op":"list","user":10}),
        );
        broker.pump();
        assert!(broker.home.is_none());
    }
    #[test]
    fn old_home_completion_is_not_delivered_to_replacement() {
        let mut broker = LauncherBroker::default();
        let _old = attach(&mut broker);
        let old_generation = broker.generation;
        let _replacement = attach(&mut broker);
        broker.respond(old_generation, 1, 0, "Old response", vec![]);
        assert!(broker.output.is_empty());
        assert_ne!(broker.generation, old_generation);
    }
}
