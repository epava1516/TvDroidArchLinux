#include "com_android_ueventd_flags.h"





namespace com::android::ueventd::flags {

class flag_provider : public flag_provider_interface {
    public:

        
        virtual bool enable_threadpool_coldboot() override {
            return COM_ANDROID_UEVENTD_FLAGS_ENABLE_THREADPOOL_COLDBOOT;
        }

    

    };

    static flag_provider_interface* get_provider_instance() {
        static flag_provider* instance_ = new flag_provider();
        return instance_;
    }

    std::unique_ptr<flag_provider_interface> provider_(get_provider_instance());
}


bool com_android_ueventd_flags_enable_threadpool_coldboot() {
    return COM_ANDROID_UEVENTD_FLAGS_ENABLE_THREADPOOL_COLDBOOT;
}

