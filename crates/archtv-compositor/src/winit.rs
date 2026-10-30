// Rendering integration informed by Smallvil; see licenses/Smithay-MIT.txt.
use crate::state::TvCompositor;
use smithay::{
    backend::{
        renderer::{
            damage::OutputDamageTracker, element::surface::WaylandSurfaceRenderElement,
            gles::GlesRenderer,
        },
        winit::{self, WinitEvent},
    },
    output::{Mode, Output, PhysicalProperties, Subpixel},
    reexports::calloop::{
        EventLoop,
        timer::{TimeoutAction, Timer},
    },
    utils::{Rectangle, Transform},
};
use std::{cell::RefCell, rc::Rc, time::Duration};

pub fn init(
    event_loop: &mut EventLoop<TvCompositor>,
    state: &mut TvCompositor,
    test_resize: Option<(u64, u32, u32)>,
    requested_mode: Option<(u32, u32)>,
) -> Result<(), Box<dyn std::error::Error>> {
    use smithay::reexports::winit::{dpi::PhysicalSize, window::WindowAttributes};
    let size = requested_mode.unwrap_or((960, 540));
    let attributes = WindowAttributes::default()
        .with_surface_size(PhysicalSize::new(size.0, size.1))
        .with_title("Arch TV compositor")
        .with_visible(true);
    let (backend, winit) = winit::init_from_attributes::<GlesRenderer>(attributes)?;
    let mode = Mode {
        size: backend.window_size(),
        refresh: 60_000,
    };
    let output = Output::new(
        "ArchTV".into(),
        PhysicalProperties {
            size: (0, 0).into(),
            subpixel: Subpixel::Unknown,
            make: "ArchTV".into(),
            model: "Nested".into(),
            serial_number: "1".into(),
        },
    );
    output.create_global::<TvCompositor>(&state.display_handle);
    output.change_current_state(
        Some(mode),
        Some(Transform::Flipped180),
        None,
        Some((0, 0).into()),
    );
    output.set_preferred(mode);
    state.resize(mode.size.w, mode.size.h);
    state.space.map_output(&output, (0, 0));
    let mut damage_tracker = OutputDamageTracker::from_output(&output);
    let backend = Rc::new(RefCell::new(backend));
    let scheduler = backend.clone();
    if let Some((seconds, width, height)) = test_resize {
        let controller = backend.clone();
        let resized_output = output.clone();
        event_loop.handle().insert_source(
            Timer::from_duration(Duration::from_secs(seconds)),
            move |_, _, state| {
                let applied = controller
                    .borrow()
                    .window()
                    .request_surface_size(PhysicalSize::new(width, height).into());
                // Winit may apply the size synchronously without a Resized event.
                if let Some(size) = applied {
                    let size = (size.width as i32, size.height as i32).into();
                    resized_output.change_current_state(
                        Some(Mode {
                            size,
                            refresh: 60_000,
                        }),
                        None,
                        None,
                        None,
                    );
                    state.resize(size.w, size.h);
                }
                TimeoutAction::Drop
            },
        )?;
    }
    event_loop
        .handle()
        .insert_source(Timer::immediate(), move |_, _, state| {
            if state.dirty {
                scheduler.borrow().window().request_redraw();
            }
            TimeoutAction::ToDuration(Duration::from_millis(16))
        })?;
    event_loop
        .handle()
        .insert_source(winit, move |event, _, state| match event {
            WinitEvent::Resized { size, .. } => {
                output.change_current_state(
                    Some(Mode {
                        size,
                        refresh: 60_000,
                    }),
                    None,
                    None,
                    None,
                );
                state.resize(size.w, size.h);
            }
            WinitEvent::Input(event) => state.process_input_event(event),
            WinitEvent::CloseRequested => state.loop_signal.stop(),
            WinitEvent::Redraw => {
                let mut backend = backend.borrow_mut();
                let damage = Rectangle::from_size(backend.window_size());
                let rendered = {
                    match backend.bind() {
                        Ok((renderer, mut framebuffer)) => {
                            smithay::desktop::space::render_output::<
                                _,
                                WaylandSurfaceRenderElement<GlesRenderer>,
                                _,
                                _,
                            >(
                                &output,
                                renderer,
                                &mut framebuffer,
                                1.0,
                                0,
                                [&state.space],
                                &[],
                                &mut damage_tracker,
                                [0.04, 0.05, 0.08, 1.0],
                            )
                            .map(|_| ())
                            .map_err(|error| format!("render failed: {error:?}"))
                        }
                        Err(error) => Err(format!("bind failed: {error:?}")),
                    }
                };
                if let Err(error) = rendered {
                    tracing::error!(%error);
                    state.loop_signal.stop();
                    return;
                }
                if let Err(error) = backend.submit(Some(&[damage])) {
                    tracing::error!(?error, "submit failed");
                    state.loop_signal.stop();
                    return;
                }
                state.dirty = false;
                for window in state.space.elements() {
                    if window
                        .toplevel()
                        .is_some_and(|top| Some(top.wl_surface()) == state.focus.current())
                    {
                        window.send_frame(
                            &output,
                            state.start_time.elapsed(),
                            Some(Duration::ZERO),
                            |_, _| Some(output.clone()),
                        );
                    }
                }
                state.space.refresh();
                state.popups.cleanup();
                if let Err(error) = state.display_handle.flush_clients() {
                    tracing::warn!(?error, "client flush failed");
                }
            }
            _ => (),
        })?;
    Ok(())
}
