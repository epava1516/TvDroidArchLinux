//! Linux process lifetime channel, not an Android API or an isolation boundary.
//! The caller supplies identities/namespaces and an executable it trusts. The
//! protocol distinguishes diagnostic startup from normal component startup;
//! neither is a claim of complete runtime or APK readiness.
use std::{
    io::{self, Read, Write},
    os::{
        fd::{AsRawFd, FromRawFd, OwnedFd},
        unix::{net::UnixStream, process::CommandExt},
    },
    process::{Child, Command, ExitStatus},
    time::{Duration, Instant},
};

#[derive(Clone, Copy, Debug, PartialEq, Eq)]
pub enum Startup {
    Component,
    Diagnostic,
}

/// An original Android shutdown request is a component failure, never a host reboot.
#[derive(Debug, PartialEq, Eq)]
pub enum NativeFailure {
    ShutdownRequested(Vec<u8>),
    ShutdownRequestTooLong,
}
impl std::fmt::Display for NativeFailure {
    fn fmt(&self, f: &mut std::fmt::Formatter<'_>) -> std::fmt::Result {
        match self {
            Self::ShutdownRequested(bytes) => {
                write!(f, "original Android shutdown requested: {bytes:02x?}")
            }
            Self::ShutdownRequestTooLong => {
                f.write_str("original Android shutdown request exceeds wire limit")
            }
        }
    }
}
impl std::error::Error for NativeFailure {}

fn check_failure(frame: &[u8]) -> io::Result<()> {
    if frame == b"ARCHTV_NATIVE_V1 FAILED_SHUTDOWN_OVERSIZE\n" {
        return Err(io::Error::other(NativeFailure::ShutdownRequestTooLong));
    }
    if let Some(hex) = frame.strip_prefix(b"ARCHTV_NATIVE_V1 FAILED_SHUTDOWN ") {
        let hex = hex.strip_suffix(b"\n").unwrap_or(hex);
        if hex.len() > 48 || !hex.len().is_multiple_of(2) {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "invalid shutdown request encoding",
            ));
        }
        let nibble = |c: u8| match c {
            b'0'..=b'9' => Some(c - b'0'),
            b'a'..=b'f' => Some(c - b'a' + 10),
            _ => None,
        };
        let mut bytes = Vec::new();
        for pair in hex.chunks_exact(2) {
            let (Some(a), Some(b)) = (nibble(pair[0]), nibble(pair[1])) else {
                return Err(io::Error::new(
                    io::ErrorKind::InvalidData,
                    "invalid shutdown request encoding",
                ));
            };
            bytes.push((a << 4) | b);
        }
        return Err(io::Error::other(NativeFailure::ShutdownRequested(bytes)));
    }
    Ok(())
}

pub struct NativeProcess {
    child: Option<Child>,
    pidfd: OwnedFd,
    control: UnixStream,
    started: bool,
    failure_observed: bool,
    partial_frame: Vec<u8>,
    protocol_failed: bool,
}

fn until(fd: i32, events: i16, deadline: Instant) -> io::Result<()> {
    loop {
        let left = deadline.saturating_duration_since(Instant::now());
        if left.is_zero() {
            return Err(io::Error::new(
                io::ErrorKind::TimedOut,
                "native process deadline expired",
            ));
        }
        let mut poll = libc::pollfd {
            fd,
            events,
            revents: 0,
        };
        let millis = left.as_millis().saturating_add(1).min(i32::MAX as u128) as i32;
        // The descriptor remains owned for this entire call.
        let result = unsafe { libc::poll(&mut poll, 1, millis) };
        if result > 0 {
            if poll.revents & libc::POLLNVAL != 0 {
                return Err(io::Error::other("invalid native process descriptor"));
            }
            return Ok(()); // Read/write/wait reports HUP and other errors precisely.
        }
        if result < 0 && io::Error::last_os_error().kind() != io::ErrorKind::Interrupted {
            return Err(io::Error::last_os_error());
        }
    }
}

impl NativeProcess {
    pub fn spawn(mut command: Command) -> io::Result<Self> {
        let (control, inherited) = UnixStream::pair()?;
        control.set_nonblocking(true)?;
        // Keep the inherited capability away from stdin/stdout/stderr even when
        // the caller has closed one of them. Parent-owned descriptors stay CLOEXEC.
        let fd = unsafe { libc::fcntl(inherited.as_raw_fd(), libc::F_DUPFD_CLOEXEC, 3) };
        if fd < 0 {
            return Err(io::Error::last_os_error());
        }
        let inherited = unsafe { OwnedFd::from_raw_fd(fd) };
        command.env("ARCHTV_NATIVE_CONTROL_FD", fd.to_string());
        unsafe {
            command.pre_exec(move || {
                let flags = libc::fcntl(fd, libc::F_GETFD);
                if flags < 0 || libc::fcntl(fd, libc::F_SETFD, flags & !libc::FD_CLOEXEC) < 0 {
                    return Err(io::Error::last_os_error());
                }
                Ok(())
            });
        }
        let mut child = command.spawn()?;
        drop(inherited);
        let raw = unsafe { libc::syscall(libc::SYS_pidfd_open, child.id(), 0) };
        if raw < 0 {
            let error = io::Error::last_os_error();
            let _ = child.kill();
            let _ = child.wait();
            return Err(error);
        }
        Ok(Self {
            child: Some(child),
            pidfd: unsafe { OwnedFd::from_raw_fd(raw as i32) },
            control,
            started: false,
            failure_observed: false,
            partial_frame: Vec::new(),
            protocol_failed: false,
        })
    }

