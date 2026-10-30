// Use the original table and implementations; only registration is host-specific.
#include "jni/android_graphics_animation_NativeInterpolatorFactory.cpp"

extern "C" JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void*) {
    JNIEnv* env = nullptr;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6) != JNI_OK) return JNI_ERR;
    jclass type = env->FindClass(android::kClassPathName);
    if (!type) return JNI_ERR;
    jint result = env->RegisterNatives(type, android::gMethods,
            sizeof(android::gMethods) / sizeof(android::gMethods[0]));
    env->DeleteLocalRef(type);
    return result == JNI_OK ? JNI_VERSION_1_6 : JNI_ERR;
}
