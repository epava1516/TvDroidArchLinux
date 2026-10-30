// Protocol integration builds upon Smithay's Smallvil example (MIT).
// See licenses/Smithay-MIT.txt for the upstream copyright notice.
mod drm;
mod handlers;
mod input;
mod session;
mod state;
mod winit;

use calloop::{
    signals::{Signal, Signals},
    timer::{TimeoutAction, Timer},
};
use smithay::reexports::{calloop::EventLoop, wayland_server::Display};
use state::TvCompositor;
use std::time::Duration;

fn main() -> Result<(), Box<dyn std::error::Error>> {
    tracing_subscriber::fmt()
        .with_env_filter(
            tracing_subscriber::EnvFilter::try_from_default_env()
                .unwrap_or_else(|_| "archtv_compositor=info,smithay=warn".into()),
        )
        .with_ansi(false)
        .init();
    let mut command = Vec::new();
    let mut shell = false;
    let mut lifetime = None;
    let mut test_resize = None;
    let mut drm_device = None;
    let mut requested_mode = None;
    let mut capture = None;
    let mut capture_request = None;
    let mut args = std::env::args().skip(1);
    while let Some(arg) = args.next() {
        match arg.as_str() {
            "--capture-request" => {
                capture_request = Some(std::path::PathBuf::from(
                    args.next().ok_or("missing capture request path")?,
                ));
            }
            "--capture-after" => {
                let seconds = args.next().ok_or("missing capture delay")?.parse::<u64>()?;
                let path = args.next().ok_or("missing capture path")?;
                capture = Some((seconds, std::path::PathBuf::from(path)));
            }
            "--shell" => shell = true,
            "--winit" => (),
            "--mode" => {
                requested_mode = Some(dimensions(&args.next().ok_or("missing mode dimensions")?)?)
            }
            "--drm" => drm_device = Some(args.next().ok_or("missing DRM device")?),
            "--test-resize" => {
                let seconds = args.next().ok_or("missing resize delay")?.parse::<u64>()?;
                let (width, height) = dimensions(&args.next().ok_or("missing resize dimensions")?)?;
                test_resize = Some((seconds, width, height));
            }
            "--exit-after" => {
                lifetime = Some(args.next().ok_or("missing seconds")?.parse::<u64>()?)
            }
            "--" => {
                command.extend(args);
                break;
            }
            "--help" => {
                println!(
                    "archtv-compositor [--winit | --drm DEVICE] [--shell] [--mode WIDTHxHEIGHT] [--exit-after SECONDS] [--test-resize SECONDS WIDTHxHEIGHT] [--capture-after SECONDS OUTPUT] [--capture-request FILE] [-- PROGRAM ARGS...]"
                );
                return Ok(());
            }
            _ => return Err(format!("unknown argument: {arg}").into()),
        }
    }
    if capture_request.is_some() && capture.is_none() {
        return Err("--capture-request requires --capture-after".into());
    }
    let signals = Signals::new(&[Signal::SIGTERM, Signal::SIGINT])?;
    let mut event_loop: EventLoop<TvCompositor> = EventLoop::try_new()?;
    let display: Display<TvCompositor> = Display::new()?;
    let mut state = TvCompositor::new(&mut event_loop, display)?;
    if let Some(device) = drm_device {
        if test_resize.is_some() {
            return Err("--test-resize requires winit".into());
        }
        drm::init(
            &mut event_loop,
            &mut state,
            std::path::Path::new(&device),
            capture,
            capture_request,
            requested_mode,
        )?;
    } else {
        if capture.is_some() {
            return Err("--capture-after requires DRM".into());
        }
        winit::init(&mut event_loop, &mut state, test_resize, requested_mode)?;
    }
    event_loop
        .handle()
        .insert_source(signals, |_, _, state| state.loop_signal.stop())?;
    if let Some(seconds) = lifetime {
        event_loop.handle().insert_source(
            Timer::from_duration(Duration::from_secs(seconds)),
            |_, _, state| {
                state.loop_signal.stop();
                TimeoutAction::Drop
            },
        )?;
    }
    let supervisor = session::start(&mut event_loop, &mut state, command, shell)?;
    tracing::info!(socket = ?state.socket_name, "TV_COMPOSITOR_READY");
    let result = event_loop.run(None, &mut state, |state| {
        // Protocol replies must progress even when no surface needs repainting.
        if let Err(error) = state.display_handle.flush_clients() {
            tracing::warn!(?error, "client flush failed");
        }
    });
    if let Some(supervisor) = supervisor {
        supervisor.borrow_mut().stop();
    }
    if let Some(shutdown) = state.shutdown_backend.take() {
        shutdown();
    }
    tracing::info!("TV_COMPOSITOR_STOPPED");
    result?;
    Ok(())
}

fn dimensions(value: &str) -> Result<(u32, u32), Box<dyn std::error::Error>> {
    let (width, height) = value.split_once('x').ok_or("expected WIDTHxHEIGHT")?;
    let (width, height) = (width.parse::<u32>()?, height.parse::<u32>()?);
    if !(320..=7680).contains(&width) || !(240..=4320).contains(&height) {
        return Err("invalid dimensions".into());
    }
    Ok((width, height))
}
