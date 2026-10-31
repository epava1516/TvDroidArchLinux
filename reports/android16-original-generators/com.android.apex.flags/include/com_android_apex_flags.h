#pragma once




#ifndef COM_ANDROID_APEX_FLAGS
#define COM_ANDROID_APEX_FLAGS(FLAG) COM_ANDROID_APEX_FLAGS_##FLAG
#endif

#ifndef COM_ANDROID_APEX_FLAGS_MOUNT_BEFORE_DATA
#define COM_ANDROID_APEX_FLAGS_MOUNT_BEFORE_DATA false
#endif

#ifdef __cplusplus

#include <memory>

namespace com::android::apex::flags {

class flag_provider_interface {
public:
    virtual ~flag_provider_interface() = default;
    virtual bool mount_before_data() = 0;
};

 extern std::unique_ptr<flag_provider_interface> provider_;


constexpr inline bool mount_before_data() {
    return COM_ANDROID_APEX_FLAGS_MOUNT_BEFORE_DATA;
}

}

extern "C" {
#endif // __cplusplus


bool com_android_apex_flags_mount_before_data();

#ifdef __cplusplus
} // extern "C"
#endif

