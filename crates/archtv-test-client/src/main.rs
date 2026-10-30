//! A native Wayland SHM client used to verify configure, frames, focus and clean disconnect.
//! SCTK integration follows its MIT simple_window example; see licenses/SCTK-MIT.txt.
use smithay_client_toolkit::{
    compositor::{CompositorHandler, CompositorState, FrameCallbackData},
    delegate_registry,
    output::{OutputHandler, OutputState},
    registry::{ProvidesRegistryState, RegistryState},
    registry_handlers,
    seat::{
        Capability, SeatHandler, SeatState,
        keyboard::{KeyEvent, KeyboardHandler, Keysym, Modifiers, RawModifiers},
    },
    shell::{
        WaylandSurface,
        xdg::{
            XdgPositioner, XdgShell, XdgSurface,
            popup::{ConfigureKind, Popup, PopupConfigure, PopupHandler},
            window::{Window, WindowConfigure, WindowDecorations, WindowHandler},
        },
    },
    shm::{Shm, ShmHandler, slot::SlotPool},
};
use wayland_client::{
    Connection, QueueHandle,
    globals::registry_queue_init,
    protocol::{wl_keyboard, wl_output, wl_seat, wl_shm, wl_surface},
};
struct Client {
    control: Option<std::os::unix::net::UnixStream>,
    control_on_enter: bool,
    compositor: CompositorState,
    shell: XdgShell,
    popup_test: bool,
    popup_grab: bool,
    focused_popup: bool,
    keyboard_seat: Option<wl_seat::WlSeat>,
    popup: Option<Popup>,
    positioner: XdgPositioner,
    popup_frames: u32,
    registry: RegistryState,
    output: OutputState,
    shm: Shm,
    window: Window,
    seats: SeatState,
    keyboard: Option<wl_keyboard::WlKeyboard>,
    pool: SlotPool,
    width: u32,
    height: u32,
    drawn: u32,
    limit: u32,
    exit: bool,
}
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let limit = std::env::args()
        .nth(1)
        .map(|arg| arg.parse::<u32>())
        .transpose()?
        .unwrap_or(3);
    use std::os::fd::{AsRawFd, FromRawFd};
    let control = std::env::var("ARCHTV_CONTROL_FD")
        .ok()
        .map(|value| -> Result<_, Box<dyn std::error::Error>> {
            let fd = value.parse::<i32>()?;
            if fd < 3 {
                return Err("invalid control descriptor".into());
            }
            // The supervisor transfers ownership of this private descriptor.
            let stream = unsafe { std::os::unix::net::UnixStream::from_raw_fd(fd) };
            unsafe {
                let flags = libc::fcntl(stream.as_raw_fd(), libc::F_GETFD);
                if flags < 0
                    || libc::fcntl(stream.as_raw_fd(), libc::F_SETFD, flags | libc::FD_CLOEXEC) < 0
                {
                    return Err(std::io::Error::last_os_error().into());
                }
            }
            Ok(stream)
        })
        .transpose()?;
    let conn = Connection::connect_to_env()?;
    let (globals, mut queue) = registry_queue_init::<Client>(&conn)?;
    let qh = queue.handle();
    let compositor = CompositorState::bind(&globals, &qh)?;
    let shell = XdgShell::bind(&globals, &qh)?;
    let shm = Shm::bind(&globals, &qh)?;
    let window = shell.create_window(
        compositor.create_surface(&qh),
        WindowDecorations::RequestServer,
        &qh,
    );
    window.set_title("Arch TV · cliente de prueba Rust");
    window.set_app_id("org.archtv.TestClient");
    window.commit();
    let pool = SlotPool::new(1024 * 1024, &shm)?;
    let positioner = XdgPositioner::new(&shell)?;
    use smithay_client_toolkit::reexports::protocols::xdg::shell::client::xdg_positioner::ConstraintAdjustment;
    positioner
        .set_constraint_adjustment(ConstraintAdjustment::SlideX | ConstraintAdjustment::SlideY);
    positioner.set_size(160, 90);
    positioner.set_anchor_rect(40, 40, 1, 1);
    let mut state = Client {
        control,
        control_on_enter: std::env::args().any(|arg| arg == "--control-on-enter"),
        compositor,
        shell,
        positioner,
        popup_test: std::env::args().any(|arg| arg == "--popup" || arg == "--popup-grab"),
        popup_grab: std::env::args().any(|arg| arg == "--popup-grab"),
        focused_popup: false,
        keyboard_seat: None,
        popup: None,
        popup_frames: 0,
        seats: SeatState::new(&globals, &qh),
        keyboard: None,
        registry: RegistryState::new(&globals),
        output: OutputState::new(&globals, &qh),
        shm,
        window,
        pool,
        width: 640,
        height: 360,
        drawn: 0,
        limit,
        exit: false,
    };
    while !state.exit {
        queue.blocking_dispatch(&mut state)?;
    }
    println!("CLIENT_EXIT frames={}", state.drawn);
    Ok(())
}
impl Client {
    fn draw(&mut self, qh: &QueueHandle<Self>) {
        let w = self.width;
        let h = self.height;
        let (buffer, canvas) = self
            .pool
            .create_buffer(w as i32, h as i32, w as i32 * 4, wl_shm::Format::Argb8888)
            .expect("SHM buffer");
        for (i, pixel) in canvas.chunks_exact_mut(4).enumerate() {
            let x = i as u32 % w;
            let y = i as u32 / w;
            let color = if x > w / 4 && x < w * 3 / 4 && y > h / 4 && y < h * 3 / 4 {
                0xff4bc2b0u32
            } else {
                0xff101a2au32
            };
            pixel.copy_from_slice(&color.to_ne_bytes());
        }
        self.window
            .wl_surface()
            .damage_buffer(0, 0, w as i32, h as i32);
        self.window
            .wl_surface()
            .frame(qh, FrameCallbackData(self.window.wl_surface().clone()));
        buffer.attach_to(self.window.wl_surface()).expect("attach");
        self.window.commit();
        self.drawn += 1;
        println!("CLIENT_FRAME {} size={}x{}", self.drawn, w, h);
    }
}
impl WindowHandler for Client {
    fn request_close(&mut self, _: &Connection, _: &QueueHandle<Self>, _: &Window) {
        self.exit = true;
    }
    fn configure(
        &mut self,
        _: &Connection,
        qh: &QueueHandle<Self>,
        _: &Window,
        c: WindowConfigure,
        _: u32,
    ) {
        self.width = c.new_size.0.map(|v| v.get()).unwrap_or(640);
        self.height = c.new_size.1.map(|v| v.get()).unwrap_or(360);
        println!(
            "CLIENT_CONFIGURE {}x{} fullscreen={}",
            self.width,
            self.height,
            c.is_fullscreen()
        );
        if self.drawn == 0 || self.limit == 0 {
            self.draw(qh);
        }
    }
}
impl CompositorHandler for Client {
    fn frame(
        &mut self,
        _: &Connection,
        qh: &QueueHandle<Self>,
        surface: &wl_surface::WlSurface,
        _: u32,
    ) {
        if self.popup_test {
            if surface == self.window.wl_surface() && self.popup.is_none() && !self.popup_grab {
                self.popup = Some(
                    Popup::new(
                        self.window.xdg_surface(),
                        &self.positioner,
                        qh,
                        &self.compositor,
                        &self.shell,
                    )
                    .expect("popup"),
                );
            } else if self
                .popup
                .as_ref()
                .is_some_and(|popup| popup.wl_surface() == surface)
            {
                self.popup_frames += 1;
                println!("POPUP_FRAME {}", self.popup_frames);
                if self.popup_grab {
                    return;
                }
                if self.popup_frames == 1 {
                    self.positioner.set_offset(80, 50);
                    self.popup.as_ref().unwrap().reposition(&self.positioner, 7);
                } else {
                    self.popup.take();
                    println!("POPUP_CLOSED");
                    self.exit = true;
                }
            }
            return;
        }
        if self.limit > 0 && self.drawn >= self.limit {
            self.exit = true;
        } else if self.limit > 0 {
            self.draw(qh);
        }
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
            self.keyboard_seat = Some(seat);
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
        surface: &wl_surface::WlSurface,
        _: u32,
        _: &[u32],
        _: &[Keysym],
    ) {
        self.focused_popup = self
            .popup
            .as_ref()
            .is_some_and(|popup| popup.wl_surface() == surface);
        println!("CLIENT_FOCUS_ENTER popup={}", self.focused_popup);
    }
    fn leave(
        &mut self,
        _: &Connection,
        _: &QueueHandle<Self>,
        _: &wl_keyboard::WlKeyboard,
        _: &wl_surface::WlSurface,
        _: u32,
    ) {
        println!("CLIENT_FOCUS_LEAVE");
    }
    fn press_key(
        &mut self,
        _: &Connection,
        qh: &QueueHandle<Self>,
        _: &wl_keyboard::WlKeyboard,
        serial: u32,
        event: KeyEvent,
    ) {
        if event.keysym == Keysym::Escape && std::env::args().any(|arg| arg == "--close-on-escape")
        {
            self.exit = true;
        }
        println!(
            "CLIENT_KEY {:?} popup={} text={:?}",
            event.keysym, self.focused_popup, event.utf8
        );
        if self.control_on_enter && event.keysym == Keysym::Return {
            use std::io::Write;
            if let Some(control) = self.control.as_mut() {
                control.write_all(b"RESUME\n").expect("shell control");
                println!("CLIENT_CONTROL_RESUME");
            } else {
                println!("CLIENT_CONTROL_UNAVAILABLE");
            }
        }
        if self.popup_grab && event.keysym == Keysym::Return && self.popup.is_none() {
            let popup = Popup::new(
                self.window.xdg_surface(),
                &self.positioner,
                qh,
                &self.compositor,
                &self.shell,
            )
            .expect("popup");
            popup
                .xdg_popup()
                .grab(self.keyboard_seat.as_ref().expect("seat"), serial);
            self.popup = Some(popup);
        } else if self.popup_grab && event.keysym == Keysym::ntilde {
            assert!(self.focused_popup, "popup must own keyboard focus");
            self.popup.take();
            println!("POPUP_CLOSED_BY_KEY");
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

impl PopupHandler for Client {
    fn configure(
        &mut self,
        _: &Connection,
        qh: &QueueHandle<Self>,
        popup: &Popup,
        config: PopupConfigure,
    ) {
        println!(
            "POPUP_CONFIGURE {}x{} position={:?} kind={:?}",
            config.width, config.height, config.position, config.kind
        );
        if let ConfigureKind::Reposition { token } = config.kind {
            assert_eq!(token, 7);
            println!("POPUP_REPOSITIONED token={token}");
        }
        let (buffer, canvas) = self
            .pool
            .create_buffer(
                config.width,
                config.height,
                config.width * 4,
                wl_shm::Format::Argb8888,
            )
            .expect("popup buffer");
        for pixel in canvas.chunks_exact_mut(4) {
            pixel.copy_from_slice(&0xffffa020u32.to_ne_bytes());
        }
        popup
            .wl_surface()
            .damage_buffer(0, 0, config.width, config.height);
        popup
            .wl_surface()
            .frame(qh, FrameCallbackData(popup.wl_surface().clone()));
        buffer.attach_to(popup.wl_surface()).expect("popup attach");
        popup.commit();
    }
    fn done(&mut self, _: &Connection, _: &QueueHandle<Self>, _: &Popup) {
        self.popup.take();
        println!("POPUP_DISMISSED");
    }
}
