// Laboratory adapter: all APK/resource parsing and reference resolution use AOSP.
#include <androidfw/AssetManager.h>
#include <androidfw/ResourceTypes.h>
#include <utils/String16.h>
#include <utils/String8.h>
#include <cstdio>

int main(int argc, char** argv) {
    if (argc < 3) { std::fprintf(stderr, "Usage: resource-probe APK RESOURCE_NAME...\n"); return 2; }
    android::AssetManager manager;
    int32_t cookie = 0;
    if (!manager.addAssetPath(android::String8(argv[1]), &cookie)) {
        std::fprintf(stderr, "Cannot load APK assets\n"); return 3;
    }
    const android::ResTable& table = manager.getResources();
    for (int index = 2; index < argc; ++index) {
        android::String16 name(argv[index]);
        uint32_t id = table.identifierForName(name.string(), name.size());
        if (!id) { std::fprintf(stderr, "Resource name not found\n"); return 4; }
        android::Res_value value{};
        ssize_t block = table.getResource(id, &value);
        if (block < 0) { std::fprintf(stderr, "Resource value not found\n"); return 5; }
        block = table.resolveReference(&value, block);
        if (block < 0 || value.dataType != android::Res_value::TYPE_STRING) {
            std::fprintf(stderr, "Not a resolved string\n"); return 6;
        }
        const android::ResStringPool* pool = table.getTableStringBlock(block);
        auto text = pool->stringAt(value.data);
        if (!text.has_value()) { std::fprintf(stderr, "String pool lookup failed\n"); return 7; }
        android::String8 utf8(text->data(), text->size());
        std::printf("%08x\t", id);
        for (size_t offset = 0; offset < utf8.size(); ++offset)
            std::printf("%02x", static_cast<unsigned char>(utf8.string()[offset]));
        std::putchar('\n');
    }
    return 0;
}
