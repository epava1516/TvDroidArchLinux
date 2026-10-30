//! Text logging for original android.util.Log on Linux stderr, without logd.
use jni_sys::{JNIEnv, jboolean, jclass, jint, jstring};
use std::io::{self, Write};

const PAYLOAD: usize = 4068;

unsafe fn string(env: *mut JNIEnv, value: jstring) -> io::Result<Option<String>> {
    if value.is_null() {
        return Ok(None);
    }
    unsafe {
        let length = (**env).GetStringLength.unwrap()(env, value);
        if !(0..=1_048_576).contains(&length) {
            return Err(io::Error::other("Log string exceeds host budget"));
        }
        let chars = (**env).GetStringChars.unwrap()(env, value, std::ptr::null_mut());
        if chars.is_null() {
            return Err(io::Error::other("Cannot read log string"));
        }
        let result = String::from_utf16_lossy(std::slice::from_raw_parts(chars, length as usize));
        (**env).ReleaseStringChars.unwrap()(env, value, chars);
        Ok(Some(result))
    }
}

fn level(value: &str) -> Option<i32> {
    match value.to_ascii_uppercase().as_str() {
        "V" | "VERBOSE" => Some(2),
        "D" | "DEBUG" => Some(3),
        "I" | "INFO" => Some(4),
        "W" | "WARN" => Some(5),
        "E" | "ERROR" => Some(6),
        "A" | "ASSERT" => Some(7),
        "S" | "SILENT" => Some(8),
        _ => None,
    }
}

fn threshold(tag: &str) -> i32 {
    let mut keys = Vec::new();
    if !tag.is_empty() && !tag.contains(['\0', '=']) {
        keys.extend([format!("log.tag.{tag}"), format!("persist.log.tag.{tag}")]);
    }
    keys.extend(["log.tag".into(), "persist.log.tag".into()]);
    keys.into_iter()
        .find_map(|key| {
            std::env::var(format!("ARCHTV_ANDROID_PROPERTY_{key}"))
                .ok()
                .and_then(|v| level(&v))
        })
        .unwrap_or(4)
}

fn prefix(text: &str, maximum: usize) -> &str {
    let mut end = text.len().min(maximum);
    while !text.is_char_boundary(end) {
        end -= 1;
    }
    &text[..end]
}

/// # Safety
/// ART supplies the thread-local JNI environment and valid String references.
#[unsafe(no_mangle)]
pub unsafe extern "system" fn Java_android_util_Log_isLoggable(
    env: *mut JNIEnv,
    _: jclass,
    tag: jstring,
    priority: jint,
) -> jboolean {
    super::guard(env, || {
        let tag = unsafe { string(env, tag)? }.unwrap_or_default();
        Ok(((2..=7).contains(&priority) && priority >= threshold(&tag)) as jboolean)
    })
}

/// # Safety
/// ART supplies valid JNI references. Null messages throw NPE; errors never report success.
#[unsafe(no_mangle)]
pub unsafe extern "system" fn Java_android_util_Log_println_1native(
    env: *mut JNIEnv,
    _: jclass,
    buffer: jint,
    priority: jint,
    tag: jstring,
    message: jstring,
) -> jint {
    super::guard(env, || {
        let channel = match buffer {
            0 => "main",
            1 => "radio",
            3 => "system",
            4 => "crash",
            _ => return Ok(-libc::EOPNOTSUPP),
        };
        if !(2..=7).contains(&priority) {
            return Ok(-libc::EINVAL);
        }
        if message.is_null() {
            unsafe {
                let class =
                    (**env).FindClass.unwrap()(env, c"java/lang/NullPointerException".as_ptr());
                if !class.is_null() {
                    (**env).ThrowNew.unwrap()(env, class, c"println needs a message".as_ptr());
                    (**env).DeleteLocalRef.unwrap()(env, class);
                }
            }
            return Ok(0);
        }
        let tag = unsafe { string(env, tag)? }.unwrap_or_default();
        if priority < threshold(&tag) {
            return Ok(-libc::EPERM);
        }
        let message = unsafe { string(env, message)? }.unwrap_or_default();
        // Budget the Android text payload: priority byte and two NUL terminators.
        let Some(available) = PAYLOAD.checked_sub(tag.len().saturating_add(3)) else {
            return Ok(-libc::E2BIG);
        };
        let accepted = prefix(&message, available);
        let entry =
            format!("ANDROID_LOG buffer={channel} priority={priority} tag={tag:?} {accepted}\n");
        io::stderr().lock().write_all(entry.as_bytes())?;
        Ok(accepted.len() as jint)
    })
}

/// # Safety
/// ART calls the private ordinary JNI method with its valid environment/class.
#[unsafe(no_mangle)]
pub unsafe extern "system" fn Java_android_util_Log_logger_1entry_1max_1payload_1native(
    _: *mut JNIEnv,
    _: jclass,
) -> jint {
    PAYLOAD as jint
}

#[cfg(test)]
mod tests {
    #[test]
    fn levels_and_unicode_boundary() {
        assert_eq!(super::level("debug"), Some(3));
        assert_eq!(super::level("S"), Some(8));
        assert_eq!(super::level("garbage"), None);
        assert_eq!(super::prefix("ñ📺x", 5), "ñ");
        assert_eq!(super::prefix("ñ📺x", 6), "ñ📺");
    }
}
