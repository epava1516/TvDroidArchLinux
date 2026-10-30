use crate::model::Message;
use smithay_client_toolkit::reexports::calloop::channel::SyncSender;
use std::{
    io::{BufRead, BufReader, Read, Write},
    os::unix::{fs::OpenOptionsExt, process::CommandExt},
    path::Path,
    process::{Child, ChildStdin, Command, Stdio},
    thread::{self, JoinHandle},
    time::{Duration, Instant},
};
pub type Update = Result<Message, String>;
pub struct Backend {
    child: Child,
    input: Option<ChildStdin>,
    reader: Option<JoinHandle<()>>,
}
pub struct Launch<'a> {
    pub art: &'a Path,
    pub dex: &'a Path,
    pub apk: &'a Path,
    pub activity: &'a str,
    pub data: &'a Path,
    pub log: &'a Path,
}
impl Backend {
    pub fn start(
        launch: Launch<'_>,
        sender: SyncSender<Update>,
        size: [u32; 2],
    ) -> Result<Self, Box<dyn std::error::Error>> {
        let Launch {
            art,
            dex,
            apk,
            activity,
            data,
            log,
        } = launch;
        let [width, height] = size;
        let error_log = std::fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .mode(0o600)
            .open(log)?;
        let art_data = data.join("art-data");
        std::fs::create_dir_all(&art_data)?;
        let classpath = std::env::join_paths([dex, apk])?;
        let resources_library = std::env::var_os("ARCHTV_APK_RESOURCES_LIBRARY")
            .ok_or("ARCHTV_APK_RESOURCES_LIBRARY is required")?;
        let resources_library = std::fs::canonicalize(resources_library)?;
        let library = std::env::var_os("ARCHTV_APK_LINUX_LIBRARY")
            .ok_or("ARCHTV_APK_LINUX_LIBRARY is required")?;
        let library = std::fs::canonicalize(library)?;
        let mut command = Command::new(art.join("bin/art"));
        command
            .args(["--64", "--no-compile", "--", "-Xint"])
            .arg(format!("-Darchtv.linux.library={}", library.display()))
            .arg(format!(
                "-Darchtv.resources.library={}",
                resources_library.display()
            ))
            .arg(format!("-Darchtv.display.width={width}"))
            .arg(format!("-Darchtv.display.height={height}"))
            .arg("-cp")
            .arg(classpath)
            .arg("org.archtv.apkruntime.Main")
            .arg(apk)
            .arg(activity)
            .arg(data.join("app-data"))
            .env_remove("LD_PRELOAD")
            .env_remove("LD_LIBRARY_PATH")
            .env_remove("CLASSPATH")
            .env("ANDROID_DATA", art_data)
            .env("ANDROID_LOG_TAGS", "*:w")
            .stdin(Stdio::piped())
            .stdout(Stdio::piped())
            .stderr(error_log);
        // A separate group permits bounded teardown of the launcher and ART together.
        unsafe {
            command.pre_exec(|| {
                if libc::setpgid(0, 0) < 0 {
                    return Err(std::io::Error::last_os_error());
                }
                Ok(())
            });
        }
        let mut child = command.spawn()?;
        let input = child.stdin.take();
        let output = child.stdout.take().ok_or("No ART output pipe")?;
        let reader = thread::spawn(move || {
            let mut stream = BufReader::new(output);
            loop {
                let mut line = Vec::new();
                let result = stream
                    .by_ref()
                    .take(1024 * 1024 + 1)
                    .read_until(b'\n', &mut line);
                let update = match result {
                    Ok(0) => break,
                    Ok(_) if line.len() <= 1024 * 1024 && line.last() == Some(&b'\n') => {
                        serde_json::from_slice::<Message>(&line).map_err(|error| error.to_string())
                    }
                    Ok(_) => Err("ART message exceeds budget or lacks terminator".into()),
                    Err(error) => Err(error.to_string()),
                };
                let failed = update.is_err();
                if sender.try_send(update).is_err() || failed {
                    break;
                }
            }
        });
        Ok(Self {
            child,
            input,
            reader: Some(reader),
        })
    }
    pub fn configure(&mut self, width: u32, height: u32) -> std::io::Result<()> {
        writeln!(
            self.input
                .as_mut()
                .ok_or_else(|| std::io::Error::other("ART input closed"))?,
            "configure {width} {height}"
        )
    }
    pub fn activate(&mut self) -> std::io::Result<()> {
        self.input
            .as_mut()
            .ok_or_else(|| std::io::Error::other("ART input closed"))?
            .write_all(b"activate\n")
    }
}
impl Drop for Backend {
    fn drop(&mut self) {
        if let Some(mut input) = self.input.take() {
            let _ = input.write_all(b"quit\n");
        }
        let deadline = Instant::now() + Duration::from_secs(2);
        while Instant::now() < deadline {
            if self.child.try_wait().ok().flatten().is_some() {
                break;
            }
            thread::sleep(Duration::from_millis(10));
        }
        // The process group is private to this child, including the bash launcher.
        unsafe {
            libc::kill(-(self.child.id() as i32), libc::SIGKILL);
        }
        let _ = self.child.wait();
        if let Some(reader) = self.reader.take() {
            let _ = reader.join();
        }
    }
}
