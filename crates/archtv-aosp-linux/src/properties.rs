//! Read-only host property source for the original SystemProperties integer getter.
//! This is process-local configuration, not Android's global property service.
use jni_sys::{JNIEnv, jclass, jint, jstring};
use std::{ffi::CStr, io};

/// # Safety
/// ART provides valid JNI references. Only the String/int overload is exported;
/// handle-based property access and mutation remain unimplemented.
#[unsafe(no_mangle)]
pub unsafe extern "system" fn Java_android_os_SystemProperties_native_1get_1int__Ljava_lang_String_2I(
    env: *mut JNIEnv,
    _: jclass,
    key: jstring,
    default: jint,
) -> jint {
    super::guard(env, || {
        if key.is_null() {
            return Err(io::Error::other("Null property name"));
        }
        let name = unsafe {
            let bytes = (**env).GetStringUTFChars.unwrap()(env, key, std::ptr::null_mut());
            if bytes.is_null() {
                return Err(io::Error::other("Cannot read property name"));
            }
            let name = CStr::from_ptr(bytes).to_string_lossy().into_owned();
            (**env).ReleaseStringUTFChars.unwrap()(env, key, bytes);
            name
        };
        let value = std::env::var(format!("ARCHTV_ANDROID_PROPERTY_{name}"));
        Ok(value
            .ok()
            .and_then(|value| value.parse::<i32>().ok())
            .unwrap_or(default))
    })
}
