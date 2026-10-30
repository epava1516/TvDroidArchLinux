// Adapted from Smallvil; see licenses/Smithay-MIT.txt.
use std::{ffi::OsString, sync::Arc};

use smithay::{
    desktop::{PopupManager, Space, Window, WindowSurfaceType},
    input::{Seat, SeatState},
    reexports::{
        calloop::{EventLoop, Interest, LoopSignal, Mode, PostAction, generic::Generic},
        wayland_server::{
            Display, DisplayHandle,
            backend::{ClientData, ClientId, DisconnectReason},
            protocol::wl_surface::WlSurface,
        },
    },
    utils::{Logical, Point},
    wayland::{
        compositor::{CompositorClientState, CompositorState},
        output::OutputManagerState,
        selection::data_device::DataDeviceState,
        shell::xdg::XdgShellState,
        shm::ShmState,
        socket::ListeningSocketSource,
    },
};

pub struct TvCompositor {
    pub pressed_by_device: std::collections::HashMap<
        String,
        std::collections::HashSet<smithay::input::keyboard::Keycode>,
    >,
    pub loop_handle: smithay::reexports::calloop::LoopHandle<'static, Self>,
    pub shutdown_backend: Option<Box<dyn FnOnce()>>,
    pub session: Option<smithay::backend::session::libseat::LibSeatSession>,
    pub start_time: std::time::Instant,
    pub socket_name: OsString,
    pub display_handle: DisplayHandle,

    pub space: Space<Window>,
    pub loop_signal: LoopSignal,

    // Smithay State
    pub compositor_state: CompositorState,
    pub xdg_shell_state: XdgShellState,
    pub shm_state: ShmState,
    pub _output_manager_state: OutputManagerState,
    pub seat_state: SeatState<TvCompositor>,
    pub data_device_state: DataDeviceState,
    pub popups: PopupManager,

    pub seat: Seat<Self>,
    pub dirty: bool,
    pub pending_activate: Vec<WlSurface>,
    pub size: (i32, i32),
    pub focus: archtv_core::FocusStack<WlSurface>,
}

impl TvCompositor {
    pub fn new(
        event_loop: &mut EventLoop<'static, Self>,
        display: Display<Self>,
    ) -> Result<Self, Box<dyn std::error::Error>> {
        let start_time = std::time::Instant::now();

        let dh = display.handle();

        // Here we initialize implementations of some wayland protocols
        // Some of them require us to implement traits on the TvCompositor state,
        // you can find those implementations in the `crate::handlers` module

        // Initialize protocols needed for displaying windows
        let compositor_state = CompositorState::new::<Self>(&dh);
        let xdg_shell_state = XdgShellState::new::<Self>(&dh);
        let shm_state = ShmState::new::<Self>(&dh, vec![]);
        let popups = PopupManager::default();

        let output_manager_state = OutputManagerState::new_with_xdg_output::<Self>(&dh);

        // Data device is responsible for clipboard and drag-and-drop
        let data_device_state = DataDeviceState::new::<Self>(&dh);

        // A seat is a group of keyboards, pointer and touch devices.
        // A seat typically has a pointer and maintains a keyboard focus and a pointer focus.
        let mut seat_state = SeatState::new();
        let mut seat: Seat<Self> = seat_state.new_wl_seat(&dh, "winit");

        // Notify clients that we have a keyboard, for the sake of the example we assume that keyboard is always present.
        // You may want to track keyboard hot-plug in real compositor.
        seat.add_keyboard(
            smithay::input::keyboard::XkbConfig {
                layout: "es",
                ..Default::default()
            },
            250,
            25,
        )?;

        // Notify clients that we have a pointer (mouse)
        // Here we assume that there is always pointer plugged in
        seat.add_pointer();

        // A space represents a two-dimensional plane. Windows and Outputs can be mapped onto it.
        //
        // Windows get a position and stacking order through mapping.
        // Outputs become views of a part of the Space and can be rendered via Space::render_output.
        let space = Space::default();

        // Setup a wayland socket that will be used to accept clients
        let socket_name = Self::init_wayland_listener(display, event_loop);

        // Get the loop signal, used to stop the event loop
        let loop_signal = event_loop.get_signal();

        Ok(Self {
            pressed_by_device: Default::default(),
            loop_handle: event_loop.handle(),
            session: None,
            shutdown_backend: None,
            start_time,
            display_handle: dh,

            space,
            loop_signal,
            socket_name,

            compositor_state,
            xdg_shell_state,
            shm_state,
            _output_manager_state: output_manager_state,
            seat_state,
            data_device_state,
            popups,
            seat,
            dirty: true,
            pending_activate: Vec::new(),
            size: (1280, 720),
            focus: Default::default(),
        })
    }

    fn init_wayland_listener(
        display: Display<TvCompositor>,
        event_loop: &mut EventLoop<'static, Self>,
    ) -> OsString {
        // Creates a new listening socket, automatically choosing the next available `wayland` socket name.
        let listening_socket = ListeningSocketSource::new_auto().unwrap();

        // Get the name of the listening socket.
        // Clients will connect to this socket.
        let socket_name = listening_socket.socket_name().to_os_string();

        let loop_handle = event_loop.handle();

        loop_handle
            .insert_source(listening_socket, move |client_stream, _, state| {
                // Inside the callback, you should insert the client into the display.
                //
                // You may also associate some data with the client when inserting the client.
                state
                    .display_handle
                    .insert_client(client_stream, Arc::new(ClientState::default()))
                    .unwrap();
            })
            .expect("Failed to init the wayland event source.");

        // You also need to add the display itself to the event loop, so that client events will be processed by wayland-server.
        loop_handle
            .insert_source(
                Generic::new(display, Interest::READ, Mode::Level),
                |_, display, state| {
                    // Safety: we don't drop the display
                    unsafe {
                        display.get_mut().dispatch_clients(state).unwrap();
                    }
                    Ok(PostAction::Continue)
                },
            )
            .unwrap();

        socket_name
    }

