//! Android provider adapters, separate from UI and compositor policy.
use archtv_core::android::*;
use std::{
    fs::File,
    io::Read,
    os::fd::AsRawFd,
    os::unix::process::CommandExt,
    path::PathBuf,
    process::{Child, Command, Stdio},
    time::{Duration, Instant},
};

fn error(kind: ErrorKind, effect_applied: Option<bool>) -> ProviderError {
    ProviderError {
        kind,
        effect_applied,
    }
}
fn unsupported<T>() -> ProviderResult<T> {
    Err(error(ErrorKind::Unsupported, Some(false)))
}
struct Process(Child);
impl Drop for Process {
    fn drop(&mut self) {
        // Every helper has its own process group; descendants must not retain pipes.
        unsafe {
            libc::kill(-(self.0.id() as i32), libc::SIGKILL);
        }
        let _ = self.0.wait();
    }
}
fn drain(output: &mut impl Read, bytes: &mut Vec<u8>) -> ProviderResult<()> {
    let mut buffer = [0; 4096];
    loop {
        match output.read(&mut buffer) {
            Ok(0) => return Ok(()),
            Ok(count) if bytes.len() + count <= 65536 => bytes.extend_from_slice(&buffer[..count]),
            Ok(_) => return Err(error(ErrorKind::BackendFailure, None)),
            Err(value) if value.kind() == std::io::ErrorKind::WouldBlock => return Ok(()),
            Err(value) if value.kind() == std::io::ErrorKind::Interrupted => continue,
            Err(_) => return Err(error(ErrorKind::BackendFailure, None)),
        }
    }
}
fn run(program: &std::path::Path, args: &[&str], deadline: Instant) -> ProviderResult<String> {
    if Instant::now() >= deadline {
        return Err(error(ErrorKind::TimedOut, Some(false)));
    }
    let parent = unsafe { libc::getpid() };
    let mut command = Command::new(program);
    command
        .args(args)
        .process_group(0)
        .env("LC_ALL", "C")
        .env_remove("WAYLAND_SOCKET")
        .env_remove("ARCHTV_CONTROL_FD")
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null());
    unsafe {
        command.pre_exec(move || {
            if libc::prctl(libc::PR_SET_PDEATHSIG, libc::SIGKILL) != 0 || libc::getppid() != parent
            {
                return Err(std::io::Error::other("provider helper parent changed"));
            }
            Ok(())
        });
    }
    let child = command.spawn().map_err(|value| {
        error(
            match value.kind() {
                std::io::ErrorKind::NotFound => ErrorKind::Unavailable,
                std::io::ErrorKind::PermissionDenied => ErrorKind::PermissionDenied,
                _ => ErrorKind::BackendFailure,
            },
            Some(false),
        )
    })?;
    let mut child = Process(child);
    let mut output = child
        .0
        .stdout
        .take()
        .ok_or(error(ErrorKind::BackendFailure, None))?;
    let fd = output.as_raw_fd();
    let flags = unsafe { libc::fcntl(fd, libc::F_GETFL) };
    if flags < 0 || unsafe { libc::fcntl(fd, libc::F_SETFL, flags | libc::O_NONBLOCK) } < 0 {
        return Err(error(ErrorKind::BackendFailure, None));
    }
    let mut bytes = Vec::new();
    loop {
        if Instant::now() >= deadline {
            return Err(error(ErrorKind::TimedOut, None));
        }
        drain(&mut output, &mut bytes)?;
        match child.0.try_wait() {
            Ok(Some(status)) => {
                drain(&mut output, &mut bytes)?;
                return if status.success() {
                    String::from_utf8(bytes).map_err(|_| error(ErrorKind::BackendFailure, None))
                } else {
                    Err(error(ErrorKind::BackendFailure, None))
                };
            }
            Ok(None) => std::thread::sleep(
                Duration::from_millis(5).min(deadline.saturating_duration_since(Instant::now())),
            ),
            Err(_) => return Err(error(ErrorKind::BackendFailure, None)),
        }
    }
}

