//! Host tracing is disabled: no trace collector or enabled tags are configured.
//! Original Trace.traceBegin/traceEnd therefore skip their optional emission calls.
use jni_sys::jlong;

/// CriticalNative ABI: no JNIEnv or class arguments. Reports the actual disabled state;
/// enabling or emitting Android trace events remains unsupported.
#[unsafe(no_mangle)]
pub extern "system" fn Java_android_os_Trace_nativeGetEnabledTags() -> jlong {
    0
}
