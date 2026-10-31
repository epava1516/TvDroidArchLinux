// Linux-supervised Bionic component. Does not dispatch Android init or certify APK readiness.
#include "init.h"
#include "property_service.h"
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
    bool diagnostic=argc==2 && std::strcmp(argv[1],"--diagnostic")==0;
    if(argc!=1 && !diagnostic)return 64;
    const char* inherited=getenv("ARCHTV_NATIVE_CONTROL_FD");
    if(!inherited || !*inherited)return 64;
    char* end=nullptr;errno=0;long parsed=std::strtol(inherited,&end,10);
    if(errno || !end || *end || parsed<3 || parsed>INT_MAX)return 64;
    unique_fd control(static_cast<int>(parsed));unsetenv("ARCHTV_NATIVE_CONTROL_FD");
    int type=0;socklen_t size=sizeof(type);ucred peer{};socklen_t peer_size=sizeof(peer);
    if(getsockopt(control,SOL_SOCKET,SO_TYPE,&type,&size)!=0 || type!=SOCK_STREAM ||
       getsockopt(control,SOL_SOCKET,SO_PEERCRED,&peer,&peer_size)!=0 || peer.uid!=getuid())return 77;
    int flags=fcntl(control,F_GETFL);
    if(flags<0 || fcntl(control,F_SETFL,flags|O_NONBLOCK)<0 || fcntl(control,F_SETFD,FD_CLOEXEC)<0)return 74;
    if(!diagnostic) {
        char* context=nullptr;
        bool valid=is_selinux_enabled()>0 && security_getenforce()==1 && getcon(&context)==0;
        if(context)freecon(context);
        if(!valid) { std::fprintf(stderr,"PROPERTY_WORKER_REFUSED: active enforcing SELinux/context required; no startup acknowledgment\n");return 78; }
    }
    if(mkdir("/data/property",0700)!=0 && errno!=EEXIST)return 74;
    struct stat property_dir{};
    if(lstat("/data/property",&property_dir)!=0 || !S_ISDIR(property_dir.st_mode) || property_dir.st_uid!=getuid() || (property_dir.st_mode&0077))return 77;
    PropertyInit();
    Epoll epoll;
    auto setup=StartLinuxPropertyActions(&epoll);
    if(!setup.ok())return 70;
    bool stop=false,peer_gone=false,invalid=false;std::string input;
    auto registered=epoll.RegisterHandler(control,[&]{
        char bytes[64];
        for(int turn=0;turn<4;++turn) {
            ssize_t n=read(control,bytes,sizeof(bytes));
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
    bool healthy=SendMessage(init_socket,load).ok();
    auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(5);
    char phase[PROP_VALUE_MAX]={};
    while(healthy && !stop && std::chrono::steady_clock::now()<deadline) {
        auto polled=PollLinuxPropertyActions(&epoll,std::chrono::milliseconds(50));healthy=polled.ok();
        if(__system_property_get("ro.persistent_properties.ready",phase)>0 && std::strcmp(phase,"true")==0)break;
    }
    healthy=healthy && !stop && std::strcmp(phase,"true")==0;
    if(healthy)healthy=send_status(control,diagnostic?"ARCHTV_NATIVE_V1 DIAGNOSTIC_STARTED\n":"ARCHTV_NATIVE_V1 STARTED\n");
    while(healthy && !stop)healthy=PollLinuxPropertyActions(&epoll,std::chrono::milliseconds(250)).ok();
    bool closed=close_actions(epoll);init_socket.reset();
    auto unregistered=epoll.UnregisterHandler(control);
    if(!healthy || !closed || !unregistered.ok() || peer_gone || invalid)return 1;
    if(!send_status(control,"ARCHTV_NATIVE_V1 STOPPED\n"))return 74;
    std::fprintf(stderr,"PROPERTY_WORKER_STOPPED: original actions drained and workers joined; not APK readiness\n");
    return 0;
}
