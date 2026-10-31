// Diagnostic Linux-supervised entrypoint. Does not dispatch Android init.
#include "property_service.h"
#include <android-base/logging.h>
#include <sys/system_properties.h>
#include <stdio.h>
static void emit_value(void*, const char* name, const char* value, unsigned int) {
    printf("PROPERTY %s=%s\n", name, value);
}
static void emit_property(const prop_info* info, void*) {
    __system_property_read_callback(info, emit_value, nullptr);
}
int main(int argc, char** argv) {
    android::base::InitLogging(argv, android::base::StderrLogger);
    fprintf(stderr, "PROPERTY_INIT_BEGIN\n");
    android::init::PropertyInit();
    fprintf(stderr, "PROPERTY_INIT_RETURNED\n");
    const int result = __system_property_foreach(emit_property, nullptr);
    fprintf(stderr, "PROPERTY_ENUMERATION_RESULT %d\n", result);
    return result == 0 ? 0 : 1;
}
