#![cfg(target_os = "linux")]
use archtv_core::native_process::{NativeFailure, NativeProcess, Startup};
use std::{
    io,
    os::fd::{AsRawFd, FromRawFd, OwnedFd},
    process::Command,
    time::{Duration, Instant},
};
fn helper(body: &str) -> Command {
    let mut command = Command::new("/usr/bin/python");
    command.args([
        "-c",
        &format!("import os,time\nfd=int(os.environ['ARCHTV_NATIVE_CONTROL_FD'])\n{body}"),
    ]);
    command
}
fn watch(process: &NativeProcess) -> OwnedFd {
    let fd = unsafe { libc::fcntl(process.pidfd(), libc::F_DUPFD_CLOEXEC, 3) };
    assert!(fd >= 0);
    unsafe { OwnedFd::from_raw_fd(fd) }
}
fn assert_exited(fd: &OwnedFd) {
    let mut poll = libc::pollfd {
        fd: fd.as_raw_fd(),
        events: libc::POLLIN,
        revents: 0,
    };
    assert_eq!(unsafe { libc::poll(&mut poll, 1, 1000) }, 1);
    assert_ne!(poll.revents & libc::POLLIN, 0);
}
#[test]
fn cooperative_exit_requires_ack_and_actual_exit() {
    let cmd = helper(
        "os.write(fd,b'ARCHTV_NATIVE_V1 DIAGNOSTIC_STARTED\\n')\ndata=b''\nwhile not data.endswith(b'\\n'): data+=os.read(fd,1)\nassert data==b'ARCHTV_NATIVE_V1 STOP\\n'\nos.write(fd,b'ARCHTV_NATIVE_V1 STOPPED\\n')",
    );
    let mut process = NativeProcess::spawn(cmd).unwrap();
    let watched = watch(&process);
    process
        .wait_started(Startup::Diagnostic, Duration::from_secs(2))
        .unwrap();
    assert!(process.stop(Duration::from_secs(2)).unwrap().success());
    assert_exited(&watched);
}
#[test]
fn startup_mode_mismatch_kills_owned_child() {
    let mut process = NativeProcess::spawn(helper(
        "os.write(fd,b'ARCHTV_NATIVE_V1 STARTED\\n')\ntime.sleep(20)",
    ))
    .unwrap();
    let watched = watch(&process);
    assert_eq!(
        process
            .wait_started(Startup::Diagnostic, Duration::from_secs(2))
            .unwrap_err()
            .kind(),
        io::ErrorKind::InvalidData
    );
    drop(process);
    assert_exited(&watched);
}
#[test]
fn startup_timeout_and_cleanup() {
    let mut process = NativeProcess::spawn(helper("time.sleep(20)")).unwrap();
    let watched = watch(&process);
    let before = Instant::now();
    assert_eq!(
        process
            .wait_started(Startup::Diagnostic, Duration::from_millis(50))
            .unwrap_err()
            .kind(),
        io::ErrorKind::TimedOut
    );
    drop(process);
    assert!(before.elapsed() < Duration::from_secs(2));
    assert_exited(&watched);
}
#[test]
fn shutdown_timeout_is_error_and_child_is_reaped() {
    let mut process = NativeProcess::spawn(helper(
        "os.write(fd,b'ARCHTV_NATIVE_V1 DIAGNOSTIC_STARTED\\n')\nos.read(fd,128)\ntime.sleep(20)",
    ))
    .unwrap();
    let watched = watch(&process);
    process
        .wait_started(Startup::Diagnostic, Duration::from_secs(2))
        .unwrap();
    assert_eq!(
        process.stop(Duration::from_millis(50)).unwrap_err().kind(),
        io::ErrorKind::TimedOut
    );
    assert_exited(&watched);
}
#[test]
fn oversized_status_is_rejected_and_cleaned() {
    let mut process =
        NativeProcess::spawn(helper("os.write(fd,b'x'*200)\ntime.sleep(20)")).unwrap();
    let watched = watch(&process);
    assert_eq!(
        process
            .wait_started(Startup::Diagnostic, Duration::from_secs(2))
            .unwrap_err()
            .kind(),
        io::ErrorKind::InvalidData
    );
    drop(process);
    assert_exited(&watched);
}

#[test]
fn acknowledgment_does_not_hide_failed_exit() {
    let mut process = NativeProcess::spawn(helper("os.write(fd,b'ARCHTV_NATIVE_V1 DIAGNOSTIC_STARTED\\n')\nos.read(fd,128)\nos.write(fd,b'ARCHTV_NATIVE_V1 STOPPED\\n')\nos._exit(7)")).unwrap();
    let watched = watch(&process);
    process
        .wait_started(Startup::Diagnostic, Duration::from_secs(2))
        .unwrap();
    assert_eq!(
        process.stop(Duration::from_secs(2)).unwrap_err().kind(),
        io::ErrorKind::Other
    );
    assert_exited(&watched);
}

