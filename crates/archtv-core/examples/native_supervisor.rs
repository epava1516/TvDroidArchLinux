//! Internal lifetime exerciser; component startup is not runtime readiness.
use archtv_core::native_process::{NativeFailure, NativeProcess, Startup};
use std::{process::Command, time::Duration};
fn main() -> Result<(), Box<dyn std::error::Error>> {
    let mut args = std::env::args_os().skip(1);
    let expected = match args.next().as_deref() {
        Some(s) if s == "--diagnostic" => Startup::Diagnostic,
        Some(s) if s == "--component" => Startup::Component,
        _ => return Err("expected --diagnostic|--component -- executable [arguments]".into()),
    };
    let mut separator = args.next();
    let observation = if separator.as_deref() == Some(std::ffi::OsStr::new("--observe-ms")) {
        let millis: u64 = args
            .next()
            .ok_or("missing observation duration")?
            .to_str()
            .ok_or("invalid duration")?
            .parse()?;
        if millis > 60_000 {
            return Err("observation duration exceeds 60000ms".into());
        }
        separator = args.next();
        Duration::from_millis(millis)
    } else {
        Duration::ZERO
    };
    if separator.as_deref() != Some(std::ffi::OsStr::new("--")) {
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
    // Original property + manager + oneshot-client startup each has a bounded
    // native phase. Permit their combined MC1 deadline without masking it.
    if let Err(error) = process.wait_started(expected, Duration::from_secs(20)) {
        if error.get_ref().is_some_and(|e| e.is::<NativeFailure>()) {
            let status = process.wait_failed(Duration::from_secs(10))?;
            eprintln!("NATIVE_COMPONENT_FAILED cause={error} actual_exit={status}");
        }
        return Err(error.into());
    }
    println!("NATIVE_COMPONENT_STARTUP mode={expected:?} NOT_APK_READINESS");
    if !observation.is_zero() {
        match process.observe(observation) {
            Ok(None) => println!("NATIVE_OBSERVATION_NO_EVENT NOT_HEALTH_OR_APK_READINESS"),
            Ok(Some(exit)) => {
                return Err(format!("unexpected native exit after startup: {exit}").into());
            }
            Err(error) => {
                if error.get_ref().is_some_and(|e| e.is::<NativeFailure>()) {
                    let status = process.wait_failed(Duration::from_secs(10))?;
                    eprintln!("NATIVE_COMPONENT_FAILED cause={error} actual_exit={status}");
                }
                return Err(error.into());
            }
        }
    }
    let exit = process.stop(Duration::from_secs(10))?;
    println!("NATIVE_COMPONENT_STOPPED exit={exit}");
    Ok(())
}
