use crate::model::{Action, Settings};
use archtv_core::desktop::{Application, data_directories, discover};
use std::{
    io::Read,
    path::{Path, PathBuf},
    process::{Child, Command, Stdio},
    sync::{
        Arc,
        atomic::{AtomicBool, Ordering},
        mpsc::{self, Receiver, SyncSender},
    },
    time::{Duration, Instant},
};
#[derive(Debug)]
pub enum Event {
    Loaded(Vec<Application>, Settings, String),
    Icon(String, Option<tiny_skia::Pixmap>),
    Status {
        volume: String,
        network: String,
        android: String,
    },
    Notice(String),
    Launched(String),
    Saved(Result<(), String>),
}
pub struct Workers {
    pub actions: SyncSender<Action>,
    pub assets: SyncSender<Vec<Application>>,
    pub events: Receiver<Event>,
    stop: Arc<AtomicBool>,
}
impl Drop for Workers {
    fn drop(&mut self) {
        self.stop.store(true, Ordering::Relaxed);
    }
}
pub fn start() -> Workers {
    let (events, event_rx) = mpsc::sync_channel(64);
    let (actions, action_rx) = mpsc::sync_channel(16);
    let (assets, asset_rx) = mpsc::sync_channel::<Vec<Application>>(4);
    let (refresh, refresh_rx) = mpsc::sync_channel(1);
    let stop = Arc::new(AtomicBool::new(false));
    let config = settings_path();
    let tx = events.clone();
    let stopped = stop.clone();
    let path = config.clone();
    std::thread::Builder::new()
        .name("archtv-assets".into())
        .spawn(move || {
            let locale = std::env::var("LC_ALL")
                .or_else(|_| std::env::var("LC_MESSAGES"))
                .or_else(|_| std::env::var("LANG"))
                .unwrap_or_else(|_| "es_ES".into());
            let dirs = data_directories();
            let apps = discover(&dirs, &locale);
            let (settings, notice) = load_settings(&path);
            if tx.send(Event::Loaded(apps, settings, notice)).is_err() {
                return;
            }
            while !stopped.load(Ordering::Relaxed) {
                if let Ok(apps) = asset_rx.recv_timeout(Duration::from_millis(200)) {
                    for app in apps.into_iter().take(20) {
                        if stopped.load(Ordering::Relaxed) {
                            return;
                        }
                        let icon =
                            icon_path(&app.icon, &dirs).and_then(|path| decode_icon(&path).ok());
                        if tx.send(Event::Icon(app.id, icon)).is_err() {
                            return;
                        }
                    }
                }
            }
        })
        .expect("asset worker");
    let tx = events.clone();
    let stopped = stop.clone();
    std::thread::Builder::new()
        .name("archtv-actions".into())
        .spawn(move || {
            let mut children: Vec<(String, Child)> = Vec::new();
            while !stopped.load(Ordering::Relaxed) {
                if let Ok(action) = action_rx.recv_timeout(Duration::from_millis(100)) {
                    let outcome: Result<String, String> = match action {
                        Action::Save(settings) => {
                            let result = save_settings(&config, &settings);
                            let _ = tx.send(Event::Saved(result));
                            Ok(String::new())
                        }
                        Action::Launch(app) => launch(&app).map(|child| {
                            println!("SHELL_APP_STARTED id={} pid={}", app.id, child.id());
                            children.push((app.name.clone(), child));
                            let _ = tx.send(Event::Launched(app.id));
                            format!("Abriendo {}…", app.name)
                        }),
                        Action::Volume(delta) => run(
                            "wpctl",
                            &[
                                "set-volume",
                                "-l",
                                "1.0",
                                "@DEFAULT_AUDIO_SINK@",
                                &format!(
                                    "{}%{}",
                                    delta.unsigned_abs(),
                                    if delta > 0 { "+" } else { "-" }
                                ),
                            ],
                            Duration::from_secs(2),
                        )
                        .map(|_| "Volumen actualizado".into()),
                        Action::Mute => run(
                            "wpctl",
                            &["set-mute", "@DEFAULT_AUDIO_SINK@", "toggle"],
                            Duration::from_secs(2),
                        )
                        .map(|_| "Sonido actualizado".into()),
                        Action::Wifi => run("nmcli", &["radio", "wifi"], Duration::from_secs(2))
                            .and_then(|value| {
                                run(
                                    "nmcli",
                                    &[
                                        "radio",
                                        "wifi",
                                        if value.trim() == "enabled" {
                                            "off"
                                        } else {
                                            "on"
                                        },
                                    ],
                                    Duration::from_secs(2),
                                )
                            })
                            .map(|_| "Radio Wi-Fi actualizada".into()),
                        Action::Refresh => Ok("Consultando estado…".into()),
                        Action::AndroidStart => {
                            let mut cmd = Command::new("waydroid");
                            cmd.args(["session", "start"])
                                .env_remove("WAYLAND_SOCKET")
                                .env_remove("ARCHTV_CONTROL_FD")
                                .stdin(Stdio::null())
                                .stdout(Stdio::null())
                                .stderr(Stdio::null());
                            cmd.spawn()
                                .map(|child| {
                                    children.push(("Sesión Android".into(), child));
                                    "Arrancando Android; esperando confirmación…".into()
                                })
                                .map_err(|error| error.to_string())
                        }
                        Action::AndroidStop => {
                            run("waydroid", &["session", "stop"], Duration::from_secs(5))
                                .map(|_| "Sesión Android detenida".into())
                        }
                        Action::Quit | Action::Resume => Ok(String::new()),
                    };
                    match outcome {
                        Ok(text) if !text.is_empty() => {
                            let _ = tx.send(Event::Notice(text));
                        }
                        Err(error) => {
                            let _ =
                                tx.send(Event::Notice(format!("No se pudo completar: {error}")));
                        }
                        _ => (),
                    }
                    let _ = refresh.try_send(());
                }
                children.retain_mut(|(name, child)| match child.try_wait() {
                    Ok(Some(status)) => {
                        if !status.success() {
                            let _ = tx.send(Event::Notice(format!(
                                "{name} terminó con error ({status})"
                            )));
                        }
                        false
                    }
                    Ok(None) => true,
                    Err(_) => false,
                });
            }
            // Apps intentionally survive a shell restart. The session control group
            // owns their lifetime; do not kill them when just the shell exits.
        })
        .expect("action worker");
    let stopped = stop.clone();
    std::thread::Builder::new()
        .name("archtv-status".into())
        .spawn(move || {
            while !stopped.load(Ordering::Relaxed) {
                let volume = run(
                    "wpctl",
                    &["get-volume", "@DEFAULT_AUDIO_SINK@"],
                    Duration::from_secs(2),
                )
                .map(|value| value.trim().replace("Volume:", "Volumen:"))
                .unwrap_or_else(|_| "Audio no disponible".into());
                let network = run(
                    "nmcli",
                    &["-t", "-f", "STATE", "general"],
                    Duration::from_secs(2),
                )
                .map(|value| value.trim().to_string())
                .unwrap_or_else(|_| "Red no disponible".into());
                let android = run("waydroid", &["status"], Duration::from_secs(2))
                    .map(|value| {
                        if value
                            .lines()
                            .find(|line| line.contains("Session:"))
                            .is_some_and(|line| line.contains("RUNNING"))
                        {
                            "Sesión activa · arranque por verificar".into()
                        } else {
                            "Sesión detenida".into()
                        }
                    })
                    .unwrap_or_else(|_| "Android no disponible".into());
                if events
                    .send(Event::Status {
                        volume,
                        network,
                        android,
                    })
                    .is_err()
                {
                    break;
                }
                let _ = refresh_rx.recv_timeout(Duration::from_secs(3));
            }
        })
        .expect("status worker");
    Workers {
        actions,
        assets,
        events: event_rx,
        stop,
    }
}
pub fn settings_path() -> PathBuf {
    std::env::var_os("XDG_CONFIG_HOME")
        .map(PathBuf::from)
        .unwrap_or_else(|| {
            PathBuf::from(std::env::var_os("HOME").unwrap_or_default()).join(".config")
        })
        .join("archtv/settings.json")
}
fn load_settings(path: &Path) -> (Settings, String) {
    if std::fs::metadata(path).is_ok_and(|meta| meta.len() > 1024 * 1024) {
        return (
            Settings::default(),
            "Configuración demasiado grande; no se sobrescribirá".into(),
        );
    }
    match std::fs::read(path) {
        Ok(bytes) if bytes.len() <= 1024 * 1024 => {
            match serde_json::from_slice::<Settings>(&bytes) {
                Ok(mut settings) if settings.version == 1 => {
                    for (list, limit) in [
                        (&mut settings.favorites, 512),
                        (&mut settings.hidden, 512),
                        (&mut settings.recent, 20),
                    ] {
                        let mut seen = std::collections::HashSet::new();
                        list.retain(|id| {
                            !id.is_empty() && id.len() <= 512 && seen.insert(id.clone())
                        });
                        list.truncate(limit);
                    }
                    (settings, "Aplicaciones listas".into())
                }
                _ => {
                    let backup = path.with_extension(format!(
                        "invalid-{}",
                        std::time::SystemTime::now()
                            .duration_since(std::time::UNIX_EPOCH)
                            .unwrap_or_default()
                            .as_nanos()
                    ));
                    if std::fs::copy(path, &backup).is_ok() {
                        (
                            Settings::default(),
                            "Se conservó una copia de la configuración no válida".into(),
                        )
                    } else {
                        (
                            Settings::default(),
                            "Configuración no válida; no se pudo guardar copia".into(),
                        )
                    }
                }
            }
        }
        Ok(_) => (
            Settings::default(),
            "Configuración demasiado grande; revisar el archivo".into(),
        ),
        Err(error) if error.kind() == std::io::ErrorKind::NotFound => {
            (Settings::default(), "Aplicaciones listas".into())
        }
        Err(error) => (
            Settings::default(),
            format!("No se pudo leer la configuración: {error}"),
        ),
    }
}
fn save_settings(path: &Path, settings: &Settings) -> Result<(), String> {
    use std::{io::Write, os::unix::fs::OpenOptionsExt};
    if path.exists() {
        let metadata = std::fs::metadata(path).map_err(|error| error.to_string())?;
        if metadata.len() > 1024 * 1024 {
            return Err("configuración demasiado grande; se conserva sin cambios".into());
        }
        let current = std::fs::read(path).map_err(|error| error.to_string())?;
        if !serde_json::from_slice::<Settings>(&current).is_ok_and(|old| old.version == 1) {
            let backup = path.with_extension(format!(
                "invalid-{}",
                std::time::SystemTime::now()
                    .duration_since(std::time::UNIX_EPOCH)
                    .unwrap_or_default()
                    .as_nanos()
            ));
            std::fs::copy(path, backup).map_err(|error| {
                format!("no se puede conservar la configuración anterior: {error}")
            })?;
        }
    }
    let parent = path.parent().ok_or("missing settings directory")?;
    std::fs::create_dir_all(parent).map_err(|error| error.to_string())?;
    let temp = path.with_extension(format!(
        "{}.{}.tmp",
        std::process::id(),
        std::time::SystemTime::now()
            .duration_since(std::time::UNIX_EPOCH)
            .unwrap_or_default()
            .as_nanos()
    ));
    let result = (|| -> Result<(), String> {
        let mut file = std::fs::OpenOptions::new()
            .write(true)
            .create_new(true)
            .mode(0o600)
            .open(&temp)
            .map_err(|error| error.to_string())?;
        file.write_all(&serde_json::to_vec_pretty(settings).map_err(|error| error.to_string())?)
            .map_err(|error| error.to_string())?;
        file.sync_all().map_err(|error| error.to_string())?;
        std::fs::rename(&temp, path).map_err(|error| error.to_string())?;
        std::fs::File::open(parent)
            .and_then(|directory| directory.sync_all())
            .map_err(|error| error.to_string())?;
        Ok(())
    })();
    if result.is_err() {
        let _ = std::fs::remove_file(temp);
    }
    result
}
fn launch(app: &Application) -> Result<Child, String> {
    let mut command = if app.terminal {
        let mut cmd = Command::new("foot");
        cmd.arg("--").args(&app.command);
        cmd
    } else {
        let mut cmd = Command::new(&app.command[0]);
        cmd.args(&app.command[1..]);
        cmd
    };
    command
        .env_remove("WAYLAND_SOCKET")
        .env_remove("ARCHTV_CONTROL_FD")
        .stdin(Stdio::null())
        .stdout(Stdio::null())
        .stderr(Stdio::null());
    if let Some(directory) = &app.directory {
        command.current_dir(directory);
    }
    command
        .spawn()
        .map_err(|error| format!("{}: {error}", app.name))
}
fn run(program: &str, args: &[&str], timeout: Duration) -> Result<String, String> {
    use std::os::unix::process::CommandExt;
    let parent = unsafe { libc::getpid() };
    let mut command = Command::new(program);
    unsafe {
        command.pre_exec(move || {
            if libc::prctl(libc::PR_SET_PDEATHSIG, libc::SIGTERM) != 0 || libc::getppid() != parent
            {
                return Err(std::io::Error::other("status helper parent changed"));
            }
            Ok(())
        });
    }
    let mut child = command
        .args(args)
        .env("LC_ALL", "C")
        .env_remove("WAYLAND_SOCKET")
        .env_remove("ARCHTV_CONTROL_FD")
        .stdin(Stdio::null())
        .stdout(Stdio::piped())
        .stderr(Stdio::null())
        .spawn()
        .map_err(|error| format!("{program}: {error}"))?;
    let start = Instant::now();
    loop {
        match child.try_wait() {
            Ok(Some(status)) => {
                let mut text = String::new();
                if let Some(stdout) = child.stdout.take() {
                    stdout
                        .take(16384)
                        .read_to_string(&mut text)
                        .map_err(|error| error.to_string())?;
                }
                return if status.success() {
                    Ok(text)
                } else {
                    Err(format!("{program}: {status}"))
                };
            }
            Ok(None) if start.elapsed() < timeout => std::thread::sleep(Duration::from_millis(20)),
            Ok(None) => {
                let _ = child.kill();
                let _ = child.wait();
                return Err(format!("{program}: tiempo de espera agotado"));
            }
            Err(error) => {
                let _ = child.kill();
                let _ = child.wait();
                return Err(error.to_string());
            }
        }
    }
}
fn icon_path(icon: &str, dirs: &[PathBuf]) -> Option<PathBuf> {
    if icon.is_empty() {
        return None;
    }
    let path = PathBuf::from(icon);
    if path.is_absolute() {
        return path.is_file().then_some(path);
    }
    if icon.contains('/') || icon.contains("..") {
        return None;
    }
    for dir in dirs {
        for theme in ["hicolor", "Adwaita"] {
            for size in ["128x128", "96x96", "64x64", "256x256", "scalable", "48x48"] {
                for kind in ["apps", "devices", "categories", "actions"] {
                    for ext in ["png", "svg"] {
                        let path = dir.join(format!("icons/{theme}/{size}/{kind}/{icon}.{ext}"));
                        if path.is_file() {
                            return Some(path);
                        }
                    }
                }
            }
        }
        for ext in ["png", "svg", "jpg", ""] {
            let path = dir.join("pixmaps").join(if ext.is_empty() {
                icon.to_string()
            } else {
                format!("{icon}.{ext}")
            });
            if path.is_file() {
                return Some(path);
            }
        }
    }
    None
}
fn decode_icon(path: &Path) -> Result<tiny_skia::Pixmap, String> {
    if std::fs::metadata(path)
        .map_err(|error| error.to_string())?
        .len()
        > 2 * 1024 * 1024
    {
        return Err("icon file too large".into());
    }
    let bytes = std::fs::read(path).map_err(|error| error.to_string())?;
    if path.extension().is_some_and(|ext| ext == "svg") {
        let mut options = resvg::usvg::Options::default();
        options.image_href_resolver.resolve_string = Box::new(|_, _| None);
        let tree =
            resvg::usvg::Tree::from_data(&bytes, &options).map_err(|error| error.to_string())?;
        let size = tree.size();
        let factor = (96.0 / size.width()).min(96.0 / size.height());
        let mut pixmap = tiny_skia::Pixmap::new(96, 96).ok_or("icon allocation")?;
        resvg::render(
            &tree,
            tiny_skia::Transform::from_scale(factor, factor),
            &mut pixmap.as_mut(),
        );
        Ok(pixmap)
    } else {
        let mut reader = image::ImageReader::new(std::io::Cursor::new(bytes))
            .with_guessed_format()
            .map_err(|error| error.to_string())?;
        let mut limits = image::Limits::default();
        limits.max_image_width = Some(2048);
        limits.max_image_height = Some(2048);
        limits.max_alloc = Some(32 * 1024 * 1024);
        reader.limits(limits);
        let image = reader
            .decode()
            .map_err(|error| error.to_string())?
            .thumbnail(96, 96)
            .to_rgba8();
        let (w, h) = image.dimensions();
        let mut data = image.into_raw();
        for pixel in data.chunks_exact_mut(4) {
            let alpha = u16::from(pixel[3]);
            for c in &mut pixel[..3] {
                *c = ((u16::from(*c) * alpha + 127) / 255) as u8;
            }
        }
        tiny_skia::Pixmap::from_vec(data, tiny_skia::IntSize::from_wh(w, h).ok_or("icon size")?)
            .ok_or_else(|| "icon pixmap".into())
    }
}
#[cfg(test)]
mod tests {
    use super::*;
    #[test]
    fn settings_roundtrip_and_corruption_backup_preserve_user_state() {
        let dir = std::env::temp_dir().join(format!("archtv-settings-{}", std::process::id()));
        std::fs::create_dir_all(&dir).unwrap();
        let path = dir.join("settings.json");
        let mut settings = Settings::default();
        settings.favorites.push("app.desktop".into());
        settings.hidden.push("other.desktop".into());
        save_settings(&path, &settings).unwrap();
        let (loaded, _) = load_settings(&path);
        assert_eq!(loaded.favorites, settings.favorites);
        assert_eq!(loaded.hidden, settings.hidden);
        std::fs::write(&path, b"broken").unwrap();
        let (_, notice) = load_settings(&path);
        assert!(notice.contains("copia"));
        assert!(
            std::fs::read_dir(&dir)
                .unwrap()
                .flatten()
                .any(|entry| entry.file_name().to_string_lossy().contains("invalid-"))
        );
        std::fs::remove_dir_all(dir).unwrap();
    }
}
