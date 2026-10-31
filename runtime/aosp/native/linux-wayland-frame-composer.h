#pragma once
#include "FrameComposer.h"
#include "DisplayFinder.h"
#include "linux-wayland-output.h"
#include <atomic>
#include <mutex>
#include <thread>
namespace aidl::android::hardware::graphics::composer3::impl {
// Experimental synchronous client-composition backend. No native present fence
// is fabricated; original PRESENT_FENCE_IS_NOT_RELIABLE contract remains visible.
class LinuxWaylandFrameComposer final : public FrameComposer {
 public:
    ~LinuxWaylandFrameComposer() override;
    HWC3::Error init() override;
    HWC3::Error registerOnHotplugCallback(const HotplugCallback&) override;
    HWC3::Error unregisterOnHotplugCallback() override;
    HWC3::Error onDisplayCreate(Display*) override;
    HWC3::Error onDisplayDestroy(Display*) override;
    HWC3::Error onDisplayClientTargetSet(Display*) override;
    HWC3::Error validateDisplay(Display*,DisplayChanges*) override;
    HWC3::Error presentDisplay(Display*,::android::base::unique_fd*,std::unordered_map<int64_t,::android::base::unique_fd>*) override;
    HWC3::Error onActiveConfigChange(Display*) override;
    HWC3::Error configurations(std::vector<DisplayMultiConfigs>*);
 private:
    void monitor();
    std::mutex mutex_,callback_mutex_;
    archtv::aosp::LinuxWaylandOutput output_;
    HotplugCallback callback_;
    bool connected_=false,display_live_=false;
    std::atomic<bool> stop_{false};
    std::thread monitor_;
};
}
