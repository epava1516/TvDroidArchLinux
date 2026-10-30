// Adapted protocol integration from Smallvil; see licenses/Smithay-MIT.txt.
use crate::state::TvCompositor;
use smithay::{
    desktop::{PopupKind, Window, find_popup_root_surface, get_popup_toplevel_coords},
    reexports::wayland_protocols::xdg::shell::server::xdg_toplevel,
    reexports::wayland_server::protocol::{wl_seat, wl_surface::WlSurface},
    utils::Serial,
    wayland::{
        compositor::with_states,
        shell::xdg::{
            PopupSurface, PositionerState, ToplevelSurface, XdgShellHandler, XdgShellState,
            XdgToplevelSurfaceData,
        },
    },
};
impl XdgShellHandler for TvCompositor {
    fn xdg_shell_state(&mut self) -> &mut XdgShellState {
        &mut self.xdg_shell_state
    }
    fn new_toplevel(&mut self, surface: ToplevelSurface) {
        surface.with_pending_state(|pending| {
            pending.size = Some(self.size.into());
            pending.bounds = Some(self.size.into());
            pending.states.set(xdg_toplevel::State::Fullscreen);
        });
        self.pending_activate.push(surface.wl_surface().clone());
        self.space
            .map_element(Window::new_wayland_window(surface), (0, 0), false);
        self.dirty = true;
    }
    fn toplevel_destroyed(&mut self, surface: ToplevelSurface) {
        let window = self
            .space
            .elements()
            .find(|w| w.toplevel().unwrap().wl_surface() == surface.wl_surface())
            .cloned();
        if let Some(window) = window {
            self.space.unmap_elem(&window);
        }
        self.pending_activate
            .retain(|pending| pending != surface.wl_surface());
        let was_active = self.focus.current() == Some(surface.wl_surface());
        let next = self.focus.remove(surface.wl_surface());
        if was_active {
            // Closing the active application returns to Home when it exists.
            let home = self.focus.home();
            if home.is_some() {
                tracing::info!("TV_APP_CLOSED_HOME");
            }
            self.focus_surface(home.or(next));
        }
        self.dirty = true;
        tracing::info!("TOPLEVEL_DESTROYED");
    }
    fn new_popup(&mut self, surface: PopupSurface, positioner: PositionerState) {
        surface.with_pending_state(|state| {
            state.geometry = positioner.get_geometry();
            state.positioner = positioner;
        });
        self.constrain_popup(&surface);
        if let Err(error) = self.popups.track_popup(PopupKind::Xdg(surface)) {
            tracing::warn!(?error, "popup rejected");
        }
        self.dirty = true;
    }
    fn reposition_request(
        &mut self,
        surface: PopupSurface,
        positioner: PositionerState,
        token: u32,
    ) {
        surface.with_pending_state(|state| {
            state.geometry = positioner.get_geometry();
            state.positioner = positioner;
        });
        self.constrain_popup(&surface);
        surface.send_repositioned(token);
        self.dirty = true;
    }
    fn grab(&mut self, surface: PopupSurface, resource: wl_seat::WlSeat, serial: Serial) {
        use smithay::{
            desktop::{PopupKeyboardGrab, PopupPointerGrab, PopupUngrabStrategy},
            input::{Seat, pointer::Focus},
        };
        let Some(seat) = Seat::<Self>::from_resource(&resource) else {
            return;
        };
        let kind = PopupKind::Xdg(surface);
        let Ok(root) = find_popup_root_surface(&kind) else {
            return;
        };
        let Some(keyboard) = seat.get_keyboard() else {
            return;
        };
        // Only the focused application may start a grab from its input serial.
        if keyboard.current_focus().as_ref() != Some(&root) && !keyboard.is_grabbed() {
            return;
        }
        let Ok(mut grab) = self.popups.grab_popup(root, kind, &seat, serial) else {
            return;
        };
        if keyboard.is_grabbed()
            && !(keyboard.has_grab(serial)
                || keyboard.has_grab(grab.previous_serial().unwrap_or(serial)))
        {
            grab.ungrab(PopupUngrabStrategy::All);
            return;
        }
        if let Some(pointer) = seat.get_pointer() {
            if pointer.is_grabbed()
                && !(pointer.has_grab(serial)
                    || pointer.has_grab(grab.previous_serial().unwrap_or(serial)))
            {
                grab.ungrab(PopupUngrabStrategy::All);
                return;
            }
            pointer.set_grab(self, PopupPointerGrab::new(&grab), serial, Focus::Keep);
        }
        keyboard.set_focus(self, grab.current_grab(), serial);
        keyboard.set_grab(self, PopupKeyboardGrab::new(&grab), serial);
        tracing::info!("POPUP_GRABBED");
    }
    fn fullscreen_request(
        &mut self,
        surface: ToplevelSurface,
        _output: Option<smithay::reexports::wayland_server::protocol::wl_output::WlOutput>,
    ) {
        surface.with_pending_state(|pending| {
            pending.size = Some(self.size.into());
            pending.states.set(xdg_toplevel::State::Fullscreen);
        });
        surface.send_pending_configure();
    }
}
pub fn handle_commit(
    popups: &mut smithay::desktop::PopupManager,
    space: &smithay::desktop::Space<Window>,
    surface: &WlSurface,
) {
    if let Some(window) = space
        .elements()
        .find(|w| w.toplevel().unwrap().wl_surface() == surface)
    {
        let initial = with_states(surface, |states| {
            states
                .data_map
                .get::<XdgToplevelSurfaceData>()
                .unwrap()
                .lock()
                .unwrap()
                .initial_configure_sent
        });
        if !initial {
            window.toplevel().unwrap().send_configure();
        }
    }
    popups.commit(surface);
    if let Some(PopupKind::Xdg(popup)) = popups.find_popup(surface) {
        if !popup.is_initial_configure_sent() {
            if let Err(error) = popup.send_configure() {
                tracing::warn!(?error, "popup configure failed");
            }
        }
    }
}

impl TvCompositor {
    fn constrain_popup(&self, popup: &PopupSurface) {
        let kind = PopupKind::Xdg(popup.clone());
        let Ok(root) = find_popup_root_surface(&kind) else {
            return;
        };
        let Some(window) = self.space.elements().find(|window| {
            window
                .toplevel()
                .is_some_and(|top| top.wl_surface() == &root)
        }) else {
            return;
        };
        let Some(geometry) = self.space.element_geometry(window) else {
            return;
        };
        let mut target = smithay::utils::Rectangle::from_size(self.size.into());
        target.loc -= geometry.loc;
        target.loc -= get_popup_toplevel_coords(&kind);
        popup.with_pending_state(|pending| {
            pending.geometry = pending.positioner.get_unconstrained_geometry(target);
        });
    }
}
