//! Linux readiness backend for the original AOSP MessageQueue JNI contract.
use std::{
    collections::HashMap,
    io,
    os::fd::{AsRawFd, FromRawFd, OwnedFd, RawFd},
    sync::{
        Mutex,
        atomic::{AtomicBool, Ordering},
    },
};
#[derive(Clone, Copy)]
struct Registration {
    mask: i32,
    sequence: u32,
}
pub struct Queue {
    epoll: OwnedFd,
    wake: OwnedFd,
    polling: AtomicBool,
    registrations: Mutex<(u32, HashMap<RawFd, Registration>)>,
}

#[cfg(test)]
mod tests {
    use super::*;
    use std::{
        io::Write,
        os::unix::net::UnixStream,
        sync::Arc,
        thread,
        time::{Duration, Instant},
    };
    #[test]
    fn pending_wake_is_consumed_without_fd_dispatch() {
        let queue = Queue::new().unwrap();
        queue.wake().unwrap();
        queue
            .poll(0, |_, _| panic!("Wake is not a Java descriptor event"))
            .unwrap();
        assert!(!queue.is_polling());
        queue
            .poll(0, |_, _| panic!("No descriptor registered"))
            .unwrap();
    }
    #[test]
    fn another_thread_wakes_a_live_poll() {
        let queue = Arc::new(Queue::new().unwrap());
        let worker = Arc::clone(&queue);
        let (sender, receiver) = std::sync::mpsc::channel();
        let thread = thread::spawn(move || {
            worker
                .poll(3000, |_, _| panic!("No descriptor registered"))
                .unwrap();
            sender.send(()).unwrap();
        });
        let deadline = Instant::now() + Duration::from_secs(2);
        while !queue.is_polling() && Instant::now() < deadline {
            thread::sleep(Duration::from_millis(1));
        }
        assert!(queue.is_polling());
        queue.wake().unwrap();
        receiver.recv_timeout(Duration::from_secs(5)).unwrap();
        thread.join().unwrap();
    }
    #[test]
    fn readable_descriptor_callback_can_unregister() {
        let queue = Queue::new().unwrap();
        let (read, mut write) = UnixStream::pair().unwrap();
        queue.set_events(read.as_raw_fd(), 1).unwrap();
        write.write_all(b"x").unwrap();
        let mut calls = 0;
        queue
            .poll(1000, |fd, events| {
                assert_eq!(fd, read.as_raw_fd());
                assert_ne!(events & 1, 0);
                calls += 1;
                Ok(0)
            })
            .unwrap();
        assert_eq!(calls, 1);
        queue
            .poll(0, |_, _| panic!("Descriptor was removed"))
            .unwrap();
    }
    #[test]
    fn callback_replacement_preserves_new_registration() {
        let queue = Queue::new().unwrap();
        let (read, mut write) = UnixStream::pair().unwrap();
        let fd = read.as_raw_fd();
        queue.set_events(fd, 1).unwrap();
        write.write_all(b"x").unwrap();
        queue
            .poll(1000, |_, _| {
                queue.set_events(fd, 2)?;
                Ok(0)
            })
            .unwrap();
        let mut calls = 0;
        queue
            .poll(1000, |_, events| {
                assert_ne!(events & 2, 0);
                calls += 1;
                Ok(0)
            })
            .unwrap();
        assert_eq!(calls, 1);
    }
}
fn last_error() -> io::Error {
    io::Error::last_os_error()
}
fn fd(value: i32) -> io::Result<OwnedFd> {
    if value < 0 {
        Err(last_error())
    } else {
        // Ownership of each newly created descriptor is transferred once.
        Ok(unsafe { OwnedFd::from_raw_fd(value) })
    }
}
impl Queue {
    pub fn new() -> io::Result<Self> {
        let epoll = fd(unsafe { libc::epoll_create1(libc::EPOLL_CLOEXEC) })?;
        let wake = fd(unsafe { libc::eventfd(0, libc::EFD_NONBLOCK | libc::EFD_CLOEXEC) })?;
        let mut event = libc::epoll_event {
            events: libc::EPOLLIN as u32,
            u64: 0,
        };
        if unsafe {
            libc::epoll_ctl(
                epoll.as_raw_fd(),
                libc::EPOLL_CTL_ADD,
                wake.as_raw_fd(),
                &mut event,
            )
        } < 0
        {
            return Err(last_error());
        }
        Ok(Self {
            epoll,
            wake,
            polling: AtomicBool::new(false),
            registrations: Mutex::new((0, HashMap::new())),
        })
    }
    pub fn wake(&self) -> io::Result<()> {
        let value = 1_u64;
        loop {
            let result =
                unsafe { libc::write(self.wake.as_raw_fd(), (&value as *const u64).cast(), 8) };
            if result == 8 {
                return Ok(());
            }
            let error = last_error();
            match error.kind() {
                io::ErrorKind::Interrupted => continue,
                io::ErrorKind::WouldBlock => return Ok(()), // An unread wake already exists.
                _ => return Err(error),
            }
        }
    }
    pub fn is_polling(&self) -> bool {
        self.polling.load(Ordering::Acquire)
    }
    pub fn set_events(&self, descriptor: i32, mask: i32) -> io::Result<()> {
        if descriptor < 0 || mask & !7 != 0 {
            return Err(io::Error::other("Invalid FD or event mask"));
        }
        let mut state = self
            .registrations
            .lock()
            .map_err(|_| io::Error::other("Queue lock poisoned"))?;
        self.update(&mut state, descriptor, mask)
    }
    fn update(
        &self,
        state: &mut (u32, HashMap<RawFd, Registration>),
        descriptor: i32,
        mask: i32,
    ) -> io::Result<()> {
        if mask == 0 {
            state.1.remove(&descriptor);
            let result = unsafe {
                libc::epoll_ctl(
                    self.epoll.as_raw_fd(),
                    libc::EPOLL_CTL_DEL,
                    descriptor,
                    std::ptr::null_mut(),
                )
            };
            if result < 0 {
                let error = last_error();
                if !matches!(error.raw_os_error(), Some(libc::ENOENT | libc::EBADF)) {
                    return Err(error);
                }
            }
            return Ok(());
        }
        state.0 = state
            .0
            .checked_add(1)
            .ok_or_else(|| io::Error::other("FD generation exhausted"))?;
        let sequence = state.0;
        let mut events = libc::EPOLLERR | libc::EPOLLHUP;
        if mask & 1 != 0 {
            events |= libc::EPOLLIN;
        }
        if mask & 2 != 0 {
            events |= libc::EPOLLOUT;
        }
        let token = (u64::from(sequence) << 32) | (descriptor as u64 + 1);
        let mut event = libc::epoll_event {
            events: events as u32,
            u64: token,
        };
        let operation = if state.1.contains_key(&descriptor) {
            libc::EPOLL_CTL_MOD
        } else {
            libc::EPOLL_CTL_ADD
        };
        if unsafe { libc::epoll_ctl(self.epoll.as_raw_fd(), operation, descriptor, &mut event) } < 0
        {
            // Closing/reusing an FD can remove its old kernel registration before Java updates it.
            if operation != libc::EPOLL_CTL_MOD
                || last_error().raw_os_error() != Some(libc::ENOENT)
                || unsafe {
                    libc::epoll_ctl(
                        self.epoll.as_raw_fd(),
                        libc::EPOLL_CTL_ADD,
                        descriptor,
                        &mut event,
                    )
                } < 0
            {
                return Err(last_error());
            }
        }
        state.1.insert(descriptor, Registration { mask, sequence });
        Ok(())
    }
    pub fn poll(
        &self,
        timeout: i32,
        mut dispatch: impl FnMut(i32, i32) -> io::Result<i32>,
    ) -> io::Result<()> {
        if timeout < -1 {
            return Err(io::Error::other("Invalid timeout"));
        }
        if self.polling.swap(true, Ordering::AcqRel) {
            return Err(io::Error::other("Concurrent polling"));
        }
        let mut events = [libc::epoll_event { events: 0, u64: 0 }; 16];
        let count = unsafe {
            libc::epoll_wait(
                self.epoll.as_raw_fd(),
                events.as_mut_ptr(),
                events.len() as i32,
                timeout,
            )
        };
        self.polling.store(false, Ordering::Release);
        if count < 0 {
            let error = last_error();
            return if error.kind() == io::ErrorKind::Interrupted {
                Ok(())
            } else {
                Err(error)
            };
        }
        for event in events.iter().take(count as usize) {
            let token = event.u64;
            if token == 0 {
                let mut value = 0_u64;
                loop {
                    let result = unsafe {
                        libc::read(self.wake.as_raw_fd(), (&mut value as *mut u64).cast(), 8)
                    };
                    if result == 8 {
                        break;
                    }
                    let error = last_error();
                    if error.kind() == io::ErrorKind::Interrupted {
                        continue;
                    }
                    if error.kind() != io::ErrorKind::WouldBlock {
                        return Err(error);
                    }
                    break;
                }
                continue;
            }
            let descriptor = ((token & 0xffffffff) - 1) as i32;
            let sequence = (token >> 32) as u32;
            let registration = self
                .registrations
                .lock()
                .map_err(|_| io::Error::other("Queue lock poisoned"))?
                .1
                .get(&descriptor)
                .copied();
            let Some(registration) = registration.filter(|entry| entry.sequence == sequence) else {
                continue;
            };
            let mut mask = 0;
            if event.events & libc::EPOLLIN as u32 != 0 {
                mask |= 1;
            }
            if event.events & libc::EPOLLOUT as u32 != 0 {
                mask |= 2;
            }
            if event.events & (libc::EPOLLERR | libc::EPOLLHUP) as u32 != 0 {
                mask |= 4;
            }
            let requested = dispatch(descriptor, mask)?;
            if requested != registration.mask {
                let mut state = self
                    .registrations
                    .lock()
                    .map_err(|_| io::Error::other("Queue lock poisoned"))?;
                if state
                    .1
                    .get(&descriptor)
                    .is_some_and(|entry| entry.sequence == sequence)
                {
                    self.update(&mut state, descriptor, requested)?;
                }
            }
        }
        Ok(())
    }
}
