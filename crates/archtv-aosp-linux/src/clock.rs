//! AOSP CriticalNative SystemClock ABI has no JNIEnv/class arguments.
use jni_sys::jlong;
fn clock(clock: libc::clockid_t, divisor: i64) -> jlong {
    let mut time = libc::timespec {
        tv_sec: 0,
        tv_nsec: 0,
    };
    // All selected clocks are defined by the supported Linux kernel. A failed
    // primitive cannot be represented as a valid clock value; CriticalNative
    // has no JNI environment with which to raise a Java exception.
    if unsafe { libc::clock_gettime(clock, &mut time) } < 0 {
        std::process::abort();
    }
    (time.tv_sec * 1_000_000_000 + time.tv_nsec) / divisor
}
#[unsafe(no_mangle)]
pub extern "system" fn Java_android_os_SystemClock_uptimeMillis() -> jlong {
    clock(libc::CLOCK_MONOTONIC, 1_000_000)
}
#[unsafe(no_mangle)]
pub extern "system" fn Java_android_os_SystemClock_uptimeNanos() -> jlong {
    clock(libc::CLOCK_MONOTONIC, 1)
}
#[unsafe(no_mangle)]
pub extern "system" fn Java_android_os_SystemClock_elapsedRealtime() -> jlong {
    clock(libc::CLOCK_BOOTTIME, 1_000_000)
}
#[unsafe(no_mangle)]
pub extern "system" fn Java_android_os_SystemClock_elapsedRealtimeNanos() -> jlong {
    clock(libc::CLOCK_BOOTTIME, 1)
}
#[unsafe(no_mangle)]
pub extern "system" fn Java_android_os_SystemClock_currentThreadTimeMillis() -> jlong {
    clock(libc::CLOCK_THREAD_CPUTIME_ID, 1_000_000)
}
#[unsafe(no_mangle)]
pub extern "system" fn Java_android_os_SystemClock_currentThreadTimeMicro() -> jlong {
    clock(libc::CLOCK_THREAD_CPUTIME_ID, 1_000)
}
#[unsafe(no_mangle)]
pub extern "system" fn Java_android_os_SystemClock_currentTimeMicro() -> jlong {
    clock(libc::CLOCK_REALTIME, 1_000)
}
