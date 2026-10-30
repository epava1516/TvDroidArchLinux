//! Calling identity for a local Linux process. No Binder IPC transport is implemented.
use jni_sys::{JNIEnv, jboolean, jclass, jint, jlong};
use std::cell::Cell;
thread_local! { static IDENTITY: Cell<Option<(u32, u32)>> = const { Cell::new(None) }; }
fn local() -> (u32, u32) {
    unsafe { (libc::getuid(), libc::getpid() as u32) }
}
fn current() -> (u32, u32) {
    IDENTITY.with(|identity| identity.get().unwrap_or_else(local))
}
#[unsafe(no_mangle)]
pub extern "system" fn Java_android_os_Binder_getCallingPid() -> jint {
    current().1 as jint
}
#[unsafe(no_mangle)]
pub extern "system" fn Java_android_os_Binder_getCallingUid() -> jint {
    current().0 as jint
}
#[unsafe(no_mangle)]
pub extern "system" fn Java_android_os_Binder_isDirectlyHandlingTransaction() -> jboolean {
    // No entrypoint accepts incoming transactions in this local-only adapter.
    0
}
#[unsafe(no_mangle)]
pub extern "system" fn Java_android_os_Binder_clearCallingIdentity() -> jlong {
    let (uid, pid) = current();
    IDENTITY.with(|identity| identity.set(None));
    ((u64::from(uid) << 32) | u64::from(pid)) as jlong
}
#[unsafe(no_mangle)]
pub extern "system" fn Java_android_os_Binder_restoreCallingIdentity(token: jlong) {
    let uid = ((token as u64) >> 32) as u32;
    let pid = token as u32;
    IDENTITY.with(|identity| identity.set(Some((uid, pid))));
}
#[unsafe(no_mangle)]
pub extern "system" fn Java_android_os_Binder_flushPendingCommands(_: *mut JNIEnv, _: jclass) {
    // Local-only mode has no transaction writer and cannot enqueue Binder commands.
    // Transaction APIs remain unimplemented; this does not report IPC success.
}
