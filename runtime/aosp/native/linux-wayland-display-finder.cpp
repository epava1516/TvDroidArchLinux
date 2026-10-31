#include "Device.h"
#include "linux-wayland-frame-composer.h"
namespace aidl::android::hardware::graphics::composer3::impl {
HWC3::Error findDisplays(const DrmClient*,std::vector<DisplayMultiConfigs>* displays) {
    FrameComposer* backend=nullptr;
    auto error=Device::getInstance().getComposer(&backend);
    if(error!=HWC3::Error::None)return error;
    // This build's only factory is LinuxWaylandFrameComposer; no fallback/no-op.
    return static_cast<LinuxWaylandFrameComposer*>(backend)->configurations(displays);
}
}
