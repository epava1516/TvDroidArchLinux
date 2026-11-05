//! Own private inherited launcher capability. No public socket, shell command,
//! APK path, app_id trust or automatic mutation retry.
use crate::worker::Event;
use archtv_core::desktop::Application;
use std::{
    collections::HashSet,
    io::{self, Read, Write},
    os::{
        fd::{FromRawFd, RawFd},
        unix::net::UnixStream,
    },
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
        mpsc::{self, SyncSender},
    },
    time::{Duration, Instant},
};
pub enum Command {
    Launch {
        component: String,
        name: String,
        deadline: Instant,
    },
    Refresh,
}
fn import() -> io::Result<Option<UnixStream>> {
    let Some(value) = std::env::var_os("ARCHTV_LAUNCHER_FD") else {
        return Ok(None);
    };
    let fd: RawFd = value
        .to_str()
        .and_then(|v| v.parse().ok())
        .filter(|v| *v >= 3)
        .ok_or_else(|| io::Error::other("Invalid launcher capability FD"))?;
    let mut kind = 0;
    let mut length = std::mem::size_of_val(&kind) as libc::socklen_t;
    let mut peer: libc::ucred = unsafe { std::mem::zeroed() };
    let mut peer_length = std::mem::size_of_val(&peer) as libc::socklen_t;
    // A private socketpair is handed only to the supervised Home child. Seal
    // it before any asset/action/status worker can spawn another process.
    if unsafe {
        libc::getsockopt(
            fd,
            libc::SOL_SOCKET,
            libc::SO_TYPE,
            (&mut kind as *mut i32).cast(),
            &mut length,
        )
    } != 0
        || kind != libc::SOCK_STREAM
        || unsafe {
            libc::getsockopt(
                fd,
                libc::SOL_SOCKET,
                libc::SO_PEERCRED,
                (&mut peer as *mut libc::ucred).cast(),
                &mut peer_length,
            )
        } != 0
        || peer.uid != unsafe { libc::geteuid() }
        || peer.gid != unsafe { libc::getegid() }
    {
        return Err(io::Error::other("Invalid launcher capability peer/type"));
    }
    let flags = unsafe { libc::fcntl(fd, libc::F_GETFD) };
    if flags < 0 || unsafe { libc::fcntl(fd, libc::F_SETFD, flags | libc::FD_CLOEXEC) } < 0 {
        return Err(io::Error::last_os_error());
    }
    Ok(Some(unsafe { UnixStream::from_raw_fd(fd) }))
}
fn remaining(deadline: Instant) -> io::Result<Duration> {
    deadline
        .checked_duration_since(Instant::now())
        .filter(|d| !d.is_zero())
        .ok_or_else(|| io::Error::new(io::ErrorKind::TimedOut, "Launcher operation deadline"))
}
fn write(stream: &mut UnixStream, mut bytes: &[u8], deadline: Instant) -> io::Result<()> {
    while !bytes.is_empty() {
        stream.set_write_timeout(Some(remaining(deadline)?))?;
        let n = stream.write(bytes)?;
        if n == 0 {
            return Err(io::ErrorKind::WriteZero.into());
        }
        bytes = &bytes[n..];
    }
    Ok(())
}
fn read(stream: &mut UnixStream, mut bytes: &mut [u8], deadline: Instant) -> io::Result<()> {
    while !bytes.is_empty() {
        stream.set_read_timeout(Some(remaining(deadline)?))?;
        let n = stream.read(bytes)?;
        if n == 0 {
            return Err(io::ErrorKind::UnexpectedEof.into());
        }
        bytes = &mut bytes[n..];
    }
    Ok(())
}
fn rpc(
    stream: &mut UnixStream,
    id: u32,
    target: Option<&str>,
    deadline: Instant,
) -> io::Result<serde_json::Value> {
    let request = if let Some(component) = target {
        serde_json::json!({"id":id,"op":"launch","component":component})
    } else {
        serde_json::json!({"id":id,"op":"list"})
    };
    let bytes = serde_json::to_vec(&request)?;
    if bytes.len() > 4096 {
        return Err(io::Error::other("Oversized launcher request"));
    }
    write(stream, &(bytes.len() as u32).to_be_bytes(), deadline)?;
    write(stream, &bytes, deadline)?;
    let mut size = [0u8; 4];
    read(stream, &mut size, deadline)?;
    let size = u32::from_be_bytes(size) as usize;
    if size == 0 || size > 2 * 1024 * 1024 {
        return Err(io::Error::other("Invalid launcher response length"));
    }
    let mut bytes = vec![0; size];
    read(stream, &mut bytes, deadline)?;
    let value: serde_json::Value = serde_json::from_slice(&bytes)?;
    if value.as_object().is_none_or(|o| o.len() != 4)
        || value["id"].as_u64() != Some(id.into())
        || value["status"].as_u64().is_none_or(|s| s > 4)
        || value["message"].as_str().is_none_or(|s| s.len() > 4096)
        || !value["entries"].is_array()
    {
        return Err(io::Error::other("Invalid launcher response"));
    }
    Ok(value)
}
fn catalog(value: &serde_json::Value) -> io::Result<Vec<Application>> {
    let entries: Vec<[String; 3]> = serde_json::from_value(value["entries"].clone())?;
    if entries.len() > 512 {
        return Err(io::Error::other("Oversized catalog"));
    }
    let mut seen = HashSet::new();
    let mut apps = Vec::new();
    let mut bytes = 0;
    for [component, label, category] in entries {
        bytes += component.len() + label.len() + category.len() + 12;
        if bytes > 262144
            || component.len() > 1024
            || component.contains('\0')
            || label.len() > 4096
            || label.contains('\0')
            || component
                .split_once('/')
                .is_none_or(|(a, b)| a.is_empty() || b.is_empty() || b.contains('/'))
            || (category != "android.intent.category.LAUNCHER"
                && category != "android.intent.category.LEANBACK_LAUNCHER")
            || !seen.insert(component.clone())
        {
            return Err(io::Error::other("Invalid original catalog"));
        }
        apps.push(Application {
            id: format!("apk:{component}"),
            name: label,
            comment: "Aplicación Android".into(),
            icon: String::new(),
            command: vec![],
            directory: None,
            terminal: false,
            android: true,
        });
    }
    Ok(apps)
}
pub fn start(events: SyncSender<Event>, stop: Arc<AtomicBool>) -> io::Result<SyncSender<Command>> {
    let (tx, rx) = mpsc::sync_channel(4);
    let Some(mut stream) = import()? else {
        let _ = events.send(Event::AndroidCatalog(
            vec![],
            "Runtime APK · control sin conexión".into(),
        ));
        return Ok(tx);
    };
    std::thread::Builder::new().name("archtv-original-launcher".into()).spawn(move||{
        let mut sequence=0u32;let mut refresh=Instant::now();let mut previous=String::new();
        while !stop.load(Ordering::Relaxed) {
            let command=match rx.recv_timeout(refresh.saturating_duration_since(Instant::now()).min(Duration::from_millis(200))) {
                Ok(c)=>Some(c),Err(mpsc::RecvTimeoutError::Disconnected)=>break,Err(mpsc::RecvTimeoutError::Timeout)=>None,
            };
            let (target,name,deadline)=match command {
                Some(Command::Launch{component,name,deadline})=>(Some(component),name,deadline),
                Some(Command::Refresh)=>(None,String::new(),Instant::now()+Duration::from_secs(15)),
                None if Instant::now()>=refresh=>(None,String::new(),Instant::now()+Duration::from_secs(15)),
                None=>continue,
            };
            if deadline<=Instant::now(){let _=events.send(Event::Notice("La solicitud caducó antes de enviarse".into()));continue;}
            let Some(id)=sequence.checked_add(1) else{break;};sequence=id;
            let result=rpc(&mut stream,id,target.as_deref(),deadline);
            match result {
                Ok(value) if target.is_some()=>{
                    let status=value["status"].as_u64().unwrap();
                    let notice=match status {
                        0=>{println!("SHELL_APK_ORIGINAL_START_REQUEST_RETURNED id={id} NOT_FRAME_ACCEPTANCE");format!("Solicitud enviada: {name}")},
                        4=>"Resultado del lanzamiento desconocido; no se reintentará".into(),
                        1=>"El servicio original rechazó el lanzamiento".into(),
                        _=>"No se pudo solicitar el lanzamiento original".into(),
                    };let _=events.send(Event::Notice(notice));refresh=Instant::now()+Duration::from_secs(5);
                },
                Ok(value)=>{
                    // Exclude changing request ID when deciding if the catalog
                    // changes. No periodic notices or UI redraw for same data.
                    let signature=format!("{}:{}",value["status"],value["entries"]);
                    if signature!=previous {
                        let (apps,status)=if value["status"]==0 {
                            match catalog(&value){Ok(apps)=>(apps,"Runtime APK · catálogo original"),Err(_)=>{break;}}
                        }else{(vec![],"Runtime APK · catálogo no disponible")};
                        if events.send(Event::AndroidCatalog(apps,status.into())).is_err(){break;}previous=signature;
                    }
                    refresh=Instant::now()+Duration::from_secs(5);
                },
                Err(error)=>{
                    eprintln!("SHELL_LAUNCHER_TRANSPORT_ENDED {error}");
                    if target.is_some(){let _=events.send(Event::Notice("Lanzamiento sin respuesta confirmada; no se reintentará".into()));}
                    break;
                },
            }
        }
        let _=events.send(Event::AndroidCatalog(vec![],"Runtime APK · control desconectado".into()));
    })?;
    Ok(tx)
}

