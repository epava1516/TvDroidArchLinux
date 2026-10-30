//! Single-output CPU presentation using DRM dumb buffers and real page flips.
use crate::state::TvCompositor;
use smithay::{
    backend::{
        allocator::{
            Allocator, Fourcc, Modifier,
            dmabuf::{AsDmabuf, Dmabuf, DmabufMappingMode, DmabufSyncFlags},
            dumb::{DumbAllocator, DumbBuffer},
        },
        drm::DrmDeviceFd,
        libinput::{LibinputInputBackend, LibinputSessionInterface},
        renderer::{
            Bind, damage::OutputDamageTracker, element::surface::WaylandSurfaceRenderElement,
            pixman::PixmanRenderer,
        },
        session::{Event as SessionEvent, Session, libseat::LibSeatSession},
    },
    output::{Mode, Output, PhysicalProperties, Subpixel},
    reexports::{
        calloop::{
            EventLoop, Interest, Mode as IoMode, PostAction,
            generic::Generic,
            timer::{TimeoutAction, Timer},
        },
        drm::control::{self, Device as _},
        input::Libinput,
    },
    utils::{DeviceFd, Transform},
};
use std::{cell::RefCell, path::Path, rc::Rc, time::Duration};

type Result<T> = std::result::Result<T, Box<dyn std::error::Error>>;
struct Scanout {
    dmabuf: Dmabuf,
    framebuffer: control::framebuffer::Handle,
    _allocation: DumbBuffer,
}
struct Backend {
    fd: DrmDeviceFd,
    crtc: control::crtc::Handle,
    connector: control::connector::Handle,
    mode: control::Mode,
    previous: control::crtc::Info,
    buffers: Vec<Scanout>,
    current: usize,
    pending: Option<usize>,
    active: bool,
    renderer: PixmanRenderer,
    output: Output,
    damage: OutputDamageTracker,
    presented: u64,
    restored: bool,
    capture: Option<(u64, std::path::PathBuf)>,
}
impl Backend {
    fn capture(&mut self, state: &TvCompositor) -> Result<()> {
        use std::io::Write;
        if self.presented == 0
            || !self.active
            || !self
                .capture
                .as_ref()
                .is_some_and(|(seconds, _)| state.start_time.elapsed().as_secs() >= *seconds)
        {
            return Ok(());
        }
        let (_, path) = self.capture.take().unwrap();
        let buffer = &self.buffers[self.current].dmabuf;
        buffer.sync_plane(0, DmabufSyncFlags::START | DmabufSyncFlags::READ)?;
        let mapping = buffer.map_plane(0, DmabufMappingMode::READ)?;
        let (width, height) = self.mode.size();
        let stride = buffer.strides().next().ok_or("missing stride")? as usize;
        // The mapping remains alive and the displayed buffer is read only here.
        let bytes =
            unsafe { std::slice::from_raw_parts(mapping.ptr().cast::<u8>(), mapping.length()) };
        if bytes.len() < stride * usize::from(height) {
            return Err("short DRM mapping".into());
        }
        let mut rgb = Vec::with_capacity(usize::from(width) * usize::from(height) * 3);
        for row in bytes.chunks_exact(stride).take(usize::from(height)) {
            for pixel in row[..usize::from(width) * 4].chunks_exact(4) {
                rgb.extend_from_slice(&[pixel[2], pixel[1], pixel[0]]);
            }
        }
        buffer.sync_plane(0, DmabufSyncFlags::END | DmabufSyncFlags::READ)?;
        let mut file = std::fs::File::create(&path)?;
        write!(file, "P6\n{width} {height}\n255\n")?;
        file.write_all(&rgb)?;
        tracing::info!(path=%path.display(), "DRM_CAPTURED");
        Ok(())
    }
    fn restore(&self) {
        if let Err(error) = self.fd.set_crtc(
            self.crtc,
            self.previous.framebuffer(),
            self.previous.position(),
            &[self.connector],
            self.previous.mode(),
        ) {
            tracing::warn!(?error, "DRM_RESTORE_FAILED");
        }
    }
    fn modeset(&self) -> std::io::Result<()> {
        self.fd.set_crtc(
            self.crtc,
            Some(self.buffers[self.current].framebuffer),
            (0, 0),
            &[self.connector],
            Some(self.mode),
        )
    }
    fn draw(&mut self, state: &mut TvCompositor) -> Result<()> {
        if !self.active || self.pending.is_some() || !state.dirty {
            return Ok(());
        }
        let next = 1 - self.current;
        let mut target = self.renderer.bind(&mut self.buffers[next].dmabuf)?;
        smithay::desktop::space::render_output::<
            _,
            WaylandSurfaceRenderElement<PixmanRenderer>,
            _,
            _,
        >(
            &self.output,
            &mut self.renderer,
            &mut target,
            1.0,
            0,
            [&state.space],
            &[],
            &mut self.damage,
            [0.04, 0.05, 0.08, 1.0],
        )
        .map_err(|e| format!("Pixman render failed: {e:?}"))?;
        drop(target);
        self.fd.page_flip(
            self.crtc,
            self.buffers[next].framebuffer,
            control::PageFlipFlags::EVENT,
            None,
        )?;
        self.pending = Some(next);
        state.dirty = false;
        Ok(())
    }
    fn finish(&mut self, state: &mut TvCompositor) {
        let Some(next) = self.pending.take() else {
            return;
        };
        self.current = next;
        self.presented += 1;
        tracing::debug!(frame = self.presented, "DRM_PRESENTED");
        for window in state.space.elements() {
            if window
                .toplevel()
                .is_some_and(|top| Some(top.wl_surface()) == state.focus.current())
            {
                window.send_frame(
                    &self.output,
                    state.start_time.elapsed(),
                    Some(Duration::ZERO),
                    |_, _| Some(self.output.clone()),
                );
            }
        }
        state.space.refresh();
        state.popups.cleanup();
    }
}
impl Drop for Backend {
    fn drop(&mut self) {
        if !self.restored {
            self.restore();
        }
        for buffer in &self.buffers {
            let _ = self.fd.destroy_framebuffer(buffer.framebuffer);
        }
        tracing::info!(frames = self.presented, "DRM_STOPPED");
    }
}