    pub fn surface_under(
        &self,
        pos: Point<f64, Logical>,
    ) -> Option<(WlSurface, Point<f64, Logical>)> {
        self.space
            .element_under(pos)
            .and_then(|(window, location)| {
                window
                    .surface_under(pos - location.to_f64(), WindowSurfaceType::ALL)
                    .map(|(s, p)| (s, (p + location).to_f64()))
            })
    }
}

/// Data associated with a wayland client that connects to TvCompositor.
/// One instance of this type per client.
#[derive(Default)]
pub struct ClientState {
    pub is_shell: bool,
    pub compositor_state: CompositorClientState,
}

impl ClientData for ClientState {
    fn initialized(&self, _client_id: ClientId) {}
    fn disconnected(&self, _client_id: ClientId, _reason: DisconnectReason) {}
}

impl TvCompositor {
    pub fn resize(&mut self, width: i32, height: i32) {
        if width <= 0 || height <= 0 {
            return;
        }
        self.size = (width, height);
        for window in self.space.elements() {
            if let Some(top) = window.toplevel() {
                top.with_pending_state(|pending| {
                    pending.size = Some(self.size.into());
                    pending.bounds = Some(self.size.into());
                });
                top.send_pending_configure();
            }
        }
        self.dirty = true;
        tracing::info!(width, height, "OUTPUT_CONFIGURED");
    }
    pub fn activate_committed(&mut self, surface: &WlSurface) {
        if !self.pending_activate.contains(surface) {
            return;
        }
        let ready = self.space.elements().any(|window| {
            window.toplevel().unwrap().wl_surface() == surface && window.geometry().size.w > 0
        });
        if ready {
            self.pending_activate.retain(|pending| pending != surface);
            use smithay::reexports::wayland_server::Resource;
            let is_shell = surface
                .client()
                .and_then(|client| client.get_data::<ClientState>().map(|data| data.is_shell))
                .unwrap_or(false);
            if is_shell {
                self.focus.set_home(surface.clone());
                tracing::info!("SHELL_SURFACE_READY");
            } else {
                self.focus.activate(surface.clone());
            }
            self.focus_surface(Some(surface.clone()));
            tracing::info!("TOPLEVEL_MAPPED");
        }
    }
    pub fn focus_surface(&mut self, surface: Option<WlSurface>) {
        if self
            .seat
            .get_keyboard()
            .is_some_and(|keyboard| keyboard.current_focus() != surface)
        {
            self.dismiss_active_popups();
        }
        let window = surface.as_ref().and_then(|surface| {
            self.space
                .elements()
                .find(|w| w.toplevel().unwrap().wl_surface() == surface)
                .cloned()
        });
        if let Some(window) = window {
            self.space.raise_element(&window, true);
        }
        self.seat.get_keyboard().unwrap().set_focus(
            self,
            surface,
            smithay::utils::SERIAL_COUNTER.next_serial(),
        );
        for window in self.space.elements() {
            window.toplevel().unwrap().send_pending_configure();
        }
        self.dirty = true;
    }
}

impl TvCompositor {
    pub fn show_home(&mut self) {
        if let Some(surface) = self.focus.home() {
            self.dismiss_active_popups();
            self.focus_surface(Some(surface));
            tracing::info!("TV_HOME");
        } else {
            tracing::warn!("TV_HOME_UNAVAILABLE");
        }
    }
    pub fn resume_application(&mut self) {
        let next = self.focus.previous();
        self.dismiss_active_popups();
        self.focus_surface(next);
        tracing::info!("TV_RESUME");
    }
    fn dismiss_active_popups(&mut self) {
        if let Some(keyboard) = self.seat.get_keyboard() {
            keyboard.unset_grab(self);
        }
        if let Some(pointer) = self.seat.get_pointer() {
            pointer.unset_grab(
                self,
                smithay::utils::SERIAL_COUNTER.next_serial(),
                smithay::backend::input::InputTime::now(),
            );
        }
        let roots: Vec<_> = self
            .space
            .elements()
            .filter_map(|window| window.toplevel().map(|top| top.wl_surface().clone()))
            .collect();
        for root in roots {
            let popups: Vec<_> = PopupManager::popups_for_surface(&root)
                .map(|(popup, _)| popup)
                .collect();
            for popup in popups {
                let _ = PopupManager::dismiss_popup(&root, &popup);
            }
        }
    }
}

impl TvCompositor {
    pub fn release_keys(
        &mut self,
        keys: impl IntoIterator<Item = smithay::input::keyboard::Keycode>,
    ) {
        if let Some(keyboard) = self.seat.get_keyboard() {
            for key in keys {
                keyboard.input::<(), _>(
                    self,
                    key,
                    smithay::backend::input::KeyState::Released,
                    smithay::utils::SERIAL_COUNTER.next_serial(),
                    smithay::backend::input::InputTime::now(),
                    |_, _, _| smithay::input::keyboard::FilterResult::Forward,
                );
            }
        }
    }
    pub fn release_all_keys(&mut self) {
        self.pressed_by_device.clear();
        if let Some(keyboard) = self.seat.get_keyboard() {
            self.release_keys(keyboard.pressed_keys());
        }
    }
}
