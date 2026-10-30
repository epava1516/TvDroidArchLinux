#include "critical-host-adapter.h"
static jint invalid(JNIEnv*,jclass,jobject){return 0;}
auto entry = &archtv::aosp::CriticalHostAdapter<&invalid>::call;