pub fn init(
    event_loop: &mut EventLoop<TvCompositor>,
    state: &mut TvCompositor,
    path: &Path,
    capture: Option<(u64, std::path::PathBuf)>,
) -> Result<()> {
    let (mut session, notifier) = LibSeatSession::new()?;
    let fd = session.open(
        path,
        rustix::fs::OFlags::RDWR | rustix::fs::OFlags::NONBLOCK | rustix::fs::OFlags::CLOEXEC,
    )?;
    let fd = DrmDeviceFd::new(DeviceFd::from(fd));
    let resources = fd.resource_handles()?;
    let connector = resources
        .connectors()
        .iter()
        .find_map(|handle| {
            fd.get_connector(*handle, true)
                .ok()
                .filter(|info| info.state() == control::connector::State::Connected)
        })
        .ok_or("no connected DRM output")?;
    let mode = connector
        .modes()
        .iter()
        .find(|mode| mode.mode_type().contains(control::ModeTypeFlags::PREFERRED))
        .or_else(|| connector.modes().first())
        .copied()
        .ok_or("output has no modes")?;
    let crtc = connector
        .encoders()
        .iter()
        .find_map(|handle| {
            let encoder = fd.get_encoder(*handle).ok()?;
            resources
                .filter_crtcs(encoder.possible_crtcs())
                .first()
                .copied()
        })
        .ok_or("no usable CRTC")?;
    let previous = fd.get_crtc(crtc)?;
    let size = mode.size();
    let mut allocator = DumbAllocator::new(fd.clone());
    let mut buffers = Vec::new();
    for _ in 0..2 {
        let allocation = allocator.create_buffer(
            size.0 as u32,
            size.1 as u32,
            Fourcc::Xrgb8888,
            &[Modifier::Linear],
        )?;
        let framebuffer = fd.add_framebuffer(allocation.handle(), 24, 32)?;
        let dmabuf = allocation.export()?;
        buffers.push(Scanout {
            dmabuf,
            framebuffer,
            _allocation: allocation,
        });
    }
    let output = Output::new(
        "ArchTV-DRM".into(),
        PhysicalProperties {
            size: connector
                .size()
                .map(|(w, h)| (w as i32, h as i32))
                .unwrap_or_default()
                .into(),
            subpixel: Subpixel::Unknown,
            make: "ArchTV".into(),
            model: format!("{:?}", connector.interface()),
            serial_number: "1".into(),
        },
    );
    let output_mode = Mode {
        size: (size.0 as i32, size.1 as i32).into(),
        refresh: mode.vrefresh() as i32 * 1000,
    };
    output.create_global::<TvCompositor>(&state.display_handle);
    output.change_current_state(
        Some(output_mode),
        Some(Transform::Normal),
        None,
        Some((0, 0).into()),
    );
    output.set_preferred(output_mode);
    state.space.map_output(&output, (0, 0));
    state.resize(size.0 as i32, size.1 as i32);
    let backend = Rc::new(RefCell::new(Backend {
        fd: fd.clone(),
        crtc,
        connector: connector.handle(),
        mode,
        previous,
        buffers,
        current: 0,
        pending: None,
        active: session.is_active(),
        renderer: PixmanRenderer::new()?,
        damage: OutputDamageTracker::from_output(&output),
        output,
        presented: 0,
        restored: false,
        capture,
    }));
    backend.borrow().modeset()?;
    let mut input = Libinput::new_with_udev(LibinputSessionInterface::from(session.clone()));
    input
        .udev_assign_seat(&session.seat())
        .map_err(|_| "cannot assign input seat")?;
    let mut session_input = input.clone();
    let session_backend = backend.clone();
    event_loop
        .handle()
        .insert_source(notifier, move |event, _, state| {
            let mut backend = session_backend.borrow_mut();
            match event {
                SessionEvent::PauseSession => {
                    state.release_all_keys();
                    session_input.suspend();
                    backend.active = false;
                    // logind has revoked access; libseat owns DRM master.
                    tracing::info!("SESSION_PAUSED");
                }
                SessionEvent::ActivateSession => {
                    let restored = backend.modeset();
                    if let Err(error) = restored {
                        tracing::error!(?error, "SESSION_RESUME_FAILED");
                        state.loop_signal.stop();
                        return;
                    }
                    backend.active = true;
                    backend.pending = None;
                    if session_input.resume().is_err() {
                        tracing::error!("INPUT_RESUME_FAILED");
                        state.loop_signal.stop();
                    }
                    state.dirty = true;
                    tracing::info!("SESSION_ACTIVE");
                }
            }
        })?;
    event_loop
        .handle()
        .insert_source(LibinputInputBackend::new(input), |event, _, state| {
            state.process_input_event(event)
        })?;
    let flips = backend.clone();
    event_loop.handle().insert_source(
        Generic::new(fd, Interest::READ, IoMode::Level),
        move |_, fd, state| {
            for event in fd.receive_events()? {
                if matches!(event, control::Event::PageFlip(_)) {
                    flips.borrow_mut().finish(state);
                }
            }
            Ok(PostAction::Continue)
        },
    )?;
    let cleanup = backend.clone();
    event_loop
        .handle()
        .insert_source(Timer::immediate(), move |_, _, state| {
            if let Err(error) = backend.borrow_mut().draw(state) {
                tracing::error!(%error, "DRM_RENDER_FAILED");
                state.loop_signal.stop();
            }
            if let Err(error) = backend.borrow_mut().capture(state) {
                tracing::error!(%error, "DRM_CAPTURE_FAILED");
                state.loop_signal.stop();
            }
            TimeoutAction::ToDuration(Duration::from_millis(16))
        })?;
    state.shutdown_backend = Some(Box::new(move || {
        let mut backend = cleanup.borrow_mut();
        if backend.active {
            backend.restore();
        }
        backend.restored = true;
    }));
    state.session = Some(session);
    tracing::info!(device=%path.display(), width=size.0, height=size.1, refresh=mode.vrefresh(), format="XRGB8888", modifier="LINEAR", buffers=2, renderer="Pixman", "DRM_READY");
    Ok(())
}
