// Controlled negative integration probe, not a production launcher.
#include "init.h"
#include "builtins.h"
#include "linux-child-reaper.h"
#include <android-base/logging.h>
#include <selinux/selinux.h>
#include <sys/wait.h>
#include <dirent.h>
#include <cstdio>
#include <cstring>
#define REQUIRE(x) do { if (!(x)) { std::fprintf(stderr,"FAILED %s errno=%d\n",#x,errno); return 1; } } while (0)
static size_t fds() {
    DIR* d=opendir("/proc/self/fd"); if (!d) return 0;
    size_t n=0;
    while (auto* e=readdir(d)) if (std::strcmp(e->d_name,".") && std::strcmp(e->d_name,"..")) ++n;
    closedir(d); return n;
}
int main(int,char** argv) {
    android::base::InitLogging(argv,android::base::StderrLogger);
    // Deliberately restricted to the reviewed failure path, before any fork.
    REQUIRE(is_selinux_enabled()==0);
    using namespace android::init;
    ActionManager actions;
    auto& services=ServiceList::GetInstance();
    Action::set_function_map(&GetBuiltinFunctionMap());
    auto parser=CreateParser(actions,services);
    REQUIRE(parser.ParseConfigFile("/system/etc/init/servicemanager.rc").ok());
    REQUIRE(parser.parse_error_count()==0 && services.size()==1);
    auto* service=services.FindService("servicemanager");
    REQUIRE(service && service->args().at(0)=="/system/bin/servicemanager");
    REQUIRE(service->seclabel().empty() && service->pid()==0 && !service->IsRunning());
    size_t baseline=fds();
    {
        Epoll loop; REQUIRE(loop.Open().ok());
        archtv::aosp::LinuxChildReaper children(loop); REQUIRE(children.Attach().ok());
        size_t before_start=fds();
        auto result=service->Start();
        REQUIRE(!result.ok());
        std::printf("ORIGINAL_START_ERROR %s\n",result.error().message().c_str());
        REQUIRE(result.error().message()=="Could not get security context");
        REQUIRE(service->pid()==0 && !service->IsRunning());
        int status=0; REQUIRE(waitpid(-1,&status,WNOHANG)==-1 && errno==ECHILD);
        REQUIRE(fds()==before_start);
        std::puts("START_REJECTED_PID_ZERO_NOT_RUNNING_NO_CHILD_NO_FIFO_LEAK");
        REQUIRE(children.Close().ok());
    }
    REQUIRE(fds()==baseline);
    std::printf("CLOSED_FDS_BEFORE=%zu_AFTER=%zu NOT_SERVICE_READINESS\n",baseline,fds());
    return 0;
}