/// Initial read-only adapter. Unsupported mutations cannot accidentally start Android.
pub struct Waydroid {
    program: PathBuf,
}
impl Default for Waydroid {
    fn default() -> Self {
        Self {
            program: "waydroid".into(),
        }
    }
}
impl AndroidProvider for Waydroid {
    fn info(&self) -> ProviderInfo {
        ProviderInfo {
            contract_version: CONTRACT_VERSION,
            id: "waydroid".into(),
            version: env!("CARGO_PKG_VERSION").into(),
            android_api: None,
            abis: vec![],
            capabilities: vec![],
        }
    }
    fn status(&mut self, deadline: Instant) -> ProviderResult<RuntimeStatus> {
        let status = run(&self.program, &["status"], deadline)?;
        let session = match status
            .lines()
            .find_map(|line| line.trim().strip_prefix("Session:").map(str::trim))
        {
            Some("RUNNING") => SessionState::Running,
            Some("STOPPED") => SessionState::Stopped,
            Some("FROZEN") => SessionState::Suspended,
            _ => SessionState::Unknown,
        };
        let boot = if session == SessionState::Running {
            match run(
                &self.program,
                &["prop", "get", "sys.boot_completed"],
                deadline,
            ) {
                Ok(value) if value.trim() == "1" => BootState::Completed,
                Ok(_) => BootState::Starting,
                Err(_) => BootState::Unknown,
            }
        } else {
            BootState::Unknown
        };
        Ok(RuntimeStatus { session, boot })
    }
    fn start_runtime(&mut self, _: Instant) -> ProviderResult<()> {
        unsupported()
    }
    fn stop_runtime(&mut self, _: Instant) -> ProviderResult<()> {
        unsupported()
    }
    fn list_apps(&mut self, _: u32, _: Instant) -> ProviderResult<Vec<App>> {
        unsupported()
    }
    fn app_status(&mut self, _: &AppId, _: Instant) -> ProviderResult<AppState> {
        unsupported()
    }
    fn install_apk(
        &mut self,
        _: &File,
        _: u32,
        _: InstallPolicy,
        _: Instant,
    ) -> ProviderResult<InstallReceipt> {
        unsupported()
    }
    fn launch(&mut self, _: &AppId, _: Instant) -> ProviderResult<LaunchReceipt> {
        unsupported()
    }
    fn force_stop(&mut self, _: &AppId, _: Instant) -> ProviderResult<()> {
        unsupported()
    }
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::os::unix::fs::PermissionsExt;
    #[test]
    fn status_requires_exact_boot_value_and_rejects_stale_boot_for_stopped_session() {
        let directory =
            std::env::temp_dir().join(format!("archtv-provider-{}", std::process::id()));
        std::fs::create_dir_all(&directory).unwrap();
        let path = directory.join("waydroid");
        for (session, boot, ready) in [
            ("RUNNING", "1", true),
            ("RUNNING", "11", false),
            ("RUNNING", "", false),
            ("STOPPED", "1", false),
        ] {
            let script = format!(
                "#!/bin/sh\ncase \"$1\" in\nstatus) printf 'Session: {session}\\n';;\nprop) printf '{boot}\\n';;\nesac\n"
            );
            std::fs::write(&path, script).unwrap();
            std::fs::set_permissions(&path, std::fs::Permissions::from_mode(0o700)).unwrap();
            let mut provider = Waydroid {
                program: path.clone(),
            };
            let status = provider
                .status(Instant::now() + Duration::from_secs(5))
                .unwrap();
            assert_eq!(status.boot_ready(), ready);
            if session == "STOPPED" {
                assert_eq!(status.boot, BootState::Unknown);
            }
        }
        std::fs::remove_dir_all(directory).unwrap();
    }
    #[test]
    fn command_deadline_and_output_limit_do_not_wait_for_pipe_eof() {
        let shell = std::path::Path::new("/bin/sh");
        let result = run(
            shell,
            &["-c", "sleep 10"],
            Instant::now() + Duration::from_millis(50),
        );
        assert_eq!(result.unwrap_err().kind, ErrorKind::TimedOut);
        let result = run(
            shell,
            &["-c", "while :; do printf '0123456789abcdef'; done"],
            Instant::now() + Duration::from_secs(5),
        );
        assert_eq!(result.unwrap_err().kind, ErrorKind::BackendFailure);
    }
}
