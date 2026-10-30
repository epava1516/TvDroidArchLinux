// Linux host entrypoints call the unmodified original AOSP holder implementation.
// No Binder driver, remote transaction or native JavaBBinder transport is provided.
#include "android_util_Binder.cpp"
extern "C" JNIEXPORT jlong JNICALL Java_android_os_Binder_getNativeBBinderHolder(JNIEnv* env, jclass type) {
    return android_os_Binder_getNativeBBinderHolder(env, type);
}
extern "C" JNIEXPORT jlong JNICALL Java_android_os_Binder_getNativeFinalizer(JNIEnv* env, jclass type) {
    return android_os_Binder_getNativeFinalizer(env, type);
}
// Linux bootstrap returns the configured local registry, never an Android driver proxy.
extern "C" JNIEXPORT jobject JNICALL Java_com_android_internal_os_BinderInternal_getContextObject(JNIEnv* env, jclass) {
    jclass registry=env->FindClass("org/archtv/aosplinux/LinuxServiceRegistry");
    if(!registry)return nullptr;
    jmethodID method=env->GetStaticMethodID(registry,"contextObject","()Landroid/os/IBinder;");
    if(!method){env->DeleteLocalRef(registry);return nullptr;}
    jobject result=env->CallStaticObjectMethod(registry,method);
    env->DeleteLocalRef(registry);return result;
}
