//! State of the host's single app virtual display, published after real Wayland configures.
use std::{
    fs::{File, OpenOptions},
    io::{self, Write},
    os::{fd::AsRawFd, unix::fs::OpenOptionsExt},
    path::{Path, PathBuf},
};

pub struct WindowPolicy {
    _lock: File,
    owner_start_ticks: u64,
    path: PathBuf,
    initial: [u32; 2],
    generation: u64,
    animator_scale: f32,
}
impl WindowPolicy {
    pub fn new(data: &Path, size: [u32; 2]) -> io::Result<Self> {
        let animator_scale: f32 = std::env::var("ARCHTV_APK_ANIMATOR_SCALE")
            .unwrap_or_else(|_| "1".into())
            .parse()
            .map_err(io::Error::other)?;
        if !animator_scale.is_finite() || !(0.0..=10.0).contains(&animator_scale) {
            return Err(io::Error::other("Invalid Android animator scale policy"));
        }
        let lock = OpenOptions::new()
            .write(true)
            .create(true)
            .truncate(false)
            .custom_flags(libc::O_NOFOLLOW)
            .mode(0o600)
            .open(data.join("window-policy.lock"))?;
        if unsafe { libc::flock(lock.as_raw_fd(), libc::LOCK_EX | libc::LOCK_NB) } < 0 {
            return Err(io::Error::last_os_error());
        }
        let stale = data.join(format!("window-policy.{}.next", std::process::id()));
        match std::fs::remove_file(stale) {
            Ok(()) => {}
            Err(error) if error.kind() == io::ErrorKind::NotFound => {}
            Err(error) => return Err(error),
        }
        let process = std::fs::read_to_string("/proc/self/stat")?;
        let owner_start_ticks = process
            .rsplit_once(')')
            .and_then(|(_, tail)| tail.split_whitespace().nth(19))
            .ok_or_else(|| io::Error::other("Missing process start time"))?
            .parse()
            .map_err(io::Error::other)?;
        let mut policy = Self {
            _lock: lock,
            owner_start_ticks,
            path: data.join("window-policy.properties"),
            initial: size,
            generation: 0,
            animator_scale,
        };
        policy.publish(size)?;
        Ok(policy)
    }
    pub fn publish(&mut self, size: [u32; 2]) -> io::Result<()> {
        if size[0] == 0 || size[0] > 3840 || size[1] == 0 || size[1] > 2160 {
            return Err(io::Error::other("Invalid virtual display size"));
        }
        let generation = self
            .generation
            .checked_add(1)
            .ok_or_else(|| io::Error::other("Window generation exhausted"))?;
        let text = format!(
            "version=1\nsource=wayland-shm\nowner_pid={}\nowner_start_ticks={}\ngeneration={generation}\ninitial_width={}\ninitial_height={}\nwidth={}\nheight={}\ndensity=160\nnavigation_bar=false\nblast=false\nanimator_scale={}\n",
            std::process::id(),
            self.owner_start_ticks,
            self.initial[0],
            self.initial[1],
            size[0],
            size[1],
            self.animator_scale
        );
        let temporary = self
            .path
            .with_extension(format!("{}.next", std::process::id()));
        let result = (|| {
            let mut file = OpenOptions::new()
                .write(true)
                .create_new(true)
                .mode(0o600)
                .open(&temporary)?;
            file.write_all(text.as_bytes())?;
            drop(file);
            std::fs::rename(&temporary, &self.path)
        })();
        if result.is_err() {
            let _ = std::fs::remove_file(&temporary);
        }
        result?;
        self.generation = generation;
        Ok(())
    }
}
impl Drop for WindowPolicy {
    fn drop(&mut self) {
        let _ = std::fs::remove_file(&self.path);
    }
}

#[cfg(test)]
mod tests {
    #[test]
    fn exclusive_owner_preserves_live_state_and_releases_on_drop() {
        let stamp = std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap()
            .as_nanos();
        let directory = std::env::temp_dir().join(format!(
            "archtv-window-owner-{}-{stamp}",
            std::process::id()
        ));
        std::fs::create_dir(&directory).unwrap();
        std::fs::write(
            directory.join(format!("window-policy.{}.next", std::process::id())),
            b"stale",
        )
        .unwrap();
        let owner = super::WindowPolicy::new(&directory, [960, 540]).unwrap();
        let snapshot = directory.join("window-policy.properties");
        assert!(super::WindowPolicy::new(&directory, [800, 450]).is_err());
        assert!(snapshot.exists());
        drop(owner);
        assert!(!snapshot.exists());
        let replacement = super::WindowPolicy::new(&directory, [800, 450]).unwrap();
        assert!(snapshot.exists());
        drop(replacement);
        std::fs::remove_dir_all(directory).unwrap();
    }
}
