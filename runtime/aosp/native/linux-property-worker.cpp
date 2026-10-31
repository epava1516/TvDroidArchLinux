// Linux-supervised Bionic component. Does not dispatch Android init or certify APK readiness.
#include "init.h"
#include "linux-child-reaper.h"
#include "linux-shutdown-sink.h"
#include "linux-mc1-cohort.h"
#include "property_service.h"
#include "selabel.h"
#include "proto_utils.h"
#include "system/core/init/property_service.pb.h"
#include <android-base/logging.h>
#include <android-base/unique_fd.h>
#include <selinux/selinux.h>
#include <sys/socket.h>
#include <sys/stat.h>
#include <sys/system_properties.h>
#include <fcntl.h>
#include <unistd.h>
#include <cerrno>
#include <climits>
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <chrono>
#include <string>
using namespace android::init;
using android::base::unique_fd;
static bool send_status(int fd,const char* status) {
    size_t size=std::strlen(status);
    return send(fd,status,size,MSG_NOSIGNAL|MSG_DONTWAIT)==static_cast<ssize_t>(size);
}
static bool close_actions(Epoll& epoll) {
    auto stopped=StopLinuxPropertyActions(&epoll);
    if(!stopped.ok() && ActionManager::GetInstance().HasMoreCommands()) {
        for(int i=0;i<1024 && ActionManager::GetInstance().HasMoreCommands();++i) {
            auto result=PollLinuxPropertyActions(&epoll,std::chrono::milliseconds(0));
            if(!result.ok())return false;
        }
        stopped=StopLinuxPropertyActions(&epoll);
    }
    if(!stopped.ok())std::fprintf(stderr,"PROPERTY_WORKER_CLOSE_FAILED %s\n",stopped.error().message().c_str());
    return stopped.ok();
}
int main(int argc,char** argv) {
    android::base::InitLogging(argv,android::base::StderrLogger);
    bool graphics=argc==2 && std::strcmp(argv[1],"--mc3-graphics-integration")==0;
    bool hardware=graphics || (argc==2 && std::strcmp(argv[1],"--mc1-hardware-integration")==0);
    bool mc1=hardware || (argc==2 && std::strcmp(argv[1],"--mc1-integration")==0);
    bool mac_integration=mc1 || (argc==2 && std::strcmp(argv[1],"--mac-integration")==0);
    bool diagnostic=mac_integration || (argc==2 && std::strcmp(argv[1],"--diagnostic")==0);
    if(argc!=1 && !diagnostic)return 64;
    const char* inherited=getenv("ARCHTV_NATIVE_CONTROL_FD");
    if(!inherited || !*inherited)return 64;
    char* end=nullptr;errno=0;long parsed=std::strtol(inherited,&end,10);
    if(errno || !end || *end || parsed<3 || parsed>INT_MAX)return 64;
    unique_fd control(static_cast<int>(parsed));unsetenv("ARCHTV_NATIVE_CONTROL_FD");
    int type=0;socklen_t size=sizeof(type);ucred peer{};socklen_t peer_size=sizeof(peer);
    if(getsockopt(control.get(),SOL_SOCKET,SO_TYPE,&type,&size)!=0 || type!=SOCK_STREAM ||
       getsockopt(control.get(),SOL_SOCKET,SO_PEERCRED,&peer,&peer_size)!=0 || peer.uid!=getuid())return 77;
    int flags=fcntl(control.get(),F_GETFL);
    if(flags<0 || fcntl(control.get(),F_SETFL,flags|O_NONBLOCK)<0 || fcntl(control.get(),F_SETFD,FD_CLOEXEC)<0)return 74;
    Epoll epoll;
    if(!epoll.Open().ok())return 70;
    archtv::aosp::LinuxChildReaper children(epoll);
    if(!children.Attach().ok())return 70; // Before SELinux/AVC/property calls that may start threads.
    const int launch_enforcing=security_getenforce();
    if(!diagnostic || mac_integration) {
        char* context=nullptr;
        int enforcing=launch_enforcing;
        bool valid=is_selinux_enabled()==1 && enforcing>=0 &&
            (enforcing==1 || mac_integration) && getcon(&context)==0 &&
            context && std::strcmp(context,"u:r:init:s0")==0;
        for(const char* name: {"process","binder","property_service","service_manager"})
            valid=valid && string_to_security_class(name)!=0;
        std::fprintf(stderr,"PROPERTY_WORKER_IDENTITY observed=%s enforcing=%d mc1=%d\n",context?context:"not-observed",enforcing,mc1);
        if(context)freecon(context);
        if(!valid) { std::fprintf(stderr,"PROPERTY_WORKER_REFUSED: loaded policy classes and u:r:init:s0 required (normal mode also requires enforcing); no startup acknowledgment\n");return 78; }
    }
    if(mkdir("/data/property",0700)!=0 && errno!=EEXIST)return 74;
    struct stat property_dir{};
    if(lstat("/data/property",&property_dir)!=0 || !S_ISDIR(property_dir.st_mode) || property_dir.st_uid!=getuid() || (property_dir.st_mode&0077))return 77;
    archtv::aosp::LinuxShutdownSink shutdown;
    if(!shutdown.Install().ok())return 70;
    // Same original initialization used before services in SecondStageMain,
    // without dispatching Android boot. util::CreateSocket must have its handle.
    SelabelInitialize();
    std::string socket_context;
    if((!diagnostic || mac_integration) &&
       (!SelabelLookupFileContext("/dev/socket/property_service",S_IFSOCK,&socket_context) ||
        socket_context!="u:object_r:property_socket:s0"))return 78;
    PropertyInit(); // SIGCHLD is attached before any original AVC/property threads.
    auto setup=StartLinuxPropertyActions(&epoll);
    if(!setup.ok())return 70;
    bool stop=false,peer_gone=false,invalid=false;std::string input;
    archtv::aosp::LinuxMc1Cohort cohort(stop,launch_enforcing,hardware,graphics);
    auto tick=[&]{return PollLinuxPropertyActions(&epoll,std::chrono::milliseconds(50)).ok() && children.healthy() && !shutdown.failed();};
    auto registered=epoll.RegisterHandler(control.get(),[&]{
        char bytes[64];
        for(int turn=0;turn<4;++turn) {
            ssize_t n=read(control.get(),bytes,sizeof(bytes));
            if(n==0){peer_gone=true;stop=true;return;}
            if(n<0){if(errno==EINTR)continue;if(errno==EAGAIN)return;invalid=true;stop=true;return;}
            input.append(bytes,n);
            if(input.size()>96){invalid=true;stop=true;return;}
            auto newline=input.find('\n');
            if(newline!=std::string::npos) {
                if(input.substr(0,newline+1)!="ARCHTV_NATIVE_V1 STOP\n" || newline+1!=input.size())invalid=true;
                stop=true;return;
            }
        }
    });
    if(!registered.ok()){close_actions(epoll);return 70;}
    int raw_init=-1;StartPropertyService(&raw_init);unique_fd init_socket(raw_init);
    InitMessage load;load.set_load_persistent_properties(true);
    bool healthy=SendMessage(init_socket.get(),load).ok();
    auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(5);
    char phase[PROP_VALUE_MAX]={};
    while(healthy && !stop && std::chrono::steady_clock::now()<deadline) {
        auto polled=PollLinuxPropertyActions(&epoll,std::chrono::milliseconds(50));healthy=polled.ok() && children.healthy() && !shutdown.failed();
        if(__system_property_get("ro.persistent_properties.ready",phase)>0 && std::strcmp(phase,"true")==0)break;
    }
    healthy=healthy && !stop && std::strcmp(phase,"true")==0;
    if(healthy && mc1) {
        for(const char* path:{"/dev/socket/property_service","/dev/socket/property_service_for_system"}) {
            char* label=nullptr;
            bool labelled=getfilecon(path,&label)>=0 && label &&
                std::strcmp(label,"u:object_r:property_socket:s0")==0;
            std::fprintf(stderr,"MC1_PROPERTY_SOCKET_LABEL path=%s actual=%s\n",path,label?label:"unknown");
            if(label)freecon(label);
            healthy=healthy && labelled;
        }
    }
    if(healthy && mc1) {
        auto admitted=cohort.Start(tick);
        if(!admitted.ok())std::fprintf(stderr,"MC1_FAILED %s\n",admitted.error().message().c_str());
        healthy=admitted.ok();
    }
    if(healthy)healthy=send_status(control.get(),diagnostic?"ARCHTV_NATIVE_V1 DIAGNOSTIC_STARTED\n":"ARCHTV_NATIVE_V1 STARTED\n");
    while(healthy && !stop)healthy=PollLinuxPropertyActions(&epoll,std::chrono::milliseconds(250)).ok() && children.healthy() && !shutdown.failed() && (!mc1 || cohort.healthy());
    auto cohort_closed=cohort.Close(tick);
    if(!cohort_closed.ok())std::fprintf(stderr,"MC1_CLOSE_FAILED %s\n",cohort_closed.error().message().c_str());
    bool closed=close_actions(epoll) && cohort_closed.ok();init_socket.reset();
    auto unregistered=epoll.UnregisterHandler(control.get());
    auto children_closed=children.Close();
    if(shutdown.failed()) {
        auto frame=shutdown.Frame();
        if(!send_status(control.get(),frame.c_str()))return 74;
        return 69; // Failure event, never STOPPED or successful component exit.
    }
    if(!healthy || !closed || !unregistered.ok() || !children_closed.ok() || peer_gone || invalid)return 1;
    if(!send_status(control.get(),"ARCHTV_NATIVE_V1 STOPPED\n"))return 74;
    std::fprintf(stderr,"PROPERTY_WORKER_STOPPED: original actions drained and workers joined; not APK readiness\n");
    return 0;
}