#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn catalog_rejects_duplicates_nul_and_unexpected_categories() {
        let row = serde_json::json!([
            "com.example/com.example.Main",
            "Aplicación",
            "android.intent.category.LAUNCHER"
        ]);
        assert_eq!(
            catalog(&serde_json::json!({"entries":[row.clone()]}))
                .unwrap()
                .len(),
            1
        );
        assert!(catalog(&serde_json::json!({"entries":[row.clone(),row]})).is_err());
        assert!(catalog(&serde_json::json!({"entries":[["com.example/Main","Nul\u{0}label","android.intent.category.LAUNCHER"]]})).is_err());
        assert!(catalog(&serde_json::json!({"entries":[["com.example/Main","Label","android.intent.category.HOME"]]})).is_err());
    }
    #[test]
    fn private_rpc_rejects_reply_for_another_request() {
        let (mut client, mut server) = UnixStream::pair().unwrap();
        let worker = std::thread::spawn(move || {
            let mut size = [0; 4];
            server.read_exact(&mut size).unwrap();
            let mut bytes = vec![0; u32::from_be_bytes(size) as usize];
            server.read_exact(&mut bytes).unwrap();
            let response = serde_json::to_vec(
                &serde_json::json!({"id":2,"status":0,"message":"","entries":[]}),
            )
            .unwrap();
            server
                .write_all(&(response.len() as u32).to_be_bytes())
                .unwrap();
            server.write_all(&response).unwrap();
        });
        assert!(
            rpc(
                &mut client,
                1,
                None,
                Instant::now() + Duration::from_secs(2)
            )
            .is_err()
        );
        worker.join().unwrap();
    }
}
