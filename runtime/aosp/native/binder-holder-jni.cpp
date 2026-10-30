// Linux host entrypoints call the unmodified original AOSP holder implementation.
// No Binder driver, remote transaction or native JavaBBinder transport is provided.
#include "android_util_Binder.cpp"
extern "C" JNIEXPORT jlong JNICALL Java_android_os_Binder_getNativeBBinderHolder(JNIEnv* env, jclass type) {
    return android_os_Binder_getNativeBBinderHolder(env, type);
}
extern "C" JNIEXPORT jlong JNICALL Java_android_os_Binder_getNativeFinalizer(JNIEnv* env, jclass type) {
    return android_os_Binder_getNativeFinalizer(env, type);
}
