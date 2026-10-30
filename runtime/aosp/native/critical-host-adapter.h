#pragma once
#include <jni.h>
#include <type_traits>

namespace archtv::aosp {

template <typename T> constexpr bool jni_primitive =
        std::is_same_v<T, jboolean> || std::is_same_v<T, jbyte>
        || std::is_same_v<T, jchar> || std::is_same_v<T, jshort>
        || std::is_same_v<T, jint> || std::is_same_v<T, jlong>
        || std::is_same_v<T, jfloat> || std::is_same_v<T, jdouble>;

// HWUI's host CRITICAL_JNI_PARAMS are anonymous JNIEnv*/jclass parameters.
// ART CriticalNative instead passes primitives only. Keep the original host
// body and let C++ generate the register/stack adaptation for its exact type.
// Only use this for host functions whose two context parameters are unused.
template <auto Function, typename Signature = decltype(Function)>
struct CriticalHostAdapter;

template <auto Function, typename Result, typename... Args>
struct CriticalHostAdapter<Function, Result (*)(JNIEnv*, jclass, Args...)> {
    static_assert(std::is_void_v<Result> || jni_primitive<Result>, "CriticalNative return must be primitive");
    static_assert((jni_primitive<Args> && ...), "CriticalNative arguments must be primitive");
    static Result call(Args... args) {
        return Function(nullptr, nullptr, args...);
    }
};

}  // namespace archtv::aosp
