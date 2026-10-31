// Test the real original Service::Start failure callback, not a fake success.
#include "init.h"
#include "builtins.h"
#include "linux-shutdown-sink.h"
#include <android-base/logging.h>
#include <selinux/selinux.h>
#include <sys/socket.h>
#include <sys/wait.h>
#include <cstdlib>
#include <cstdio>
#include <cstring>
#define REQUIRE(x) do { if(!(x)){std::fprintf(stderr,"FAILED %s errno=%d\n",#x,errno);return 1;} } while(0)
int main(int argc,char** argv) {
    android::base::InitLogging(argv,android::base::StderrLogger);
    REQUIRE(argc==2 && is_selinux_enabled()==0);
    const char* value=getenv("ARCHTV_NATIVE_CONTROL_FD");REQUIRE(value);
    char* end=nullptr;long fd=strtol(value,&end,10);REQUIRE(end && !*end && fd>=3 && fd<=INT_MAX);
    unsetenv("ARCHTV_NATIVE_CONTROL_FD");
    using namespace android::init;
    ActionManager actions;ServiceList services;
    Action::set_function_map(&GetBuiltinFunctionMap());auto parser=CreateParser(actions,services);
    REQUIRE(parser.ParseConfigFile("/data/profiles/service.rc").ok() && parser.parse_error_count()==0);
    auto* service=services.FindService("audit.failure");REQUIRE(service && service->seclabel().empty());
    REQUIRE(trigger_shutdown==nullptr);
    std::string frame;
    {
        archtv::aosp::LinuxShutdownSink sink;REQUIRE(sink.Install().ok());
        archtv::aosp::LinuxShutdownSink other;REQUIRE(!other.Install().ok());
        REQUIRE(!sink.failed() && sink.Frame().empty());
        auto started=service->Start();REQUIRE(!started.ok());
        REQUIRE(started.error().message()=="Could not get security context");
        REQUIRE(sink.failed() && service->pid()==0 && !service->IsRunning());
        int status=0;REQUIRE(waitpid(-1,&status,WNOHANG)==-1 && errno==ECHILD);
        frame=sink.Frame();
        if(std::strcmp(argv[1],"normal")==0) REQUIRE(frame=="ARCHTV_NATIVE_V1 FAILED_SHUTDOWN 7265626f6f74\n");
        else REQUIRE(std::strcmp(argv[1],"oversize")==0 && frame=="ARCHTV_NATIVE_V1 FAILED_SHUTDOWN_OVERSIZE\n");
        std::fprintf(stderr,"ORIGINAL_START_FAILED: %s; Linux captured request, no child\n",started.error().message().c_str());
    }
    REQUIRE(trigger_shutdown==nullptr);
    REQUIRE(send(static_cast<int>(fd),frame.data(),frame.size(),MSG_NOSIGNAL)==static_cast<ssize_t>(frame.size()));
    return 69;
}
