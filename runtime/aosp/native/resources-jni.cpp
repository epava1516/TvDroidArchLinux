// Linux JNI adapter for original AOSP Java classes; resource algorithms remain AOSP.
#include <jni.h>
#include <androidfw/ApkAssets.h>
#include <androidfw/AssetManager2.h>
#include <utils/String8.h>
#include <mutex>
#include <unordered_map>
#include <memory>
#include <stdexcept>
#include <limits>

namespace {
std::mutex lock;
jlong sequence = 0;
struct Manager {
    std::vector<std::shared_ptr<android::ApkAssets>> assets;
    android::AssetManager2 value;
};
std::unordered_map<jlong, std::shared_ptr<android::ApkAssets>> assets;
std::unordered_map<jlong, std::unique_ptr<Manager>> managers;
void fail(JNIEnv* env, const char* type, const char* message) {
    jclass klass = env->FindClass(type);
    if (klass) env->ThrowNew(klass, message);
}
template<class R, class F> R guard(JNIEnv* env, R fallback, F work) {
    try { std::lock_guard<std::mutex> held(lock); return work(); }
    catch (const std::exception& error) {
        if (!env->ExceptionCheck()) fail(env, "java/lang/IllegalStateException", error.what());
        return fallback;
    }
}
jlong token() {
    if (sequence == std::numeric_limits<jlong>::max()) throw std::runtime_error("Native handle limit");
    return ++sequence;
}
std::string string(JNIEnv* env, jstring value) {
    if (!value) return {};
    const jchar* chars = env->GetStringChars(value, nullptr);
    if (!chars) throw std::runtime_error("Cannot read Java string");
    android::String8 utf8(reinterpret_cast<const char16_t*>(chars), env->GetStringLength(value));
    env->ReleaseStringChars(value, chars);
    return std::string(utf8.string(), utf8.size());
}
const android::ResStringPool* pool(jlong handle) {
    auto& apk = assets.at(handle);
    return apk->GetLoadedArsc()->GetStringPool();
}
}
extern "C" JNIEXPORT jlong JNICALL Java_android_content_res_ApkAssets_nativeLoad(
    JNIEnv* env, jclass, jint format, jstring path, jint flags, jobject provider) {
    return guard<jlong>(env, 0, [&] {
        if (format != 0 || flags != 0 || provider) {
            fail(env, "java/lang/UnsupportedOperationException", "Only ordinary path APKs supported"); return jlong(0);
        }
        auto apk = android::ApkAssets::Load(string(env, path));
        if (!apk) { fail(env, "java/io/IOException", "Cannot load APK resources"); return jlong(0); }
        jlong id = token(); assets.emplace(id, std::shared_ptr<android::ApkAssets>(std::move(apk))); return id;
    });
}
extern "C" JNIEXPORT jlong JNICALL Java_android_content_res_ApkAssets_nativeGetStringBlock(
    JNIEnv* env, jclass, jlong handle) {
    return guard<jlong>(env, 0, [&] { pool(handle); return handle; });
}
extern "C" JNIEXPORT void JNICALL Java_android_content_res_ApkAssets_nativeDestroy(
    JNIEnv* env, jclass, jlong handle) {
    guard<int>(env, 0, [&] { if (!assets.erase(handle)) throw std::runtime_error("Unknown APK handle"); return 0; });
}
extern "C" JNIEXPORT jint JNICALL Java_android_content_res_StringBlock_nativeGetSize(
    JNIEnv* env, jclass, jlong handle) {
    return guard<jint>(env, 0, [&] { return jint(pool(handle)->size()); });
}
extern "C" JNIEXPORT jstring JNICALL Java_android_content_res_StringBlock_nativeGetString(
    JNIEnv* env, jclass, jlong handle, jint index) {
    return guard<jstring>(env, nullptr, [&] {
        const auto* strings = pool(handle);
        if (index < 0 || size_t(index) >= strings->size()) {
            fail(env, "java/lang/IndexOutOfBoundsException", "String pool index"); return jstring(nullptr);
        }
        auto text = strings->stringAt(index);
        if (!text.has_value()) return jstring(nullptr);
        return env->NewString(reinterpret_cast<const jchar*>(text->data()), text->size());
    });
}
extern "C" JNIEXPORT jintArray JNICALL Java_android_content_res_StringBlock_nativeGetStyle(
    JNIEnv* env, jclass, jlong handle, jint index) {
    return guard<jintArray>(env, nullptr, [&] {
        const auto* strings = pool(handle);
        if (index < 0 || size_t(index) >= strings->size()) throw std::out_of_range("Style index");
        auto style = strings->styleAt(index);
        if (style.has_value())
            fail(env, "java/lang/UnsupportedOperationException", "Styled strings not ported yet");
        return jintArray(nullptr);
    });
}
extern "C" JNIEXPORT jlong JNICALL Java_android_content_res_AssetManager_nativeCreate(JNIEnv* env, jclass) {
    return guard<jlong>(env, 0, [&] { jlong id = token(); managers.emplace(id, std::make_unique<Manager>()); return id; });
}
extern "C" JNIEXPORT void JNICALL Java_android_content_res_AssetManager_nativeDestroy(
    JNIEnv* env, jclass, jlong handle) {
    guard<int>(env, 0, [&] { if (!managers.erase(handle)) throw std::runtime_error("Unknown manager handle"); return 0; });
}
extern "C" JNIEXPORT void JNICALL Java_android_content_res_AssetManager_nativeSetApkAssets(
    JNIEnv* env, jclass, jlong handle, jobjectArray input, jboolean invalidate) {
    guard<int>(env, 0, [&] {
        if (!input) { fail(env, "java/lang/NullPointerException", "APK assets"); return 0; }
        auto& manager = *managers.at(handle);
        std::vector<std::shared_ptr<android::ApkAssets>> owned;
        std::vector<const android::ApkAssets*> raw;
        jclass klass = env->FindClass("android/content/res/ApkAssets");
        if (!klass) return 0;
        jfieldID field = env->GetFieldID(klass, "mNativePtr", "J");
        if (!field) return 0;
        for (jsize i = 0; i < env->GetArrayLength(input); ++i) {
            jobject object = env->GetObjectArrayElement(input, i);
            if (!object) throw std::runtime_error("Null APK entry");
            auto apk = assets.at(env->GetLongField(object, field));
            env->DeleteLocalRef(object);
            raw.push_back(apk.get()); owned.push_back(std::move(apk));
        }
        if (!manager.value.SetApkAssets(std::move(raw), invalidate)) throw std::runtime_error("Invalid APK asset set");
        manager.assets = std::move(owned);
        return 0;
    });
}
extern "C" JNIEXPORT jint JNICALL Java_android_content_res_AssetManager_nativeGetResourceIdentifier(
    JNIEnv* env, jclass, jlong handle, jstring name, jstring type, jstring package) {
    return guard<jint>(env, 0, [&] {
        if (!name) { fail(env, "java/lang/NullPointerException", "Resource name"); return jint(0); }
        auto id = managers.at(handle)->value.GetResourceId(string(env, name), string(env, type), string(env, package));
        return id.has_value() ? jint(*id) : jint(0);
    });
}
extern "C" JNIEXPORT jint JNICALL Java_android_content_res_AssetManager_nativeGetResourceValue(
    JNIEnv* env, jclass, jlong handle, jint id, jshort density, jobject output, jboolean resolve) {
    return guard<jint>(env, 0, [&] {
        if (!output) { fail(env, "java/lang/NullPointerException", "TypedValue"); return jint(0); }
        auto& manager = managers.at(handle)->value;
        auto value = manager.GetResource(uint32_t(id), false, uint16_t(density));
        if (!value.has_value()) return jint(0);
        if (resolve && !manager.ResolveReference(*value).has_value()) return jint(0);
        jclass klass = env->GetObjectClass(output);
        const char* names[] = {"type", "assetCookie", "data", "resourceId", "changingConfigurations", "density"};
        jint values[] = {value->type, jint(value->cookie + 1), jint(value->data), jint(value->resid),
                         jint(value->flags), value->config.density};
        for (size_t i = 0; i < 6; ++i) {
            jfieldID field = env->GetFieldID(klass, names[i], "I");
            if (!field) return jint(0);
            env->SetIntField(output, field, values[i]);
        }
        jfieldID text = env->GetFieldID(klass, "string", "Ljava/lang/CharSequence;");
        if (!text) return jint(0);
        env->SetObjectField(output, text, nullptr);
        return jint(value->cookie + 1);
    });
}
