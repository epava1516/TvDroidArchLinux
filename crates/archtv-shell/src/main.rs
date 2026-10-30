//! Native TV shell and its isolated renderer measurement mode.
mod layout;
mod model;
mod render;
mod runtime;
mod view;
mod worker;
use std::{path::PathBuf, time::Instant};
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args().skip(1);
    let first = args.next();
    if first.as_deref() != Some("--render-probe") {
        let mut all = first.into_iter().chain(args);
        let mut exit_after = None;
        let mut capture = None;
        let mut capture_states = None;
        while let Some(arg) = all.next() {
            match arg.as_str() {
                "--exit-after" => {
                    exit_after = Some(all.next().ok_or("missing seconds")?.parse::<u64>()?)
                }
                "--capture-after" => {
                    let seconds = all.next().ok_or("missing capture delay")?.parse::<u64>()?;
                    capture = Some((
                        seconds,
                        PathBuf::from(all.next().ok_or("missing capture path")?),
                    ));
                }
                "--capture-states" => {
                    capture_states = Some(PathBuf::from(
                        all.next().ok_or("missing capture directory")?,
                    ))
                }
                "--help" => {
                    println!(
                        "archtv-shell [--exit-after SECONDS] [--capture-after SECONDS FILE.png] [--capture-states DIRECTORY] | --render-probe DIRECTORY"
                    );
                    return Ok(());
                }
                _ => return Err(format!("unknown argument: {arg}").into()),
            }
        }
        return runtime::run(exit_after, capture, capture_states);
    }
    let directory = PathBuf::from(args.next().ok_or("missing output directory")?);
    std::fs::create_dir_all(&directory)?;
    let font = std::fs::read("/usr/share/fonts/TTF/DejaVuSans.ttf")?;
    let mut results = String::from(
        "CPU renderer prototype: tiny-skia + fontdue, no Wayland/DRM or input latency claim.\n",
    );
    for (width, height) in [(1280, 720), (1920, 1080), (3840, 2160)] {
        let start = Instant::now();
        let mut canvas = render::Canvas::new(width, height, &font)?;
        canvas.home_probe(0);
        let cold = start.elapsed();
        for focus in 0..10 {
            canvas.home_probe(focus % 5);
        }
        let mut samples = Vec::new();
        for focus in 0..60 {
            let start = Instant::now();
            canvas.home_probe(focus % 5);
            samples.push(start.elapsed().as_secs_f64() * 1000.0);
        }
        samples.sort_by(f64::total_cmp);
        canvas
            .pixmap
            .save_png(directory.join(format!("home-{width}x{height}.png")))?;
        results.push_str(&format!(
            "{width}x{height}: cold_ms={:.2} warm_p50_ms={:.2} warm_p95_ms={:.2} canvas_bytes={}\n",
            cold.as_secs_f64() * 1000.0,
            samples[samples.len() / 2],
            samples[(samples.len() * 95).div_ceil(100) - 1],
            canvas.pixmap.data().len()
        ));
    }
    std::fs::write(directory.join("renderer-metrics.txt"), &results)?;
    print!("{results}");
    Ok(())
}