    pub fn pid(&self) -> u32 {
        self.child.as_ref().expect("owned child").id()
    }
    pub fn pidfd(&self) -> i32 {
        self.pidfd.as_raw_fd()
    }

    fn line(&mut self, deadline: Instant) -> io::Result<Vec<u8>> {
        let result = self.read_line(deadline);
        if result
            .as_ref()
            .is_err_and(|e| e.kind() != io::ErrorKind::TimedOut)
        {
            self.protocol_failed = true;
        }
        result
    }

    // A deadline ends an observation, not the incoming frame. Keep its bounded
    // prefix until completion; otherwise a fragmented failure can lose its type.
    fn read_line(&mut self, deadline: Instant) -> io::Result<Vec<u8>> {
        loop {
            let mut byte = [0];
            match self.control.read(&mut byte) {
                Ok(0) => {
                    return Err(io::Error::new(
                        io::ErrorKind::UnexpectedEof,
                        "native lifetime channel closed",
                    ));
                }
                Ok(_) => {
                    self.partial_frame.push(byte[0]);
                    if byte[0] == b'\n' {
                        let line = std::mem::take(&mut self.partial_frame);
                        if let Err(error) = check_failure(&line) {
                            self.failure_observed =
                                error.get_ref().is_some_and(|e| e.is::<NativeFailure>());
                            return Err(error);
                        }
                        return Ok(line);
                    }
                    if self.partial_frame.len() >= 96 {
                        return Err(io::Error::new(
                            io::ErrorKind::InvalidData,
                            "native status frame too long",
                        ));
                    }
                }
                Err(e) if e.kind() == io::ErrorKind::WouldBlock => {
                    until(self.control.as_raw_fd(), libc::POLLIN, deadline)?
                }
                Err(e) if e.kind() == io::ErrorKind::Interrupted => {}
                Err(e) => return Err(e),
            }
        }
    }

    pub fn wait_started(&mut self, expected: Startup, timeout: Duration) -> io::Result<()> {
        if self.failure_observed {
            return Err(io::Error::other("native component already failed"));
        }
        if self.protocol_failed {
            return Err(io::Error::other("native protocol already failed"));
        }
        if self.started {
            return Err(io::Error::other("native startup already acknowledged"));
        }
        let expected = match expected {
            Startup::Component => b"ARCHTV_NATIVE_V1 STARTED\n".as_slice(),
            Startup::Diagnostic => b"ARCHTV_NATIVE_V1 DIAGNOSTIC_STARTED\n".as_slice(),
        };
        if self.line(Instant::now() + timeout)? != expected {
            self.protocol_failed = true;
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "unexpected native startup mode or protocol",
            ));
        }
        self.started = true;
        Ok(())
    }

    /// Collects the actual failed exit after a typed startup failure. The request
    /// string is diagnostic data; this API never executes a reboot or command.
    pub fn wait_failed(mut self, timeout: Duration) -> io::Result<ExitStatus> {
        if !self.failure_observed {
            return Err(io::Error::other("no typed native failure observed"));
        }
        until(
            self.pidfd.as_raw_fd(),
            libc::POLLIN,
            Instant::now() + timeout,
        )?;
        let status = self.child.as_mut().expect("owned child").wait()?;
        self.child.take();
        if status.success() {
            return Err(io::Error::other(
                "native failure reported with successful exit",
            ));
        }
        Ok(status)
    }

    /// Waits for cooperative completion and then the actual child exit. On an
    /// error Drop kills/reaps the owned child; descendants and uninterruptible
    /// kernel I/O require the caller's namespace/supervisor recovery policy.
    pub fn stop(mut self, timeout: Duration) -> io::Result<ExitStatus> {
        if !self.started {
            return Err(io::Error::other("native startup not acknowledged"));
        }
        let deadline = Instant::now() + timeout;
        let mut bytes = b"ARCHTV_NATIVE_V1 STOP\n".as_slice();
        while !bytes.is_empty() {
            match self.control.write(bytes) {
                Ok(0) => {
                    return Err(io::Error::new(
                        io::ErrorKind::WriteZero,
                        "native control write stopped",
                    ));
                }
                Ok(n) => bytes = &bytes[n..],
                Err(e) if e.kind() == io::ErrorKind::WouldBlock => {
                    until(self.control.as_raw_fd(), libc::POLLOUT, deadline)?
                }
                Err(e) if e.kind() == io::ErrorKind::Interrupted => {}
                Err(e) => return Err(e),
            }
        }
        if self.line(deadline)? != b"ARCHTV_NATIVE_V1 STOPPED\n" {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "native shutdown not acknowledged",
            ));
        }
        until(self.pidfd.as_raw_fd(), libc::POLLIN, deadline)?;
        let result = self.child.as_mut().expect("owned child").wait()?;
        self.child.take();
        if !result.success() {
            return Err(io::Error::other(format!("native child failed: {result}")));
        }
        Ok(result)
    }
}

impl Drop for NativeProcess {
    fn drop(&mut self) {
        if let Some(mut child) = self.child.take() {
            let _ = child.kill();
            let _ = child.wait();
        }
    }
}
