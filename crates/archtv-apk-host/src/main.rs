//! Minimal APK View frontend. SCTK plumbing follows the project test client.
mod backend;
mod model;
mod render;
use smithay_client_toolkit::{
    compositor::{CompositorHandler, CompositorState, FrameCallbackData},
    delegate_registry,
    output::{OutputHandler, OutputState},
    reexports::{
        calloop::{EventLoop, channel},
        calloop_wayland_source::WaylandSource,
    },
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
    path::PathBuf,
    time::{Duration, Instant},
};
use wayland_client::{
    Connection, QueueHandle,
    globals::registry_queue_init,
    protocol::{wl_keyboard, wl_output, wl_seat, wl_shm, wl_surface},
};
struct Client {
    registry: RegistryState,
    output: OutputState,
    shm: Shm,
    window: Window,
    seats: SeatState,
    keyboard: Option<wl_keyboard::WlKeyboard>,
    pool: SlotPool,
    backend: backend::Backend,
    renderer: render::Renderer,
    tree: Option<model::Node>,
    width: u32,
    height: u32,
    configured: bool,
    dirty: bool,
    frame_pending: bool,
    frames: u64,
    exit: bool,
    failure: Option<String>,
    requests: usize,
    progress: Instant,
    capture: Option<PathBuf>,
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.len() != 6 && args.len() != 7 {
        return Err("Usage: archtv-apk-host ART_ROOT RUNTIME_DEX APK ACTIVITY DATA_DIR STDERR_LOG [CAPTURE_DIR]".into());
    }
    let art = PathBuf::from(&args[0]).canonicalize()?;
    let dex = PathBuf::from(&args[1]).canonicalize()?;
    let apk = PathBuf::from(&args[2]).canonicalize()?;
    let data = std::path::absolute(&args[4])?;
    let log = std::path::absolute(&args[5])?;
    let capture = args.get(6).map(PathBuf::from);
    if let Some(directory) = &capture {
        std::fs::create_dir_all(directory)?;
    }
    let connection = Connection::connect_to_env()?;
    let (globals, queue) = registry_queue_init::<Client>(&connection)?;
    let qh = queue.handle();
    let compositor = CompositorState::bind(&globals, &qh)?;
    let shell = XdgShell::bind(&globals, &qh)?;
    let shm = Shm::bind(&globals, &qh)?;
    let window = shell.create_window(
        compositor.create_surface(&qh),
        WindowDecorations::RequestServer,
        &qh,
    );
    window.set_title("Arch TV · APK");
    window.set_app_id("org.archtv.ApkHost");
    window.commit();
    let renderer = render::Renderer::new(std::fs::read("/usr/share/fonts/TTF/DejaVuSans.ttf")?)?;
    let pool = SlotPool::new(1280 * 720 * 4, &shm)?;
    let (sender, receiver) = channel::sync_channel(8);
    let backend = backend::Backend::start(&art, &dex, &apk, &args[3], &data, &log, sender)?;
    let mut state = Client {
        registry: RegistryState::new(&globals),
        output: OutputState::new(&globals, &qh),
        seats: SeatState::new(&globals, &qh),
        keyboard: None,
        shm,
        window,
        pool,
        backend,
        renderer,
        tree: None,
        width: 1280,
        height: 720,
        configured: false,
        dirty: false,
        frame_pending: false,
        frames: 0,
        exit: false,
        failure: None,
        requests: 0,
        progress: Instant::now(),
        capture,
    };
    let mut event_loop: EventLoop<Client> = EventLoop::try_new()?;
    WaylandSource::new(connection.clone(), queue).insert(event_loop.handle())?;
    event_loop
        .handle()
        .insert_source(receiver, |event, _, state| match event {
            channel::Event::Msg(update) => {
                if let Err(error) = state.update(update) {
                    state.fail(error);
                }
            }
            channel::Event::Closed => {
                if !state.exit {
                    state.fail("ART output closed unexpectedly".into());
                }
            }
        })?;
    while !state.exit {
        event_loop.dispatch(Some(Duration::from_secs(1)), &mut state)?;
        if state.progress.elapsed() > Duration::from_secs(60)
            && (state.tree.is_none() || state.requests > 0)
        {
            state.fail("ART response timed out".into());
        }
        if state.dirty && state.configured && !state.frame_pending {
            state.draw(&qh)?;
        }
        connection.flush()?;
    }
    drop(state.backend);
    println!("APK_HOST_STOPPED frames={}", state.frames);
    if let Some(error) = state.failure {
        return Err(error.into());
    }
    Ok(())
}
impl Client {
    fn fail(&mut self, error: String) {
        eprintln!("APK_HOST_ERROR {error}");
        self.failure = Some(error);
        self.exit = true;
    }
    fn update(&mut self, update: backend::Update) -> Result<(), String> {
        let message = update?;
        match message.event.as_str() {
            "ready" if self.tree.is_none() => {}
            "updated" if self.requests > 0 => {
                self.requests -= 1;
            }
            "closed" => {
                return Err("ART closed without a client close request".into());
            }
            _ => return Err("Unexpected ART event".into()),
        }
        let tree = message.root.ok_or("Missing View root")?;
        tree.validate(0, &mut 4096)?;
        println!("APK_VIEW {} {:?}", message.event, tree);
        self.tree = Some(tree);
        self.dirty = true;
        self.progress = Instant::now();
        Ok(())
    }
    fn draw(&mut self, qh: &QueueHandle<Self>) -> Result<(), Box<dyn std::error::Error>> {
        let Some(tree) = &self.tree else {
            return Ok(());
        };
        let pixmap = self.renderer.render(tree, self.width, self.height)?;
        let (buffer, canvas) = self.pool.create_buffer(
            self.width as i32,
            self.height as i32,
            self.width as i32 * 4,
            wl_shm::Format::Argb8888,
        )?;
        for (pixel, rgba) in canvas
            .chunks_exact_mut(4)
            .zip(pixmap.data().chunks_exact(4))
        {
            pixel.copy_from_slice(
                &u32::from_be_bytes([rgba[3], rgba[0], rgba[1], rgba[2]]).to_ne_bytes(),
            );
        }
        self.window
            .wl_surface()
            .damage_buffer(0, 0, self.width as i32, self.height as i32);
        self.window
            .wl_surface()
            .frame(qh, FrameCallbackData(self.window.wl_surface().clone()));
        buffer.attach_to(self.window.wl_surface())?;
        self.window.commit();
        self.frames += 1;
        self.frame_pending = true;
        self.dirty = false;
        if let Some(directory) = &self.capture {
            pixmap.save_png(directory.join(format!("frame-{:04}.png", self.frames)))?;
        }
        println!("APK_FRAME {} {}x{}", self.frames, self.width, self.height);
        Ok(())
    }
}
impl WindowHandler for Client {
    fn request_close(&mut self, _: &Connection, _: &QueueHandle<Self>, _: &Window) {
        self.exit = true;
    }
    fn configure(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &Window,
        config: WindowConfigure,
        _: u32,
    ) {
        self.width = config.new_size.0.map(|size| size.get()).unwrap_or(1280);
        self.height = config.new_size.1.map(|size| size.get()).unwrap_or(720);
        if self.width > 3840 || self.height > 2160 {
            self.fail("Output exceeds 4K budget".into());
            return;
        }
        self.configured = true;
        self.dirty = true;
    }
}
impl CompositorHandler for Client {
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
impl OutputHandler for Client {
    fn output_state(&mut self) -> &mut OutputState {
        &mut self.output
    }
    fn new_output(&mut self, _: &Connection, _: &QueueHandle<Self>, _: wl_output::WlOutput) {}
    fn update_output(&mut self, _: &Connection, _: &QueueHandle<Self>, _: wl_output::WlOutput) {}
    fn output_destroyed(&mut self, _: &Connection, _: &QueueHandle<Self>, _: wl_output::WlOutput) {}
}
impl ShmHandler for Client {
    fn shm_state(&mut self) -> &mut Shm {
        &mut self.shm
    }
}
impl ProvidesRegistryState for Client {
    fn registry(&mut self) -> &mut RegistryState {
        &mut self.registry
    }
    registry_handlers![OutputState, SeatState];
}
delegate_registry!(Client);
smithay_client_toolkit::delegate_dispatch2!(Client);

impl SeatHandler for Client {
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
        cap: Capability,
    ) {
        if cap == Capability::Keyboard && self.keyboard.is_none() {
            self.keyboard = Some(self.seats.get_keyboard(qh, &seat, None).expect("keyboard"));
        }
    }
    fn remove_capability(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: wl_seat::WlSeat,
        cap: Capability,
    ) {
        if cap == Capability::Keyboard {
            if let Some(keyboard) = self.keyboard.take() {
                keyboard.release();
            }
        }
    }
}
impl KeyboardHandler for Client {
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
        println!("APK_FOCUS_ENTER");
    }
    fn leave(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &wl_keyboard::WlKeyboard,
        _: &wl_surface::WlSurface,
        _: u32,
    ) {
    }
    fn press_key(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &wl_keyboard::WlKeyboard,
        _: u32,
        event: KeyEvent,
    ) {
        println!("APK_KEY {:?}", event.keysym);
        match event.keysym {
            Keysym::Escape => self.exit = true,
            Keysym::Return | Keysym::KP_Enter | Keysym::space if self.tree.is_some() => {
                if self.requests >= 16 {
                    self.fail("Input queue exceeds budget".into());
                    return;
                }
                if let Err(error) = self.backend.activate() {
                    self.fail(error.to_string());
                } else {
                    if self.requests == 0 {
                        self.progress = Instant::now();
                    }
                    self.requests += 1;
                }
            }
            _ => {}
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
    fn release_key(
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
        _: Modifiers,
        _: RawModifiers,
        _: u32,
    ) {
    }
}
