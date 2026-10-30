use crate::{
    model::{Action, Key, Model, Page},
    render::Canvas,
    worker::{self, Event, Workers},
};
use smithay_client_toolkit::{
    compositor::{CompositorHandler, CompositorState, FrameCallbackData},
    delegate_registry,
    output::{OutputHandler, OutputState},
    reexports::{calloop::EventLoop, calloop_wayland_source::WaylandSource},
    registry::{ProvidesRegistryState, RegistryState},
    registry_handlers,
    seat::{
        Capability, SeatHandler, SeatState,
        keyboard::{KeyEvent, KeyboardHandler, Keysym, Modifiers, RawModifiers},
    },
    shell::{
        WaylandSurface,
        xdg::{
            XdgShell,
            window::{Window, WindowConfigure, WindowDecorations, WindowHandler},
        },
    },
    shm::{Shm, ShmHandler, slot::SlotPool},
};
use std::{
    collections::{HashMap, HashSet, VecDeque},
    io::Write,
    os::fd::{AsRawFd, FromRawFd},
    os::unix::net::UnixStream,
    path::PathBuf,
    time::{Duration, Instant},
};
use wayland_client::{
    Connection, QueueHandle,
    globals::registry_queue_init,
    protocol::{wl_keyboard, wl_output, wl_seat, wl_shm, wl_surface},
};
struct State {
    registry: RegistryState,
    output: OutputState,
    shm: Shm,
    window: Window,
    seats: SeatState,
    keyboard: Option<wl_keyboard::WlKeyboard>,
    pool: SlotPool,
    model: Model,
    canvas: Canvas,
    font: Vec<u8>,
    workers: Workers,
    control: Option<UnixStream>,
    icons: HashMap<String, Option<tiny_skia::Pixmap>>,
    icon_order: VecDeque<String>,
    requested: HashSet<String>,
    dirty: bool,
    frame_pending: bool,
    configured: bool,
    exit: bool,
    frames: u64,
    held: Option<(u32, Key, Instant)>,
    enter_pending: Option<Instant>,
    enter_long: bool,
    modifiers: Modifiers,
    pending_save: Option<crate::model::Settings>,
    save_in_flight: bool,
    quit_after_save: bool,
}
pub fn run(
    exit_after: Option<u64>,
    capture: Option<(u64, PathBuf)>,
) -> Result<(), Box<dyn std::error::Error>> {
    let control = control_fd()?;
    let connection = Connection::connect_to_env()?;
    let (globals, queue) = registry_queue_init::<State>(&connection)?;
    let qh = queue.handle();
    let compositor = CompositorState::bind(&globals, &qh)?;
    let shell = XdgShell::bind(&globals, &qh)?;
    let shm = Shm::bind(&globals, &qh)?;
    let window = shell.create_window(
        compositor.create_surface(&qh),
        WindowDecorations::RequestServer,
        &qh,
    );
    window.set_title("Arch TV");
    window.set_app_id("org.archtv.Shell");
    window.set_fullscreen(None);
    window.commit();
    let font = std::fs::read("/usr/share/fonts/TTF/DejaVuSans.ttf")?;
    let canvas = Canvas::new(1280, 720, &font)?;
    let pool = SlotPool::new(1280 * 720 * 4, &shm)?;
    let mut state = State {
        registry: RegistryState::new(&globals),
        output: OutputState::new(&globals, &qh),
        seats: SeatState::new(&globals, &qh),
        keyboard: None,
        shm,
        window,
        pool,
        model: Model::default(),
        canvas,
        font,
        workers: worker::start(),
        control,
        icons: HashMap::new(),
        icon_order: VecDeque::new(),
        requested: HashSet::new(),
        dirty: true,
        frame_pending: false,
        configured: false,
        exit: false,
        frames: 0,
        held: None,
        enter_pending: None,
        enter_long: false,
        modifiers: Modifiers::default(),
        pending_save: None,
        save_in_flight: false,
        quit_after_save: false,
    };
    let mut event_loop: EventLoop<State> = EventLoop::try_new()?;
    WaylandSource::new(connection.clone(), queue).insert(event_loop.handle())?;
    let started = Instant::now();
    let mut capture = capture;
    println!("SHELL_STARTED");
    while !state.exit {
        event_loop.dispatch(Some(Duration::from_millis(16)), &mut state)?;
        state.tick();
        if capture.as_ref().is_some_and(|(seconds, _)| {
            !state.model.loading && started.elapsed().as_secs() >= *seconds
        }) && state.configured
        {
            let (_, path) = capture.take().unwrap();
            state.canvas.shell(&state.model, &state.icons);
            state.canvas.pixmap.save_png(&path)?;
            println!("SHELL_CAPTURED {}", path.display());
        }
        if state.dirty && state.configured && !state.frame_pending {
            state.draw(&qh)?;
        }
        connection.flush()?;
        if exit_after.is_some_and(|seconds| started.elapsed().as_secs() >= seconds) {
            state.exit = true;
        }
    }
    println!("SHELL_STOPPED frames={}", state.frames);
    Ok(())
}
fn control_fd() -> Result<Option<UnixStream>, Box<dyn std::error::Error>> {
    let Some(value) = std::env::var_os("ARCHTV_CONTROL_FD") else {
        return Ok(None);
    };
    let fd = value.to_string_lossy().parse::<i32>()?;
    if fd < 3 {
        return Err("invalid shell control descriptor".into());
    }
    // The session supervisor transfers ownership of this private descriptor.
    let control = unsafe { UnixStream::from_raw_fd(fd) };
    let flags = unsafe { libc::fcntl(control.as_raw_fd(), libc::F_GETFD) };
    if flags < 0
        || unsafe { libc::fcntl(control.as_raw_fd(), libc::F_SETFD, flags | libc::FD_CLOEXEC) } < 0
    {
        return Err(std::io::Error::last_os_error().into());
    }
    control.set_nonblocking(true)?;
    Ok(Some(control))
}
impl State {
    fn control(&mut self, command: &[u8]) {
        if let Some(control) = self.control.as_mut() {
            if let Err(error) = control.write_all(command) {
                self.model.notice = format!("Control de sesión no disponible: {error}");
            }
        } else {
            self.model.notice = "Esta acción requiere la sesión Arch TV".into();
        }
    }
    fn actions(&mut self, actions: Vec<Action>) {
        for action in actions {
            match action {
                Action::Quit => {
                    self.quit_after_save = true;
                }
                Action::Resume => self.control(b"RESUME\n"),
                Action::Save(settings) => self.pending_save = Some(settings),
                action => {
                    if self.workers.actions.try_send(action).is_err() {
                        self.model.notice = "Hay otra acción pendiente; inténtalo de nuevo".into();
                    }
                }
            }
        }
    }
    fn key(&mut self, key: Key) {
        let actions = self.model.key(key);
        self.actions(actions);
        self.model.focus_glow = if self.model.settings.reduced_motion {
            255
        } else {
            160
        };
        self.dirty = true;
        println!(
            "SHELL_KEY {key:?} page={:?} band={} index={}",
            self.model.page, self.model.band, self.model.index
        );
    }
    fn tick(&mut self) {
        if self.model.focus_glow < 255 {
            self.model.focus_glow = self.model.focus_glow.saturating_add(24);
            self.dirty = true;
        }
        let events: Vec<_> = self.workers.events.try_iter().take(32).collect();
        for event in events {
            match event {
                Event::Loaded(apps, settings, notice) => {
                    println!("SHELL_CATALOG applications={}", apps.len());
                    self.model.apps = apps;
                    self.model.settings = settings;
                    self.model.notice = notice;
                    self.model.loading = false;
                    self.model.clamp();
                    self.dirty = true;
                }
                Event::Icon(id, icon) => {
                    self.requested.remove(&id);
                    if self.icons.len() >= 64 {
                        if let Some(old) = self.icon_order.pop_front() {
                            self.icons.remove(&old);
                        }
                    }
                    self.icon_order.push_back(id.clone());
                    self.icons.insert(id, icon);
                    self.dirty = true;
                }
                Event::Status {
                    volume,
                    network,
                    android,
                } => {
                    if self.model.volume != volume
                        || self.model.network != network
                        || self.model.android != android
                    {
                        self.model.volume = volume;
                        self.model.network = network;
                        self.model.android = android;
                        self.dirty = true;
                    }
                }
                Event::Notice(text) => {
                    println!("SHELL_NOTICE {text}");
                    self.model.notice = text;
                    self.dirty = true;
                }
                Event::Launched(id) => {
                    println!("SHELL_APP_LAUNCHED id={id}");
                    self.model.launched(id);
                    self.pending_save = Some(self.model.settings.clone());
                }
                Event::Saved(result) => {
                    self.save_in_flight = false;
                    match result {
                        Ok(()) => println!("SHELL_SETTINGS_SAVED"),
                        Err(error) => {
                            self.model.notice = format!("No se pudo guardar: {error}");
                            self.quit_after_save = false;
                            self.dirty = true;
                        }
                    }
                }
            }
        }
        if !self.save_in_flight {
            if let Some(settings) = self.pending_save.take() {
                match self.workers.actions.try_send(Action::Save(settings)) {
                    Ok(()) => self.save_in_flight = true,
                    Err(std::sync::mpsc::TrySendError::Full(Action::Save(settings))) => {
                        self.pending_save = Some(settings)
                    }
                    Err(_) => {
                        self.model.notice = "No se puede guardar la configuración".into();
                        self.quit_after_save = false;
                    }
                }
            }
        }
        if self.quit_after_save && self.pending_save.is_none() && !self.save_in_flight {
            self.control(b"QUIT\n");
            self.exit = true;
        }
        if self
            .enter_pending
            .is_some_and(|time| time.elapsed() >= Duration::from_millis(650))
            && !self.enter_long
        {
            self.enter_long = true;
            self.model.show_context();
            println!("SHELL_CONTEXT_OPEN");
            self.dirty = true;
        }
        if let Some((code, key, time)) = self.held {
            if Instant::now() >= time {
                self.key(key);
                self.held = Some((code, key, Instant::now() + Duration::from_millis(90)));
            }
        }
        if !self.model.loading {
            self.request_icons();
        }
    }
    fn request_icons(&mut self) {
        let wanted: Vec<_> = match self.model.page {
            Page::Home => {
                let mut row: Vec<_> = self
                    .model
                    .row(2)
                    .into_iter()
                    .skip(if self.model.band == 2 {
                        self.model.index.saturating_sub(3)
                    } else {
                        0
                    })
                    .take(5)
                    .cloned()
                    .collect();
                row.extend(
                    self.model
                        .row(3)
                        .into_iter()
                        .skip(if self.model.band == 3 {
                            self.model.index.saturating_sub(7)
                        } else {
                            0
                        })
                        .take(9)
                        .cloned(),
                );
                row
            }
            Page::Apps | Page::Recent => self
                .model
                .row(1)
                .into_iter()
                .skip((self.model.index / 5).saturating_sub(2) * 5)
                .take(20)
                .cloned()
                .collect(),
            Page::Search => self
                .model
                .row(2)
                .into_iter()
                .skip(if self.model.band == 2 {
                    self.model.index.saturating_sub(4)
                } else {
                    0
                })
                .take(8)
                .cloned()
                .collect(),
            Page::Settings => vec![],
        };
        let mut seen = HashSet::new();
        let wanted: Vec<_> = wanted
            .into_iter()
            .filter(|app| {
                !self.icons.contains_key(&app.id)
                    && !self.requested.contains(&app.id)
                    && seen.insert(app.id.clone())
            })
            .collect();
        if !wanted.is_empty() {
            let ids: Vec<_> = wanted.iter().map(|app| app.id.clone()).collect();
            if self.workers.assets.try_send(wanted).is_ok() {
                self.requested.extend(ids);
            }
        }
    }
    fn draw(&mut self, qh: &QueueHandle<Self>) -> Result<(), Box<dyn std::error::Error>> {
        self.canvas.shell(&self.model, &self.icons);
        let (width, height) = (self.canvas.pixmap.width(), self.canvas.pixmap.height());
        let (buffer, bytes) = self.pool.create_buffer(
            width as i32,
            height as i32,
            width as i32 * 4,
            wl_shm::Format::Argb8888,
        )?;
        // tiny-skia produces premultiplied RGBA; wl_shm ARGB8888 is native-endian.
        for (pixel, rgba) in bytes
            .chunks_exact_mut(4)
            .zip(self.canvas.pixmap.data().chunks_exact(4))
        {
            let argb = (u32::from(rgba[3]) << 24)
                | (u32::from(rgba[0]) << 16)
                | (u32::from(rgba[1]) << 8)
                | u32::from(rgba[2]);
            pixel.copy_from_slice(&argb.to_ne_bytes());
        }
        self.window
            .wl_surface()
            .damage_buffer(0, 0, width as i32, height as i32);
        self.window
            .wl_surface()
            .frame(qh, FrameCallbackData(self.window.wl_surface().clone()));
        buffer.attach_to(self.window.wl_surface())?;
        self.window.commit();
        self.frame_pending = true;
        self.dirty = false;
        self.frames += 1;
        println!(
            "SHELL_FRAME {} size={}x{} page={:?}",
            self.frames, width, height, self.model.page
        );
        Ok(())
    }
    fn press(&mut self, event: KeyEvent) {
        if self
            .held
            .as_ref()
            .is_some_and(|(code, _, _)| *code == event.raw_code)
        {
            return;
        }
        let sym = event.keysym;
        if sym == Keysym::Return || sym == Keysym::KP_Enter {
            if self.enter_pending.is_none() {
                self.enter_pending = Some(Instant::now());
                self.enter_long = false;
            }
            return;
        }
        let key = if sym == Keysym::Left {
            Some(Key::Left)
        } else if sym == Keysym::Right {
            Some(Key::Right)
        } else if sym == Keysym::Up {
            Some(Key::Up)
        } else if sym == Keysym::Down {
            Some(Key::Down)
        } else if sym == Keysym::Escape || sym == Keysym::XF86_Back {
            Some(Key::Back)
        } else if sym == Keysym::BackSpace {
            Some(if self.model.page == Page::Search {
                Key::Backspace
            } else {
                Key::Back
            })
        } else if sym == Keysym::Menu || sym == Keysym::F10 {
            Some(Key::Menu)
        } else {
            None
        };
        if let Some(key) = key {
            self.key(key);
            if matches!(
                key,
                Key::Left | Key::Right | Key::Up | Key::Down | Key::Backspace
            ) {
                self.held = Some((
                    event.raw_code,
                    key,
                    Instant::now() + Duration::from_millis(350),
                ));
            }
        } else if sym == Keysym::XF86_AudioRaiseVolume {
            self.actions(vec![Action::Volume(5)]);
        } else if sym == Keysym::XF86_AudioLowerVolume {
            self.actions(vec![Action::Volume(-5)]);
        } else if sym == Keysym::XF86_AudioMute {
            self.actions(vec![Action::Mute]);
        } else if !self.modifiers.ctrl && !self.modifiers.alt && !self.modifiers.logo {
            if let Some(text) = event.utf8 {
                for ch in text.chars() {
                    self.key(Key::Character(ch));
                }
            }
        }
    }
}
impl WindowHandler for State {
    fn request_close(&mut self, _: &Connection, _: &QueueHandle<Self>, _: &Window) {
        self.quit_after_save = true;
    }
    fn configure(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &Window,
        configure: WindowConfigure,
        _: u32,
    ) {
        let width = configure
            .new_size
            .0
            .map(|v| v.get())
            .unwrap_or(self.canvas.pixmap.width());
        let height = configure
            .new_size
            .1
            .map(|v| v.get())
            .unwrap_or(self.canvas.pixmap.height());
        if width > 7680 || height > 4320 {
            self.exit = true;
            return;
        }
        if width != self.canvas.pixmap.width() || height != self.canvas.pixmap.height() {
            match Canvas::new(width, height, &self.font) {
                Ok(canvas) => self.canvas = canvas,
                Err(error) => {
                    eprintln!("SHELL_CANVAS_ERROR {error}");
                    self.exit = true;
                    return;
                }
            }
        }
        self.configured = true;
        self.dirty = true;
        println!("SHELL_CONFIGURE {width}x{height}");
    }
}
impl CompositorHandler for State {
    fn frame(&mut self, _: &Connection, _: &QueueHandle<Self>, _: &wl_surface::WlSurface, _: u32) {
        self.frame_pending = false;
    }
    fn scale_factor_changed(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &wl_surface::WlSurface,
        _: i32,
    ) {
    }
    fn transform_changed(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &wl_surface::WlSurface,
        _: wl_output::Transform,
    ) {
    }
    fn surface_enter(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &wl_surface::WlSurface,
        _: &wl_output::WlOutput,
    ) {
    }
    fn surface_leave(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &wl_surface::WlSurface,
        _: &wl_output::WlOutput,
    ) {
    }
}
impl SeatHandler for State {
    fn seat_state(&mut self) -> &mut SeatState {
        &mut self.seats
    }
    fn new_seat(&mut self, _: &Connection, _: &QueueHandle<Self>, _: wl_seat::WlSeat) {}
    fn remove_seat(&mut self, _: &Connection, _: &QueueHandle<Self>, _: wl_seat::WlSeat) {}
    fn new_capability(
        &mut self,
        _: &Connection,
        qh: &QueueHandle<Self>,
        seat: wl_seat::WlSeat,
        capability: Capability,
    ) {
        if capability == Capability::Keyboard && self.keyboard.is_none() {
            self.keyboard = self.seats.get_keyboard(qh, &seat, None).ok();
        }
    }
    fn remove_capability(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: wl_seat::WlSeat,
        capability: Capability,
    ) {
        if capability == Capability::Keyboard {
            if let Some(keyboard) = self.keyboard.take() {
                keyboard.release();
            }
            self.held = None;
            self.enter_pending = None;
        }
    }
}
impl KeyboardHandler for State {
    fn enter(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &wl_keyboard::WlKeyboard,
        _: &wl_surface::WlSurface,
        _: u32,
        _: &[u32],
        _: &[Keysym],
    ) {
        println!(
            "SHELL_FOCUS_ENTER page={:?} band={} index={}",
            self.model.page, self.model.band, self.model.index
        );
        self.dirty = true;
    }
    fn leave(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &wl_keyboard::WlKeyboard,
        _: &wl_surface::WlSurface,
        _: u32,
    ) {
        self.held = None;
        self.enter_pending = None;
        println!("SHELL_FOCUS_LEAVE");
    }
    fn press_key(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &wl_keyboard::WlKeyboard,
        _: u32,
        event: KeyEvent,
    ) {
        self.press(event);
    }
    fn release_key(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &wl_keyboard::WlKeyboard,
        _: u32,
        event: KeyEvent,
    ) {
        if self
            .held
            .as_ref()
            .is_some_and(|(code, _, _)| *code == event.raw_code)
        {
            self.held = None;
        }
        if event.keysym == Keysym::Return || event.keysym == Keysym::KP_Enter {
            if self.enter_pending.take().is_some() && !self.enter_long {
                self.key(Key::Enter);
            }
            self.enter_long = false;
        }
    }
    fn repeat_key(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &wl_keyboard::WlKeyboard,
        _: u32,
        _: KeyEvent,
    ) {
    }
    fn update_modifiers(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &wl_keyboard::WlKeyboard,
        _: u32,
        modifiers: Modifiers,
        _: RawModifiers,
        _: u32,
    ) {
        self.modifiers = modifiers;
    }
}
impl OutputHandler for State {
    fn output_state(&mut self) -> &mut OutputState {
        &mut self.output
    }
    fn new_output(&mut self, _: &Connection, _: &QueueHandle<Self>, _: wl_output::WlOutput) {}
    fn update_output(&mut self, _: &Connection, _: &QueueHandle<Self>, _: wl_output::WlOutput) {}
    fn output_destroyed(&mut self, _: &Connection, _: &QueueHandle<Self>, _: wl_output::WlOutput) {}
}
impl ShmHandler for State {
    fn shm_state(&mut self) -> &mut Shm {
        &mut self.shm
    }
}
impl ProvidesRegistryState for State {
    fn registry(&mut self) -> &mut RegistryState {
        &mut self.registry
    }
    registry_handlers![OutputState, SeatState];
}
delegate_registry!(State);
smithay_client_toolkit::delegate_dispatch2!(State);
