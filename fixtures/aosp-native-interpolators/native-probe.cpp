// Test-only access to owned original interpolators; excluded from production.
#include <jni.h>
#include <Interpolator.h>

using android::uirenderer::Interpolator;

extern "C" JNIEXPORT jfloat JNICALL
Java_org_archtv_aospprobe_NativeInterpolatorsProbe_evaluate(JNIEnv* env, jclass, jlong value, jfloat input) {
    if (!value) {
        jclass type = env->FindClass("java/lang/IllegalArgumentException");
        if (type) { env->ThrowNew(type, "Null interpolator"); env->DeleteLocalRef(type); }
        return 0;
    }
    return reinterpret_cast<Interpolator*>(value)->interpolate(input);
}

extern "C" JNIEXPORT void JNICALL
Java_org_archtv_aospprobe_NativeInterpolatorsProbe_release(JNIEnv*, jclass, jlong value) {
    delete reinterpret_cast<Interpolator*>(value);
}
