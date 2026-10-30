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
#include <ziparchive/zip_archive.h>
#include <set>
#include <unistd.h>

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
        if (format != 0 || (flags & ~jint(android::PROPERTY_SYSTEM)) != 0 || provider) {
            fail(env, "java/lang/UnsupportedOperationException", "Only path APKs with optional PROPERTY_SYSTEM supported"); return jlong(0);
        }
        auto apk = android::ApkAssets::Load(string(env, path), android::package_property_t(flags));
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
namespace {
// NativeAllocationRegistry's real release callback. Themes are original AOSP objects.
void release_theme(void* pointer) { delete static_cast<android::Theme*>(pointer); }
}
extern "C" JNIEXPORT jlong JNICALL Java_android_content_res_AssetManager_nativeGetThemeFreeFunction(
    JNIEnv*, jclass) {
    return static_cast<jlong>(reinterpret_cast<uintptr_t>(&release_theme));
}
extern "C" JNIEXPORT jlong JNICALL Java_android_content_res_AssetManager_nativeThemeCreate(
    JNIEnv* env, jclass, jlong handle) {
    return guard<jlong>(env, 0, [&] {
        return static_cast<jlong>(reinterpret_cast<uintptr_t>(managers.at(handle)->value.NewTheme().release()));
    });
}
extern "C" JNIEXPORT void JNICALL Java_android_content_res_AssetManager_nativeSetConfiguration(
    JNIEnv* env, jclass, jlong handle, jint mcc, jint mnc, jstring locale,
    jint orientation, jint touchscreen, jint density, jint keyboard, jint keyboard_hidden,
    jint navigation, jint width, jint height, jint smallest_width_dp, jint width_dp,
    jint height_dp, jint layout, jint ui_mode, jint color_mode, jint sdk) {
    guard<int>(env, 0, [&] {
        android::ResTable_config configuration{};
        configuration.mcc = uint16_t(mcc);
        configuration.mnc = uint16_t(mnc);
        configuration.orientation = uint8_t(orientation);
        configuration.touchscreen = uint8_t(touchscreen);
        configuration.density = uint16_t(density);
        configuration.keyboard = uint8_t(keyboard);
        configuration.inputFlags = uint8_t(keyboard_hidden);
        configuration.navigation = uint8_t(navigation);
        configuration.screenWidth = uint16_t(width);
        configuration.screenHeight = uint16_t(height);
        configuration.smallestScreenWidthDp = uint16_t(smallest_width_dp);
        configuration.screenWidthDp = uint16_t(width_dp);
        configuration.screenHeightDp = uint16_t(height_dp);
        configuration.screenLayout = uint8_t(layout);
        configuration.screenLayout2 = uint8_t((layout & 0x300) >> 8);
        configuration.uiMode = uint8_t(ui_mode);
        configuration.colorMode = uint8_t(color_mode);
        configuration.sdkVersion = uint16_t(sdk);
        if (locale) configuration.setBcp47Locale(string(env, locale).c_str());
        managers.at(handle)->value.SetConfiguration(configuration);
        return 0;
    });
}

namespace {
std::u16string xmlText(const char16_t* text, size_t size, size_t maximum = 512*1024) {
    if (!text || size > maximum) throw std::runtime_error("Invalid manifest string");
    return std::u16string(text, size);
}
std::u16string ascii16(const std::string& text) {
    return std::u16string(text.begin(), text.end());
}
}

