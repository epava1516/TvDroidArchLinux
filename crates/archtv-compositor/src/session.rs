//! Bounded supervision and private channels for the session shell.
use crate::state::{ClientState, TvCompositor};
use smithay::reexports::calloop::{
    EventLoop, Interest, Mode, PostAction,
    generic::Generic,
    timer::{TimeoutAction, Timer},
};
use std::{
    cell::RefCell,
    collections::VecDeque,
    io::{ErrorKind, Read},
    os::fd::AsRawFd,
    os::unix::{net::UnixStream, process::CommandExt},
    process::{Child, Command},
    rc::Rc,
    sync::Arc,
    time::{Duration, Instant},
};
type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;

pub struct Supervisor {
    child: Option<Child>,
    command: Vec<String>,
    shell: bool,
    starts: VecDeque<Instant>,
    next_start: Option<Instant>,
}
impl Supervisor {
    fn spawn(
        &mut self,
        handle: &smithay::reexports::calloop::LoopHandle<'static, TvCompositor>,
        state: &mut TvCompositor,
    ) -> Result<()> {
        let mut command = Command::new(&self.command[0]);
        command
            .args(&self.command[1..])
            .env("WAYLAND_DISPLAY", &state.socket_name)
            .env_remove("WAYLAND_SOCKET")
            .env_remove("ARCHTV_CONTROL_FD");
        let mut inherited = Vec::new();
        if self.shell {
            // These connections are granted only to our child. A public Wayland
            // connection or a forged app_id never grants the shell role.
            let (server, client) = UnixStream::pair()?;
            state.display_handle.insert_client(
                server,
                Arc::new(ClientState {
                    is_shell: true,
                    ..Default::default()
                }),
            )?;
            command.env("WAYLAND_SOCKET", client.as_raw_fd().to_string());
            inherited.push(client);
            let (control, child_control) = UnixStream::pair()?;
            control.set_nonblocking(true)?;
            command.env("ARCHTV_CONTROL_FD", child_control.as_raw_fd().to_string());
            inherited.push(child_control);
            let mut pending = Vec::new();
            handle.insert_source(
                Generic::new(control, Interest::READ, Mode::Level),
                move |_, stream, state| {
                    let mut bytes = [0u8; 256];
                    for _ in 0..16 {
                        match (&**stream).read(&mut bytes) {
                            Ok(0) => return Ok(PostAction::Remove),
                            Ok(count) => {
                                pending.extend_from_slice(&bytes[..count]);
                                if pending.len() > 1024 {
                                    return Ok(PostAction::Remove);
                                }
                                while let Some(end) = pending.iter().position(|byte| *byte == b'\n')
                                {
                                    let line: Vec<_> = pending.drain(..=end).collect();
                                    match line.as_slice() {
                                        b"HOME\n" => state.show_home(),
                                        b"RESUME\n" => state.resume_application(),
                                        b"QUIT\n" => state.loop_signal.stop(),
                                        _ => tracing::warn!("SHELL_CONTROL_REJECTED"),
                                    }
                                }
                            }
                            Err(error) if error.kind() == ErrorKind::WouldBlock => break,
                            Err(error) => {
                                tracing::warn!(?error, "SHELL_CONTROL_CLOSED");
                                return Ok(PostAction::Remove);
                            }
                        }
                    }
                    Ok(PostAction::Continue)
                },
            )?;
        }
        let fds: Vec<_> = inherited.iter().map(AsRawFd::as_raw_fd).collect();
        // Only async-signal-safe libc calls are used between fork and exec.
        unsafe {
            command.pre_exec(move || {
                let mut mask: libc::sigset_t = std::mem::zeroed();
                libc::sigemptyset(&mut mask);
                if libc::sigprocmask(libc::SIG_SETMASK, &mask, std::ptr::null_mut()) != 0 {
                    return Err(std::io::Error::last_os_error());
                }
                for fd in &fds {
                    let flags = libc::fcntl(*fd, libc::F_GETFD);
                    if flags < 0 || libc::fcntl(*fd, libc::F_SETFD, flags & !libc::FD_CLOEXEC) < 0 {
                        return Err(std::io::Error::last_os_error());
                    }
                }
                Ok(())
            });
        }
        let child = command.spawn()?;
        tracing::info!(
            pid = child.id(),
            shell = self.shell,
            "SESSION_CHILD_STARTED"
        );
        self.child = Some(child);
        self.starts.push_back(Instant::now());
        self.next_start = None;
        Ok(())
    }
    fn tick(
        &mut self,
        handle: &smithay::reexports::calloop::LoopHandle<'static, TvCompositor>,
        state: &mut TvCompositor,
    ) -> Result<()> {
        if let Some(status) = self
            .child
            .as_mut()
            .map(Child::try_wait)
            .transpose()?
            .flatten()
        {
            tracing::warn!(?status, shell = self.shell, "SESSION_CHILD_EXITED");
            self.child.take();
            if self.shell {
                self.next_start = Some(Instant::now() + Duration::from_secs(1));
            }
        }
        if self.next_start.is_some_and(|next| Instant::now() >= next) {
            while self
                .starts
                .front()
                .is_some_and(|time| time.elapsed() > Duration::from_secs(30))
            {
                self.starts.pop_front();
            }
            if self.starts.len() >= 4 {
                self.next_start = None;
                tracing::error!("SHELL_RESTART_LIMIT: compositor and applications remain active");
            } else if let Err(error) = self.spawn(handle, state) {
                tracing::error!(%error, "SHELL_RESTART_FAILED");
                self.starts.push_back(Instant::now());
                self.next_start = Some(Instant::now() + Duration::from_secs(1));
            }
        }
        Ok(())
    }
    pub fn stop(&mut self) {
        if let Some(mut child) = self.child.take() {
            if child.try_wait().ok().flatten().is_none() {
                let _ = child.kill();
            }
            let _ = child.wait();
        }
    }
}
impl Drop for Supervisor {
    fn drop(&mut self) {
        self.stop();
    }
}

pub fn start(
    event_loop: &mut EventLoop<'static, TvCompositor>,
    state: &mut TvCompositor,
    command: Vec<String>,
    shell: bool,
) -> Result<Option<Rc<RefCell<Supervisor>>>> {
    if command.is_empty() {
        if shell {
            return Err("--shell requires a command after --".into());
        }
        return Ok(None);
    }
    let mut supervisor = Supervisor {
        child: None,
        command,
        shell,
        starts: VecDeque::new(),
        next_start: None,
    };
    if let Err(error) = supervisor.spawn(&event_loop.handle(), state) {
        if !shell {
            return Err(error);
        }
        tracing::error!(%error, "SHELL_START_FAILED");
        supervisor.starts.push_back(Instant::now());
        supervisor.next_start = Some(Instant::now() + Duration::from_secs(1));
    }
    let supervisor = Rc::new(RefCell::new(supervisor));
    let scheduler = supervisor.clone();
    event_loop.handle().insert_source(
        Timer::from_duration(Duration::from_millis(250)),
        move |_, _, state| {
            let handle = state.loop_handle.clone();
            if let Err(error) = scheduler.borrow_mut().tick(&handle, state) {
                tracing::error!(%error, "SESSION_SUPERVISOR_FAILED");
            }
            TimeoutAction::ToDuration(Duration::from_millis(250))
        },
    )?;
    Ok(Some(supervisor))
}
