#include "linux-wayland-frame-composer.h"
#include "Display.h"
#include "Layer.h"
#include <ui/GraphicBufferMapper.h>
#include <ui/Rect.h>
#include <aidl/android/hardware/graphics/common/BufferUsage.h>
#include <aidl/android/hardware/graphics/common/PlaneLayout.h>
#include <sync/sync.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <cerrno>
#include <cstring>
#include <cstdlib>
#include <chrono>
#include <limits>
#include <vector>
#include <unistd.h>
namespace aidl::android::hardware::graphics::composer3::impl {
LinuxWaylandFrameComposer::~LinuxWaylandFrameComposer(){stop_=true;if(monitor_.joinable())monitor_.join();}
HWC3::Error LinuxWaylandFrameComposer::init() {
    std::lock_guard<std::mutex> lock(mutex_);
    int fd=-1;
    const char* inherited=std::getenv("ARCHTV_WAYLAND_FD");
    if(inherited) {
        char* end=nullptr;errno=0;long value=std::strtol(inherited,&end,10);
        if(errno || !end || *end || value<3 || value>65535)return HWC3::Error::BadParameter;
        fd=static_cast<int>(value);unsetenv("ARCHTV_WAYLAND_FD");
    } else {
        fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);if(fd<0)return HWC3::Error::NoResources;
        sockaddr_un address{};address.sun_family=AF_UNIX;
        std::strcpy(address.sun_path,"/dev/socket/archtv-wayland");
        if(connect(fd,reinterpret_cast<sockaddr*>(&address),sizeof(address))!=0){close(fd);return HWC3::Error::NoResources;}
    }
    if(!output_.Connect(fd) || output_.refresh_millihz()<=0)return HWC3::Error::NoResources;
    connected_=true;
    monitor_=std::thread([this]{monitor();});
    return HWC3::Error::None;
}
void LinuxWaylandFrameComposer::monitor() {
    while(!stop_) {
        bool disconnected=false;
        {
            std::lock_guard<std::mutex> lock(mutex_);
            if(connected_ && !output_.Poll()){connected_=false;disconnected=true;}
        }
        if(disconnected) {
            // Callback serialized with unregister; never hold transport mutex
            // while calling original client's display lifecycle code.
            std::lock_guard<std::mutex> lock(callback_mutex_);
            if(callback_)callback_(false,0,0,0,0,0,0);
        }
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
    }
}
HWC3::Error LinuxWaylandFrameComposer::registerOnHotplugCallback(const HotplugCallback& cb) {
    if(!cb)return HWC3::Error::BadParameter;
    std::lock_guard<std::mutex> lock(callback_mutex_);callback_=cb;return HWC3::Error::None;
}
HWC3::Error LinuxWaylandFrameComposer::unregisterOnHotplugCallback(){std::lock_guard<std::mutex> lock(callback_mutex_);callback_={};return HWC3::Error::None;}
HWC3::Error LinuxWaylandFrameComposer::configurations(std::vector<DisplayMultiConfigs>* result) {
    std::lock_guard<std::mutex> lock(mutex_);
    if(!connected_ || output_.width()<=0 || output_.height()<=0 || output_.refresh_millihz()<=0)return HWC3::Error::NoResources;
    int64_t period=1000000000000LL/output_.refresh_millihz();
    if(period<=0 || period>std::numeric_limits<int32_t>::max())return HWC3::Error::BadConfig;
    result->clear();result->push_back(DisplayMultiConfigs{.displayId=0,.activeConfigId=0,.configs={DisplayConfig(0,output_.width(),output_.height(),output_.dpi_x(),output_.dpi_y(),static_cast<int32_t>(period))}});
    DisplayConfig::addConfigGroups(&result->front().configs);return HWC3::Error::None;
}
HWC3::Error LinuxWaylandFrameComposer::onDisplayCreate(Display* d){std::lock_guard<std::mutex> lock(mutex_);if(!connected_ || display_live_ || d->getId()!=0)return HWC3::Error::BadDisplay;display_live_=true;return HWC3::Error::None;}
HWC3::Error LinuxWaylandFrameComposer::onDisplayDestroy(Display* d){std::lock_guard<std::mutex> lock(mutex_);if(!display_live_ || d->getId()!=0)return HWC3::Error::BadDisplay;display_live_=false;return HWC3::Error::None;}
HWC3::Error LinuxWaylandFrameComposer::onDisplayClientTargetSet(Display* d){std::lock_guard<std::mutex> lock(mutex_);if(!connected_ || !display_live_ || d->getId()!=0)return HWC3::Error::BadDisplay;return d->getClientTarget().getBuffer()?HWC3::Error::None:HWC3::Error::BadParameter;}
HWC3::Error LinuxWaylandFrameComposer::onActiveConfigChange(Display* d){std::lock_guard<std::mutex> lock(mutex_);int32_t id=-1;if(!connected_ || !display_live_ || d->getId()!=0)return HWC3::Error::BadDisplay;auto error=d->getActiveConfig(&id);return error==HWC3::Error::None && id==0?HWC3::Error::None:HWC3::Error::BadConfig;}
HWC3::Error LinuxWaylandFrameComposer::validateDisplay(Display* d,DisplayChanges* changes) {
    std::lock_guard<std::mutex> lock(mutex_);if(!connected_ || !display_live_ || d->getId()!=0)return HWC3::Error::BadDisplay;
    for(auto* layer:d->getOrderedLayers())if(layer->getCompositionType()!=Composition::CLIENT)changes->addLayerCompositionChange(d->getId(),layer->getId(),Composition::CLIENT);
    return HWC3::Error::None;
}
HWC3::Error LinuxWaylandFrameComposer::presentDisplay(Display* d,::android::base::unique_fd* present,std::unordered_map<int64_t,::android::base::unique_fd>* releases) {
    std::lock_guard<std::mutex> lock(mutex_);
    if(!connected_ || !display_live_ || d->getId()!=0)return HWC3::Error::BadDisplay;
    auto handle=d->getClientTarget().getBuffer();if(!handle)return HWC3::Error::BadParameter;
    errno=0;auto acquire=d->getClientTarget().getFence();
    if(!acquire.ok() && errno)return HWC3::Error::NoResources;
    if(acquire.ok() && sync_wait(acquire.get(),3000)!=0)return HWC3::Error::NoResources;
    auto& mapper=::android::GraphicBufferMapper::get();
    uint64_t w=0,h=0,allocation=0,protected_content=0;
    ::android::ui::PixelFormat format{};
    std::vector<aidl::android::hardware::graphics::common::PlaneLayout> planes;
    if(mapper.getWidth(handle,&w)!=0 || mapper.getHeight(handle,&h)!=0 || mapper.getAllocationSize(handle,&allocation)!=0 || mapper.getProtectedContent(handle,&protected_content)!=0 || mapper.getPixelFormatRequested(handle,&format)!=0 || mapper.getPlaneLayouts(handle,&planes)!=0)return HWC3::Error::NoResources;
    if(protected_content || planes.size()!=1)return HWC3::Error::Unsupported;
    if(w!=uint64_t(output_.width()) || h!=uint64_t(output_.height()) || w==0 || h==0 || w*h>16777216)return HWC3::Error::BadParameter;
    const auto& plane=planes[0];
    if(plane.offsetInBytes!=0 || plane.sampleIncrementInBits!=32 || plane.strideInBytes<0 || uint64_t(plane.strideInBytes)<w*4 || uint64_t(plane.strideInBytes)>allocation || h>allocation/uint64_t(plane.strideInBytes))return HWC3::Error::Unsupported;
    bool rgba=format==::android::ui::PixelFormat::RGBA_8888 || format==::android::ui::PixelFormat::RGBX_8888;
    if(!rgba && format!=::android::ui::PixelFormat::BGRA_8888)return HWC3::Error::Unsupported;
    std::vector<uint32_t> pixels(w*h);void* data=nullptr;
    if(mapper.lock(handle,static_cast<uint32_t>(aidl::android::hardware::graphics::common::BufferUsage::CPU_READ_OFTEN),::android::Rect(static_cast<int32_t>(w),static_cast<int32_t>(h)),&data)!=0)return HWC3::Error::NoResources;
    if(!data){mapper.unlock(handle);return HWC3::Error::NoResources;}
    for(uint64_t y=0;y<h;++y) {
        const auto* row=static_cast<const uint8_t*>(data)+y*uint64_t(plane.strideInBytes);
        for(uint64_t x=0;x<w;++x){const auto* p=row+x*4;pixels[y*w+x]=0xff000000u|(uint32_t(p[rgba?0:2])<<16)|(uint32_t(p[1])<<8)|p[rgba?2:0];}
    }
    ::android::base::unique_fd unlock;
    if(mapper.unlock(handle,&unlock)!=0 || (unlock.ok() && sync_wait(unlock.get(),3000)!=0))return HWC3::Error::NoResources;
    if(!output_.CommitCpu(pixels.data(),int(w),int(h),int(w)))return HWC3::Error::NoResources;
    // Source read is complete and the real Wayland callback arrived. There is
    // no kernel present fence: leave it absent, as the original frontend's
    // addPresentFence already does for invalid FDs. Timing/VTS remains OPEN.
    present->reset();releases->clear();return HWC3::Error::None;
}
}