#[test]
fn successful_exit_without_shutdown_ack_is_rejected() {
    let mut process = NativeProcess::spawn(helper(
        "os.write(fd,b'ARCHTV_NATIVE_V1 DIAGNOSTIC_STARTED\\n')\nos.read(fd,128)\nos._exit(0)",
    ))
    .unwrap();
    let watched = watch(&process);
    process
        .wait_started(Startup::Diagnostic, Duration::from_secs(2))
        .unwrap();
    assert_eq!(
        process.stop(Duration::from_secs(2)).unwrap_err().kind(),
        io::ErrorKind::UnexpectedEof
    );
    assert_exited(&watched);
}

#[test]
fn original_shutdown_is_typed_failure_and_actual_exit_is_collected() {
    let mut process = NativeProcess::spawn(helper(
        "os.write(fd,b'ARCHTV_NATIVE_V1 FAILED_SHUTDOWN 7265626f6f74\\n')\nos._exit(69)",
    ))
    .unwrap();
    let error = process
        .wait_started(Startup::Diagnostic, Duration::from_secs(2))
        .unwrap_err();
    assert_eq!(
        error.get_ref().unwrap().downcast_ref::<NativeFailure>(),
        Some(&NativeFailure::ShutdownRequested(b"reboot".to_vec()))
    );
    assert_eq!(
        process.wait_failed(Duration::from_secs(2)).unwrap().code(),
        Some(69)
    );
}
#[test]
fn malformed_failure_payload_cannot_be_a_typed_original_request() {
    let mut process = NativeProcess::spawn(helper(
        "os.write(fd,b'ARCHTV_NATIVE_V1 FAILED_SHUTDOWN zz\\n')\ntime.sleep(20)",
    ))
    .unwrap();
    let watched = watch(&process);
    assert_eq!(
        process
            .wait_started(Startup::Diagnostic, Duration::from_secs(2))
            .unwrap_err()
            .kind(),
        io::ErrorKind::InvalidData
    );
    drop(process);
    assert_exited(&watched);
}
#[test]
fn oversize_request_is_explicit_failure_never_truncated_success() {
    let mut process = NativeProcess::spawn(helper(
        "os.write(fd,b'ARCHTV_NATIVE_V1 FAILED_SHUTDOWN_OVERSIZE\\n')\nos._exit(69)",
    ))
    .unwrap();
    let error = process
        .wait_started(Startup::Diagnostic, Duration::from_secs(2))
        .unwrap_err();
    assert_eq!(
        error.get_ref().unwrap().downcast_ref::<NativeFailure>(),
        Some(&NativeFailure::ShutdownRequestTooLong)
    );
    assert_eq!(
        process.wait_failed(Duration::from_secs(2)).unwrap().code(),
        Some(69)
    );
}

#[test]
fn failure_cannot_be_overridden_by_later_startup_ack() {
    let mut process=NativeProcess::spawn(helper("os.write(fd,b'ARCHTV_NATIVE_V1 FAILED_SHUTDOWN 7265626f6f74\\nARCHTV_NATIVE_V1 DIAGNOSTIC_STARTED\\n')\nos._exit(69)")).unwrap();
    assert!(
        process
            .wait_started(Startup::Diagnostic, Duration::from_secs(2))
            .is_err()
    );
    assert_eq!(
        process
            .wait_started(Startup::Diagnostic, Duration::from_secs(2))
            .unwrap_err()
            .to_string(),
        "native component already failed"
    );
    assert_eq!(
        process.wait_failed(Duration::from_secs(2)).unwrap().code(),
        Some(69)
    );
}

#[test]
fn partial_failure_survives_observation_timeout() {
    let mut process = NativeProcess::spawn(helper(
        "os.write(fd,b'ARCHTV_NATIVE_V1 FAILED_SHUTDOWN ')\ntime.sleep(0.3)\nos.write(fd,b'7265626f6f74\\n')\nos._exit(69)",
    )).unwrap();
    assert_eq!(
        process
            .wait_started(Startup::Diagnostic, Duration::from_millis(100))
            .unwrap_err()
            .kind(),
        io::ErrorKind::TimedOut
    );
    let error = process
        .wait_started(Startup::Diagnostic, Duration::from_secs(2))
        .unwrap_err();
    assert_eq!(
        error
            .get_ref()
            .and_then(|e| e.downcast_ref::<NativeFailure>()),
        Some(&NativeFailure::ShutdownRequested(b"reboot".to_vec()))
    );
    assert_eq!(
        process.wait_failed(Duration::from_secs(2)).unwrap().code(),
        Some(69)
    );
}

#[test]
fn malformed_status_cannot_be_replaced_by_later_ack() {
    let mut process = NativeProcess::spawn(helper(
        "os.write(fd,b'ARCHTV_NATIVE_V1 FAILED_SHUTDOWN zz\\nARCHTV_NATIVE_V1 DIAGNOSTIC_STARTED\\n')\ntime.sleep(20)",
    )).unwrap();
    assert_eq!(
        process
            .wait_started(Startup::Diagnostic, Duration::from_secs(2))
            .unwrap_err()
            .kind(),
        io::ErrorKind::InvalidData
    );
    assert!(
        process
            .wait_started(Startup::Diagnostic, Duration::from_secs(2))
            .is_err()
    );
}