// Flat, typed manifest attributes for the Linux application metadata adapter.
// ZIP and binary XML decoding are the original libziparchive/androidfw parsers.
extern "C" JNIEXPORT jobjectArray JNICALL
Java_org_archtv_apkruntime_ApkMetadata_nativeRead(JNIEnv* env, jclass, jstring path) {
    return guard<jobjectArray>(env, nullptr, [&]() -> jobjectArray {
        std::string filename = string(env, path);
        if (filename.empty() || filename.find('\0') != std::string::npos)
            throw std::runtime_error("Invalid APK path");
        struct Archive {
            ZipArchiveHandle value = nullptr;
            ~Archive() { if (value) CloseArchive(value); }
        } archive;
        if (OpenArchive(filename.c_str(), &archive.value) != 0)
            throw std::runtime_error("Cannot open APK manifest archive");
        ZipEntry64 entry;
        if (FindEntry(archive.value, "AndroidManifest.xml", &entry) != 0
                || entry.uncompressed_length == 0 || entry.uncompressed_length > 1024*1024)
            throw std::runtime_error("Missing or oversized APK manifest");
        std::vector<uint8_t> bytes(entry.uncompressed_length);
        if (ExtractToMemory(archive.value, &entry, bytes.data(), bytes.size()) != 0)
            throw std::runtime_error("Cannot extract APK manifest");
        android::ResXMLTree xml;
        if (xml.setTo(bytes.data(), bytes.size(), false) != android::NO_ERROR)
            throw std::runtime_error("Invalid APK binary XML");
        std::vector<std::u16string> result, stack;
        size_t outputUnits = 0;
        auto append = [&](std::u16string key, std::u16string type, std::u16string data) {
            size_t needed = key.size() + type.size() + data.size();
            if (needed > 2*1024*1024 - outputUnits)
                throw std::runtime_error("Manifest metadata output exceeds budget");
            outputUnits += needed;
            result.push_back(std::move(key)); result.push_back(std::move(type)); result.push_back(std::move(data));
        };
        std::set<std::u16string> keys, sections;
        bool rootSeen = false;
        size_t events = 0;
        for (;;) {
            auto event = xml.next();
            if (++events > 100000 || event == android::ResXMLParser::BAD_DOCUMENT)
                throw std::runtime_error("Invalid or oversized manifest event stream");
            if (event == android::ResXMLParser::END_DOCUMENT) break;
            if (event != android::ResXMLParser::START_TAG && event != android::ResXMLParser::END_TAG) continue;
            size_t length = 0;
            const char16_t* name = xml.getElementName(&length);
            std::u16string tag = xmlText(name, length, 256);
            if (event == android::ResXMLParser::END_TAG) {
                if (stack.empty() || stack.back() != tag) throw std::runtime_error("Unbalanced manifest tags");
                stack.pop_back();
                continue;
            }
            stack.push_back(tag);
            if (stack.size() > 64) throw std::runtime_error("Manifest nesting exceeds budget");
            if (stack.size() == 1) {
                if (rootSeen || tag != u"manifest") throw std::runtime_error("Invalid manifest root");
                rootSeen = true;
            }
            bool collect = stack.size() == 1 || (stack.size() == 2
                    && (tag == u"uses-sdk" || tag == u"application" || tag == u"supports-screens"));
            if (!collect) continue;
            if (!sections.insert(tag).second) throw std::runtime_error("Repeated metadata section");
            append(tag + u"/@present", u"18", u"1");
            size_t count = xml.getAttributeCount();
            if (count > 256) throw std::runtime_error("Manifest attribute budget exceeded");
            for (size_t i = 0; i < count; ++i) {
                size_t n = 0;
                const char16_t* ns = xml.getAttributeNamespace(i, &n);
                std::u16string prefix;
                if (ns) {
                    if (xmlText(ns, n, 1024) != u"http://schemas.android.com/apk/res/android") continue;
                    prefix = u"android:";
                }
                const char16_t* attribute = xml.getAttributeName(i, &n);
                std::u16string key = tag + u"/" + prefix + xmlText(attribute, n, 256);
                if (!keys.insert(key).second) throw std::runtime_error("Duplicate metadata attribute");
                android::Res_value value;
                if (xml.getAttributeValue(i, &value) < 0) throw std::runtime_error("Invalid metadata attribute");
                std::u16string data;
                if (value.dataType == android::Res_value::TYPE_STRING) {
                    auto text = xml.getStrings().stringAt(value.data);
                    if (!text.has_value()) throw std::runtime_error("Invalid manifest string index");
                    data = xmlText(text->data(), text->size());
                } else data = ascii16(std::to_string(value.data));
                append(std::move(key), ascii16(std::to_string(value.dataType)), std::move(data));
            }
        }
        if (!rootSeen || !stack.empty()) throw std::runtime_error("Incomplete manifest");
        append(u"host/uid", u"16", ascii16(std::to_string(getuid())));
        jclass strings = env->FindClass("java/lang/String");
        if (!strings) return nullptr;
        jobjectArray output = env->NewObjectArray(result.size(), strings, nullptr);
        env->DeleteLocalRef(strings);
        if (!output) return nullptr;
        for (size_t i = 0; i < result.size(); ++i) {
            jstring text = env->NewString(reinterpret_cast<const jchar*>(result[i].data()), result[i].size());
            if (!text) return nullptr;
            env->SetObjectArrayElement(output, i, text);
            env->DeleteLocalRef(text);
            if (env->ExceptionCheck()) return nullptr;
        }
        return output;
    });
}
