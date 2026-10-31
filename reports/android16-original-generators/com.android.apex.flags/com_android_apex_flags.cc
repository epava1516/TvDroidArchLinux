#include "com_android_apex_flags.h"





namespace com::android::apex::flags {

class flag_provider : public flag_provider_interface {
    public:

        
        virtual bool mount_before_data() override {
            return COM_ANDROID_APEX_FLAGS_MOUNT_BEFORE_DATA;
        }

    

    };

    static flag_provider_interface* get_provider_instance() {
        static flag_provider* instance_ = new flag_provider();
        return instance_;
    }

    std::unique_ptr<flag_provider_interface> provider_(get_provider_instance());
}


bool com_android_apex_flags_mount_before_data() {
    return COM_ANDROID_APEX_FLAGS_MOUNT_BEFORE_DATA;
}

