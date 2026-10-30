//! Read-only process-local host properties, not Android's global property service.
use jni_sys::{JNIEnv, jboolean, jclass, jint, jstring};
use std::{ffi::CStr, io};

unsafe fn property(env: *mut JNIEnv, key: jstring) -> io::Result<Option<String>> {
    if key.is_null() {
        return Err(io::Error::other("Null property name"));
    }
    let name = unsafe {
        let bytes = (**env).GetStringUTFChars.unwrap()(env, key, std::ptr::null_mut());
        if bytes.is_null() {
            return Err(io::Error::other("Cannot read property name"));
        }
        let name = CStr::from_ptr(bytes).to_bytes().to_vec();
        (**env).ReleaseStringUTFChars.unwrap()(env, key, bytes);
        name
    };
    if !name.is_ascii() {
        return Err(io::Error::other("Host property names must be ASCII"));
    }
    let name = String::from_utf8(name).map_err(io::Error::other)?;
    Ok(std::env::var(format!("ARCHTV_ANDROID_PROPERTY_{name}")).ok())
}

/// # Safety
/// ART supplies valid JNI references. Decimal integer String/int overload only;
/// handle-based properties and mutation remain unsupported.
#[unsafe(no_mangle)]
pub unsafe extern "system" fn Java_android_os_SystemProperties_native_1get_1int__Ljava_lang_String_2I(
    env: *mut JNIEnv,
    _: jclass,
    key: jstring,
    default: jint,
) -> jint {
    super::guard(env, || {
        Ok(unsafe { property(env, key)? }
            .and_then(|value| value.parse::<i32>().ok())
            .unwrap_or(default))
    })
}

/// # Safety
/// ART supplies valid JNI references. Returned text uses JNI UTF-16, including
/// non-ASCII and supplementary characters. Empty/missing values use the Java default.
#[unsafe(no_mangle)]
pub unsafe extern "system" fn Java_android_os_SystemProperties_native_1get__Ljava_lang_String_2Ljava_lang_String_2(
    env: *mut JNIEnv,
    _: jclass,
    key: jstring,
    default: jstring,
) -> jstring {
    super::guard(env, || {
        let value = unsafe { property(env, key)? }.unwrap_or_default();
        if value.is_empty() && !default.is_null() {
            return Ok(default);
        }
        let text: Vec<u16> = value.encode_utf16().collect();
        let length = i32::try_from(text.len()).map_err(io::Error::other)?;
        Ok(unsafe { (**env).NewString.unwrap()(env, text.as_ptr(), length) })
    })
}

/// # Safety
/// ART supplies valid JNI references. Values match AOSP libbase ParseBool's
/// case-sensitive spellings; absent or invalid values preserve the caller default.
#[unsafe(no_mangle)]
pub unsafe extern "system" fn Java_android_os_SystemProperties_native_1get_1boolean__Ljava_lang_String_2Z(
    env: *mut JNIEnv,
    _: jclass,
    key: jstring,
    default: jboolean,
) -> jboolean {
    super::guard(env, || {
        Ok(match unsafe { property(env, key)? }.as_deref() {
            Some("1" | "y" | "yes" | "on" | "true") => 1,
            Some("0" | "n" | "no" | "off" | "false") => 0,
            _ => default,
        })
    })
}
