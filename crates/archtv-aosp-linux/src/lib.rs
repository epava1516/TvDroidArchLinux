//! JNI adapters for original AOSP MessageQueue; Java scheduling remains upstream.
mod clock;
mod identity;
mod logging;
mod properties;
mod queue;
mod tracing;
use jni_sys::{JNIEnv, jboolean, jclass, jint, jlong, jobject, jvalue};
use queue::Queue;
use std::{
    collections::HashMap,
    ffi::CString,
    io,
    sync::{
        Arc, Mutex, OnceLock,
        atomic::{AtomicI64, Ordering},
    },
};
static QUEUES: OnceLock<Mutex<HashMap<i64, Arc<Queue>>>> = OnceLock::new();
static NEXT: AtomicI64 = AtomicI64::new(1);
fn queues() -> &'static Mutex<HashMap<i64, Arc<Queue>>> {
    QUEUES.get_or_init(Mutex::default)
}
fn lookup(handle: i64) -> io::Result<Arc<Queue>> {
    queues()
        .lock()
        .map_err(|_| io::Error::other("Queue registry poisoned"))?
        .get(&handle)
        .cloned()
        .ok_or_else(|| io::Error::other("Invalid queue handle"))
}
// JNI supplies a valid thread-local JNIEnv. Never replace an already pending Java exception.
unsafe fn throw(env: *mut JNIEnv, message: &str) {
    unsafe {
        if (**env).ExceptionCheck.unwrap()(env) != 0 {
            return;
        }
        let class = (**env).FindClass.unwrap()(env, c"java/lang/IllegalStateException".as_ptr());
        if !class.is_null() {
            let text = CString::new(message.replace('\0', "?")).expect("NUL removed");
            (**env).ThrowNew.unwrap()(env, class, text.as_ptr());
            (**env).DeleteLocalRef.unwrap()(env, class);
        }
    }
}
fn guard<T: Default>(env: *mut JNIEnv, action: impl FnOnce() -> io::Result<T>) -> T {
    match std::panic::catch_unwind(std::panic::AssertUnwindSafe(action)) {
        Ok(Ok(value)) => value,
        Ok(Err(error)) => {
            unsafe {
                throw(env, &error.to_string());
            }
            T::default()
        }
        Err(_) => {
            unsafe {
                throw(env, "Panic in Linux queue adapter");
            }
            T::default()
        }
    }
}

/// # Safety
/// Called by ART with a valid JNI environment and MessageQueue class.
#[unsafe(no_mangle)]
pub unsafe extern "system" fn Java_android_os_MessageQueue_nativeInit(
    env: *mut JNIEnv,
    _: jclass,
) -> jlong {
    guard(env, || {
        let queue = Arc::new(Queue::new()?);
        let handle = NEXT.fetch_add(1, Ordering::Relaxed);
        if handle <= 0 {
            return Err(io::Error::other("Queue handles exhausted"));
        }
        queues()
            .lock()
            .map_err(|_| io::Error::other("Queue registry poisoned"))?
            .insert(handle, queue);
        Ok(handle)
    })
}
/// # Safety
/// Called by ART with the opaque handle returned by nativeInit.
#[unsafe(no_mangle)]
pub unsafe extern "system" fn Java_android_os_MessageQueue_nativeDestroy(
    env: *mut JNIEnv,
    _: jclass,
    handle: jlong,
) {
    guard(env, || {
        let queue = queues()
            .lock()
            .map_err(|_| io::Error::other("Queue registry poisoned"))?
            .remove(&handle)
            .ok_or_else(|| io::Error::other("Invalid queue handle"))?;
        queue.wake()?; // Release an outstanding poll; Arc retains its descriptors until it returns.
        Ok(())
    });
}
/// # Safety
/// Called by ART with a live MessageQueue instance on its polling thread.
#[unsafe(no_mangle)]
pub unsafe extern "system" fn Java_android_os_MessageQueue_nativePollOnce(
    env: *mut JNIEnv,
    object: jobject,
    handle: jlong,
    timeout: jint,
) {
    guard(env, || {
        let queue = lookup(handle)?;
        // The local class reference and method ID remain valid throughout this native call.
        unsafe {
            let class = (**env).GetObjectClass.unwrap()(env, object);
            if class.is_null() {
                return Err(io::Error::other("Cannot resolve MessageQueue class"));
            }
            let method = (**env).GetMethodID.unwrap()(
                env,
                class,
                c"dispatchEvents".as_ptr(),
                c"(II)I".as_ptr(),
            );
            (**env).DeleteLocalRef.unwrap()(env, class);
            if method.is_null() {
                return Err(io::Error::other("Cannot resolve FD dispatcher"));
            }
            queue.poll(timeout, |descriptor, events| {
                let arguments = [jvalue { i: descriptor }, jvalue { i: events }];
                let result =
                    (**env).CallIntMethodA.unwrap()(env, object, method, arguments.as_ptr());
                if (**env).ExceptionCheck.unwrap()(env) != 0 {
                    return Err(io::Error::other("Java FD callback threw"));
                }
                Ok(result)
            })
        }
    });
}
/// # Safety
/// Called by ART with a live opaque queue handle.
#[unsafe(no_mangle)]
pub unsafe extern "system" fn Java_android_os_MessageQueue_nativeWake(
    env: *mut JNIEnv,
    _: jclass,
    handle: jlong,
) {
    guard(env, || lookup(handle)?.wake());
}
/// # Safety
/// Called by ART with a live opaque queue handle.
#[unsafe(no_mangle)]
pub unsafe extern "system" fn Java_android_os_MessageQueue_nativeIsPolling(
    env: *mut JNIEnv,
    _: jclass,
    handle: jlong,
) -> jboolean {
    guard(env, || Ok(u8::from(lookup(handle)?.is_polling())))
}
/// # Safety
/// Called by ART with a live opaque queue handle and process-local descriptor.
#[unsafe(no_mangle)]
pub unsafe extern "system" fn Java_android_os_MessageQueue_nativeSetFileDescriptorEvents(
    env: *mut JNIEnv,
    _: jclass,
    handle: jlong,
    descriptor: jint,
    events: jint,
) {
    guard(env, || lookup(handle)?.set_events(descriptor, events));
}
