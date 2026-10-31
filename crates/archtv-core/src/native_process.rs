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

pub struct NativeProcess {
    child: Option<Child>,
    pidfd: OwnedFd,
    control: UnixStream,
    started: bool,
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
        })
    }

    pub fn pid(&self) -> u32 {
        self.child.as_ref().expect("owned child").id()
    }
    pub fn pidfd(&self) -> i32 {
        self.pidfd.as_raw_fd()
    }

    fn line(&mut self, deadline: Instant) -> io::Result<Vec<u8>> {
        let mut line = Vec::new();
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
                    line.push(byte[0]);
                    if byte[0] == b'\n' {
                        return Ok(line);
                    }
                    if line.len() >= 96 {
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
        if self.started {
            return Err(io::Error::other("native startup already acknowledged"));
        }
        let expected = match expected {
            Startup::Component => b"ARCHTV_NATIVE_V1 STARTED\n".as_slice(),
            Startup::Diagnostic => b"ARCHTV_NATIVE_V1 DIAGNOSTIC_STARTED\n".as_slice(),
        };
        if self.line(Instant::now() + timeout)? != expected {
            return Err(io::Error::new(
                io::ErrorKind::InvalidData,
                "unexpected native startup mode or protocol",
            ));
        }
        self.started = true;
        Ok(())
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
