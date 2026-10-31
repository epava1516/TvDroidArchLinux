// Experimental integration client using original libui and generated AIDL.
// No replacement allocator, mapper, service answers, or APK readiness.
#include <aidl/android/hardware/graphics/allocator/IAllocator.h>
#include <aidl/android/hardware/graphics/composer3/IComposer.h>
#include <aidl/android/hardware/graphics/composer3/PowerMode.h>
#include <aidlcommonsupport/NativeHandle.h>
#include <android/binder_manager.h>
#include <android/binder_process.h>
#include <ui/GraphicBuffer.h>
#include <chrono>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <fcntl.h>
#include <thread>
#include <unistd.h>

namespace c3 = aidl::android::hardware::graphics::composer3;
namespace alloc = aidl::android::hardware::graphics::allocator;

static bool status(const char* stage,const ndk::ScopedAStatus& value) {
    if(value.isOk())return true;
    std::fprintf(stderr,"MC3_CLIENT_ERROR stage=%s status=%s\n",stage,value.getDescription().c_str());
    return false;
}

static ndk::SpAIBinder lookup(const char* name) {
    const auto end=std::chrono::steady_clock::now()+std::chrono::seconds(3);
    do {
        ndk::SpAIBinder binder(AServiceManager_checkService(name));
        if(binder.get())return binder;
        std::this_thread::sleep_for(std::chrono::milliseconds(20));
    } while(std::chrono::steady_clock::now()<end);
    std::fprintf(stderr,"MC3_CLIENT_MISSING_SERVICE %s\n",name);
    return {};
}

