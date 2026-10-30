#include "critical-host-adapter.h"
#include <stdint.h>
#include <stdlib.h>

using archtv::aosp::CriticalHostAdapter;
static jlong stored;
static void context(JNIEnv* env, jclass type) { if (env || type) abort(); }
static jlong integer(JNIEnv* env, jclass type, jlong a, jint b, jboolean flip) {
    context(env, type);
    uint64_t value = uint64_t(a) ^ (uint64_t(uint32_t(b)) << 32);
    return jlong(flip ? ~value : value);
}
static jdouble floating(JNIEnv* env, jclass type, jdouble a, jfloat b, jlong c) {
    context(env, type);
    return a + double(b) * .5 + double(c % 1024);
}
static jboolean compare(JNIEnv* env, jclass type, jfloat a, jdouble b) {
    context(env, type);
    return a < b ? JNI_TRUE : JNI_FALSE;
}
static jfloat scale(JNIEnv* env, jclass type, jfloat a, jfloat b) {
    context(env, type);
    return a * b;
}
static jint lower(JNIEnv* env, jclass type, jlong a, jint b) {
    context(env, type);
    return jint(uint32_t(a) ^ uint32_t(b));
}
static void record(JNIEnv* env, jclass type, jlong value) { context(env, type); stored = value; }
static jlong read(JNIEnv* env, jclass type) { context(env, type); return stored; }
static jdouble wide(JNIEnv* env, jclass type, jlong a, jint b, jfloat c, jdouble d,
                    jlong e, jint f, jfloat g, jdouble h, jlong i, jint j, jfloat k, jdouble l) {
    context(env, type);
    return double(a) + 2.*b + 3.*c + 4.*d + 5.*e + 6.*f + 7.*g + 8.*h + 9.*i + 10.*j + 11.*k + 12.*l;
}

#define ENTRY(name, signature) {#name, signature, (void*)CriticalHostAdapter<&name>::call}
static const JNINativeMethod methods[] = {
    ENTRY(integer, "(JIZ)J"), ENTRY(floating, "(DFJ)D"), ENTRY(compare, "(FD)Z"),
    ENTRY(record, "(J)V"), ENTRY(read, "()J"), ENTRY(wide, "(JIFDJIFDJIFD)D"),
    ENTRY(scale, "(FF)F"), ENTRY(lower, "(JI)I"),
};
#undef ENTRY
extern "C" JNIEXPORT jint JNICALL JNI_OnLoad(JavaVM* vm, void*) {
    JNIEnv* env = nullptr;
    if (vm->GetEnv(reinterpret_cast<void**>(&env), JNI_VERSION_1_6) != JNI_OK) return JNI_ERR;
    jclass type = env->FindClass("org/archtv/aospprobe/CriticalHostProbe");
    if (!type) return JNI_ERR;
    jint result = env->RegisterNatives(type, methods, sizeof(methods)/sizeof(methods[0]));
    env->DeleteLocalRef(type);
    return result == JNI_OK ? JNI_VERSION_1_6 : JNI_ERR;
}
