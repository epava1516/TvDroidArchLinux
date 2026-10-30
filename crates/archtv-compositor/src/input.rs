// Adapted from Smallvil; see licenses/Smithay-MIT.txt.
use smithay::{
    backend::input::{
        AbsolutePositionEvent, Axis, AxisSource, ButtonState, Device, Event, InputBackend,
        InputEvent, KeyState, KeyboardKeyEvent, PointerAxisEvent, PointerButtonEvent,
        PointerMotionEvent,
    },
    input::{
        keyboard::FilterResult,
        pointer::{AxisFrame, ButtonEvent, MotionEvent},
    },
    utils::SERIAL_COUNTER,
};

use crate::state::TvCompositor;
enum Shortcut {
    Vt(i32),
    Home,
    Resume,
    Exit,
}

impl TvCompositor {
    pub fn process_input_event<I: InputBackend>(&mut self, event: InputEvent<I>) {
        match event {
            InputEvent::Keyboard { event, .. } => {
                let id = event.device().id();
                let key = event.key_code();
                match event.state() {
                    KeyState::Pressed => {
                        self.pressed_by_device
                            .entry(id.clone())
                            .or_default()
                            .insert(key);
                    }
                    KeyState::Released => {
                        if let Some(keys) = self.pressed_by_device.get_mut(&id) {
                            keys.remove(&key);
                        }
                    }
                }
                if self
                    .pressed_by_device
                    .iter()
                    .any(|(other, keys)| other != &id && keys.contains(&key))
                {
                    return;
                }
                let serial = SERIAL_COUNTER.next_serial();
                let time = Event::time(&event);

                let shortcut = self.seat.get_keyboard().unwrap().input::<Shortcut, _>(
                    self,
                    event.key_code(),
                    event.state(),
                    serial,
                    time,
                    |state, modifiers, key| {
                        use smithay::input::keyboard::Keysym;
                        let modified = key.modified_sym();
                        if modified == Keysym::Home || modified == Keysym::XF86_HomePage {
                            return FilterResult::Intercept(Shortcut::Home);
                        }
                        if modifiers.alt && modified == Keysym::Tab {
                            return FilterResult::Intercept(Shortcut::Resume);
                        }
                        if modifiers.ctrl && modifiers.alt && modified == Keysym::BackSpace {
                            return FilterResult::Intercept(Shortcut::Exit);
                        }
                        if state.session.is_some() && modifiers.ctrl && modifiers.alt {
                            let sym = key
                                .raw_syms()
                                .first()
                                .copied()
                                .unwrap_or_else(|| key.modified_sym())
                                .raw();
                            if (Keysym::F1.raw()..=Keysym::F12.raw()).contains(&sym) {
                                return FilterResult::Intercept(Shortcut::Vt(
                                    (sym - Keysym::F1.raw() + 1) as i32,
                                ));
                            }
                        }
                        FilterResult::Forward
                    },
                );
                if let Some(shortcut) = shortcut.filter(|_| event.state() == KeyState::Pressed) {
                    match shortcut {
                        Shortcut::Home => self.show_home(),
                        Shortcut::Resume => self.resume_application(),
                        Shortcut::Exit => self.loop_signal.stop(),
                        Shortcut::Vt(vt) => {
                            use smithay::backend::session::Session;
                            if let Some(session) = self.session.as_mut() {
                                if let Err(error) = session.change_vt(vt) {
                                    tracing::warn!(?error, vt, "VT_SWITCH_FAILED");
                                }
                            }
                        }
                    }
                }
            }
            InputEvent::DeviceAdded { device } => {
                tracing::info!(name = device.name(), "INPUT_ADDED")
            }
            InputEvent::DeviceRemoved { device } => {
                tracing::info!(name = device.name(), "INPUT_REMOVED");
                if let Some(keys) = self.pressed_by_device.remove(&device.id()) {
                    let orphaned: Vec<_> = keys
                        .into_iter()
                        .filter(|key| {
                            !self
                                .pressed_by_device
                                .values()
                                .any(|held| held.contains(key))
                        })
                        .collect();
                    self.release_keys(orphaned);
                }
            }
            InputEvent::PointerMotion { event } => {
                let pointer = self.seat.get_pointer().unwrap();
                let mut pos = pointer.current_location() + event.delta();
                pos.x = pos.x.clamp(0.0, f64::from(self.size.0 - 1));
                pos.y = pos.y.clamp(0.0, f64::from(self.size.1 - 1));
                let under = self.surface_under(pos);
                pointer.motion(
                    self,
                    under,
                    &MotionEvent {
                        location: pos,
                        serial: SERIAL_COUNTER.next_serial(),
                        time: event.time(),
                    },
                );
                pointer.frame(self);
            }
            InputEvent::PointerMotionAbsolute { event, .. } => {
                let output = self.space.outputs().next().unwrap();

                let output_geo = self.space.output_geometry(output).unwrap();

                let pos = event.position_transformed(output_geo.size) + output_geo.loc.to_f64();

                let serial = SERIAL_COUNTER.next_serial();

                let pointer = self.seat.get_pointer().unwrap();

                let under = self.surface_under(pos);

                pointer.motion(
                    self,
                    under,
                    &MotionEvent {
                        location: pos,
                        serial,
                        time: event.time(),
                    },
                );
                pointer.frame(self);
            }
            InputEvent::PointerButton { event, .. } => {
                let pointer = self.seat.get_pointer().unwrap();

                let serial = SERIAL_COUNTER.next_serial();

                let button = event.button_code();

                let button_state = event.state();

                if ButtonState::Pressed == button_state && !pointer.is_grabbed() {
                    if let Some((window, _loc)) = self
                        .space
                        .element_under(pointer.current_location())
                        .map(|(w, l)| (w.clone(), l))
                    {
                        let surface = window.toplevel().unwrap().wl_surface().clone();
                        self.focus.activate(surface.clone());
                        self.focus_surface(Some(surface));
                    }
                };

                pointer.button(
                    self,
                    &ButtonEvent {
                        button,
                        state: button_state,
                        serial,
                        time: event.time(),
                    },
                );
                pointer.frame(self);
            }
            InputEvent::PointerAxis { event, .. } => {
                let source = event.source();

                let horizontal_amount = event.amount(Axis::Horizontal).unwrap_or_else(|| {
                    event.amount_v120(Axis::Horizontal).unwrap_or(0.0) * 15.0 / 120.
                });
                let vertical_amount = event.amount(Axis::Vertical).unwrap_or_else(|| {
                    event.amount_v120(Axis::Vertical).unwrap_or(0.0) * 15.0 / 120.
                });
                let horizontal_amount_discrete = event.amount_v120(Axis::Horizontal);
                let vertical_amount_discrete = event.amount_v120(Axis::Vertical);

                let mut frame = AxisFrame::new(event.time()).source(source);
                if horizontal_amount != 0.0 {
                    frame = frame.value(Axis::Horizontal, horizontal_amount);
                    if let Some(discrete) = horizontal_amount_discrete {
                        frame = frame.v120(Axis::Horizontal, discrete as i32);
                    }
                }
                if vertical_amount != 0.0 {
                    frame = frame.value(Axis::Vertical, vertical_amount);
                    if let Some(discrete) = vertical_amount_discrete {
                        frame = frame.v120(Axis::Vertical, discrete as i32);
                    }
                }

                if source == AxisSource::Finger {
                    if event.amount(Axis::Horizontal) == Some(0.0) {
                        frame = frame.stop(Axis::Horizontal);
                    }
                    if event.amount(Axis::Vertical) == Some(0.0) {
                        frame = frame.stop(Axis::Vertical);
                    }
                }

                let pointer = self.seat.get_pointer().unwrap();
                pointer.axis(self, frame);
                pointer.frame(self);
            }
            _ => {}
        }
    }
}