int main() {
    int report=open("/data/misc/surfaceflinger/archtv-integration.txt",
                    O_WRONLY|O_CREAT|O_EXCL|O_NOFOLLOW|O_CLOEXEC,0600);
    if(report<0)return 74;
    if(dup2(report,STDOUT_FILENO)<0 || dup2(report,STDERR_FILENO)<0)return 74;
    close(report);
    setbuf(stdout,nullptr);
    std::printf("MC3_CLIENT_BEGIN uid=%u gid=%u NOT_SURFACEFLINGER_OR_APK\n",getuid(),getgid());
    if(getuid()!=1000 || getgid()!=1003)return 77;
    FILE* identity=fopen("/proc/self/attr/current","r");char context[256]={};
    if(!identity || !fgets(context,sizeof(context),identity))return 77;
    fclose(identity);context[strcspn(context,"\n")]=0;
    std::printf("MC3_CLIENT_ACTUAL_SID %s\n",context);
    if(std::strcmp(context,"u:r:surfaceflinger:s0"))return 77;
    FILE* process=fopen("/proc/self/status","r");char line[512];int observed=0;
    if(!process)return 77;
    while(fgets(line,sizeof(line),process)) {
        if(!strncmp(line,"CapEff:",7) || !strncmp(line,"CapPrm:",7) ||
           !strncmp(line,"CapInh:",7) || !strncmp(line,"CapAmb:",7)) {
            std::printf("MC3_CLIENT_STATUS %s",line);
            if(strtoull(line+7,nullptr,16)!=0)return 77;
            ++observed;
        }
        if(!strncmp(line,"NoNewPrivs:",11)) {
            std::printf("MC3_CLIENT_STATUS %s",line);
            if(strtol(line+11,nullptr,10)!=1)return 77;
            ++observed;
        }
    }
    fclose(process);if(observed!=5)return 77;
    ABinderProcess_setThreadPoolMaxThreadCount(2);
    ABinderProcess_startThreadPool();
    auto allocator=alloc::IAllocator::fromBinder(lookup("android.hardware.graphics.allocator.IAllocator/default"));
    if(!allocator)return 1;
    int32_t allocator_version=0;std::string allocator_hash;
    if(!status("allocator-version",allocator->getInterfaceVersion(&allocator_version)) ||
       !status("allocator-hash",allocator->getInterfaceHash(&allocator_hash)))return 1;
    if(allocator_version!=2 || allocator_hash!="9499fec09c544e9de5be3c87125721600f8ade66")return 1;
    std::printf("MC3_ALLOCATOR_ORIGINAL_INTERFACE version=%d hash=%s\n",allocator_version,allocator_hash.c_str());
    auto composer=c3::IComposer::fromBinder(lookup("android.hardware.graphics.composer3.IComposer/default"));
    if(!composer)return 1;
    std::shared_ptr<c3::IComposerClient> client;
    if(!status("create-client",composer->createClient(&client)) || !client)return 1;
    std::vector<c3::DisplayConfiguration> configs;
    if(!status("display-configurations",client->getDisplayConfigurations(0,0,&configs)) || configs.size()!=1)return 1;
    const auto& config=configs.front();
    if(config.width<=0 || config.height<=0 || config.width>8192 || config.height>8192)return 1;
    std::printf("MC3_REAL_DISPLAY config=%d width=%d height=%d\n",config.configId,config.width,config.height);
    const uint64_t usage=android::GraphicBuffer::USAGE_SW_READ_OFTEN |
                         android::GraphicBuffer::USAGE_SW_WRITE_OFTEN |
                         android::GraphicBuffer::USAGE_HW_COMPOSER;
    auto buffer=android::sp<android::GraphicBuffer>::make(config.width,config.height,
        android::PIXEL_FORMAT_RGBA_8888,1,usage,"ArchTV original-graphics integration");
    if(buffer->initCheck()!=android::NO_ERROR || !buffer->handle) {
        std::fprintf(stderr,"MC3_REAL_ALLOCATION_FAILED status=%d\n",buffer->initCheck());return 1;
    }
    void* pixels=nullptr;
    if(buffer->lock(android::GraphicBuffer::USAGE_SW_WRITE_OFTEN,&pixels)!=android::NO_ERROR || !pixels)return 1;
    auto* data=static_cast<uint32_t*>(pixels);
    for(int y=0;y<config.height;++y)for(int x=0;x<config.width;++x) {
        bool right=x>=config.width/2,bottom=y>=config.height/2;
        data[static_cast<size_t>(y)*buffer->getStride()+x]=bottom?(right?0xffffffff:0xffff0000):(right?0xff00ff00:0xff0000ff);
    }
    if(buffer->unlock()!=android::NO_ERROR)return 1;
    std::printf("MC3_REAL_BUFFER_WRITTEN stride=%u fds=%d\n",buffer->getStride(),buffer->handle->numFds);
    if(!status("slots",client->setClientTargetSlotCount(0,1)) ||
       !status("power-on",client->setPowerMode(0,c3::PowerMode::ON)))return 1;
    c3::DisplayCommand command;command.display=0;
    command.clientTarget.emplace();command.clientTarget->buffer.slot=0;
    command.clientTarget->buffer.handle=android::dupToAidl(buffer->handle);
    command.validateDisplay=true;command.acceptDisplayChanges=true;command.presentDisplay=true;
    std::vector<c3::DisplayCommand> commands;commands.emplace_back(std::move(command));
    std::vector<c3::CommandResultPayload> results;
    if(!status("execute",client->executeCommands(commands,&results)))return 1;
    for(const auto& result:results) {
        std::printf("MC3_COMMAND_RESULT %s\n",result.toString().c_str());
        if(result.getTag()==c3::CommandResultPayload::Tag::error)return 1;
    }
    std::printf("MC3_COMMANDS_ACCEPTED physical_timing_not_proven NOT_APK_READINESS\n");
    // Keep the actual presented target alive during the independent Linux
    // screenshot. This bounded observation window proves no fence timing.
    std::this_thread::sleep_for(std::chrono::seconds(3));
    client.reset();buffer.clear();composer.reset();allocator.reset();
    return 0;
}
