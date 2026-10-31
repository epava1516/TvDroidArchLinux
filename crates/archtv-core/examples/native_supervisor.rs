//! Internal lifetime exerciser; component startup is not runtime readiness.
use archtv_core::native_process::{NativeProcess, Startup};
use std::{process::Command, time::Duration};
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args_os().skip(1);
    let expected = match args.next().as_deref() {
        Some(s) if s == "--diagnostic" => Startup::Diagnostic,
        Some(s) if s == "--component" => Startup::Component,
        _ => return Err("expected --diagnostic|--component -- executable [arguments]".into()),
    };
    if args.next().as_deref() != Some(std::ffi::OsStr::new("--")) {
        return Err("expected --".into());
    }
    let executable = args.next().ok_or("missing executable")?;
    let mut command = Command::new(executable);
    command.args(args).env_clear().env("PATH", "/usr/bin:/bin");
    let mut process = NativeProcess::spawn(command)?;
    println!(
        "NATIVE_PROCESS_OWNED pid={} pidfd={}",
        process.pid(),
        process.pidfd()
    );
    process.wait_started(expected, Duration::from_secs(10))?;
    println!("NATIVE_COMPONENT_STARTUP mode={expected:?} NOT_APK_READINESS");
    let exit = process.stop(Duration::from_secs(10))?;
    println!("NATIVE_COMPONENT_STOPPED exit={exit}");
    Ok(())
}
