#pragma once




#ifndef COM_ANDROID_UEVENTD_FLAGS
#define COM_ANDROID_UEVENTD_FLAGS(FLAG) COM_ANDROID_UEVENTD_FLAGS_##FLAG
#endif

#ifndef COM_ANDROID_UEVENTD_FLAGS_ENABLE_THREADPOOL_COLDBOOT
#define COM_ANDROID_UEVENTD_FLAGS_ENABLE_THREADPOOL_COLDBOOT false
#endif

#ifdef __cplusplus

#include <memory>

namespace com::android::ueventd::flags {

class flag_provider_interface {
public:
    virtual ~flag_provider_interface() = default;
    virtual bool enable_threadpool_coldboot() = 0;
};

 extern std::unique_ptr<flag_provider_interface> provider_;


constexpr inline bool enable_threadpool_coldboot() {
    return COM_ANDROID_UEVENTD_FLAGS_ENABLE_THREADPOOL_COLDBOOT;
}

}

extern "C" {
#endif // __cplusplus


bool com_android_ueventd_flags_enable_threadpool_coldboot();

#ifdef __cplusplus
} // extern "C"
#endif

