#pragma once
// Serialized coordinator boundary, not an implementation of Android shutdown.
// Original Service::Start/Reap may request shutdown. Linux owns recovery policy.
// Install before service operations, remove after all producers have stopped.
#include "util.h"
#include <android-base/result.h>
#include <array>
#include <algorithm>
#include <string>
namespace archtv::aosp {
class LinuxShutdownSink {
 public:
    LinuxShutdownSink()=default;
    LinuxShutdownSink(const LinuxShutdownSink&)=delete;
    LinuxShutdownSink& operator=(const LinuxShutdownSink&)=delete;
    ~LinuxShutdownSink() {
        if(installed_==this) { android::init::trigger_shutdown=nullptr;installed_=nullptr; }
    }
    android::base::Result<void> Install() {
        if(installed_ || android::init::trigger_shutdown)
            return android::base::Error()<<"Shutdown boundary already installed";
        installed_=this;
        android::init::trigger_shutdown=&Receive;
        return {};
    }
    bool failed() const { return failed_; }
    std::string Frame() const {
        if(!failed_) return {};
        if(oversize_) return "ARCHTV_NATIVE_V1 FAILED_SHUTDOWN_OVERSIZE\n";
        std::string frame="ARCHTV_NATIVE_V1 FAILED_SHUTDOWN ";
        static constexpr char hex[]="0123456789abcdef";
        for(size_t i=0;i<size_;++i) { unsigned char c=command_[i];frame+=hex[c>>4];frame+=hex[c&15]; }
        frame+='\n';return frame;
    }
 private:
    static void Receive(const std::string& command) {
        auto& self=*installed_;
        // Keep the first failure, not a later consequence. Never execute the string.
        if(self.failed_) return;
        self.failed_=true;
        self.oversize_=command.size()>self.command_.size();
        if(!self.oversize_) {self.size_=command.size();std::copy(command.begin(),command.end(),self.command_.begin());}
    }
    inline static LinuxShutdownSink* installed_=nullptr;
    std::array<char,24> command_{};
    size_t size_=0;
    bool failed_=false,oversize_=false;
};
}
