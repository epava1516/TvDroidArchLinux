#pragma once
// One bounded MC1 functional experiment, using original service lifecycle code.
// No boot scripts, synthesized readiness, control backend or APK acceptance.
#include "init.h"
#include "builtins.h"
#include "service.h"
#include "service_list.h"
#include "parser.h"
#include "action.h"
#include "action_manager.h"
#include <android-base/file.h>
#include <android-base/result.h>
#include <selinux/selinux.h>
#include <sys/stat.h>
#include <sys/system_properties.h>
#include <signal.h>
#include <cstdio>
#include <cerrno>
#include <vector>
#include <chrono>
#include <functional>
#include <string>

namespace archtv::aosp {
class LinuxMc1Cohort {
 public:
    using Tick = std::function<bool()>;
    LinuxMc1Cohort(const bool& stop,int expected_mode) : stop_(stop),expected_mode_(expected_mode) {}
    android::base::Result<void> Start(const Tick& tick) {
        using namespace android::init;
        auto& services=ServiceList::GetInstance();
        if(services.size()!=0) return android::base::Error()<<"MC1 requires a fresh service list";
        active_=true;
        Action::set_function_map(&GetBuiltinFunctionMap());
        auto parser=CreateParser(ActionManager::GetInstance(),services);
        auto parsed=parser.ParseConfigFile("/system/etc/init/servicemanager.rc");
        if(!parsed.ok() || parser.parse_error_count()!=0 || services.size()!=1)
            return android::base::Error()<<"MC1 original manager profile rejected";
        manager_=services.FindService("servicemanager");
        if(!manager_ || manager_->args()!=std::vector<std::string>{"/system/bin/servicemanager"})
            return android::base::Error()<<"MC1 unexpected manager executable";
        char ready[PROP_VALUE_MAX]={};
        if(__system_property_get("servicemanager.ready",ready)>0 && std::string(ready)=="true")
            return android::base::Error()<<"MC1 refuses stale pre-start manager readiness";
        struct stat previous{};
        if(lstat("/data/local/tmp/archtv-mc1/service-list.txt",&previous)==0 || errno!=ENOENT)
            return android::base::Error()<<"MC1 requires fresh original client output";
        manager_->AddReapCallback([this](const siginfo_t& info) {
            std::fprintf(stderr,"MC1_MANAGER_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
            if(!closing_) manager_failed_=true;
        });
        if(auto result=manager_->Start();!result.ok()) return result;
        std::fprintf(stderr,"MC1_MANAGER_STARTED pid=%d uid=%u gid=%u\n",manager_->pid(),manager_->uid(),manager_->gid());
        auto waiting=Wait(tick,[&]{
            char value[PROP_VALUE_MAX]={};
            return __system_property_get("servicemanager.ready",value)>0 && std::string(value)=="true";
        });
        if(!waiting.ok()) return waiting;
        // External Linux diagnostic observes identity through original getpidcon.
        // Android init's original neverallow forbids CAP_SYS_PTRACE; do not
        // weaken it merely to inspect a different-UID child's /proc attrs.
        // Original shell/CLI, explicit original shell context and UID. The shell
        // writes its real output to fresh private shell_data_file storage.
        auto client=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","shell","shell","--",
            "/system/bin/sh","-c","/system/bin/service list > /data/local/tmp/archtv-mc1/service-list.txt 2>&1"});
        if(!client.ok()) return client.error();
        auto* process=client->get();
        process->AddReapCallback([this](const siginfo_t& info) {
            client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;
            std::fprintf(stderr,"MC1_CLIENT_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
        });
        services.AddService(std::move(*client));
        if(auto result=process->ExecStart();!result.ok()) return result;
        if(auto result=Wait(tick,[this]{return client_done_;});!result.ok())return result;
        if(!client_ok_)return android::base::Error()<<"MC1 original client failed";
        const char* path="/data/local/tmp/archtv-mc1/service-list.txt";
        struct stat info{};
        if(lstat(path,&info)!=0 || !S_ISREG(info.st_mode) || info.st_uid!=2000 || info.st_gid!=2000 ||
            (info.st_mode&0777)!=0600 || info.st_size<1 || info.st_size>65536)
            return android::base::Error()<<"MC1 missing or excessive original client output";
        char* context=nullptr;
        if(getfilecon(path,&context)<0)return android::base::Error()<<"MC1 missing real client output label";
        bool label_ok=context && std::string(context)=="u:object_r:shell_data_file:s0";
        freecon(context);
        if(!label_ok)return android::base::Error()<<"MC1 unexpected real client output label";
        int observed_mode=security_getenforce();
        if(observed_mode!=expected_mode_)return android::base::Error()<<"MC1 security mode changed during startup";
        std::fprintf(stderr,"MC1_ORIGINAL_CLIENT_EXIT0_REQUIRES_EXTERNAL_VERIFICATION enforcing=%d\n",observed_mode);
        return {};
    }
    bool healthy() const { return !manager_failed_ && (!manager_ || manager_->IsRunning()); }
    android::base::Result<void> Close(const Tick& tick) {
        using namespace android::init;
        if(!active_) return {};
        closing_=true;
        auto& services=ServiceList::GetInstance();
        for(const auto& service:services)if(service->IsRunning())service->Stop();
        const auto end=std::chrono::steady_clock::now()+std::chrono::seconds(3);
        for(;;) {
            bool running=false;
            for(const auto& service:services)running=running || service->IsRunning();
            if(!running)break;
            if(std::chrono::steady_clock::now()>=end || !tick())
                return android::base::Error()<<"MC1 services not collected during close";
        }
        manager_=nullptr;
        services.RemoveServiceIf([](const auto& service){return !service->IsRunning();});
        active_=false;
        int observed_mode=security_getenforce();
        std::fprintf(stderr,"MC1_CLOSE_OBSERVED enforcing=%d expected=%d\n",observed_mode,expected_mode_);
        if(observed_mode!=expected_mode_)return android::base::Error()<<"MC1 security mode changed during close";
        return {};
    }
 private:
    android::base::Result<void> Wait(const Tick& tick,const std::function<bool()>& done) {
        const auto end=std::chrono::steady_clock::now()+std::chrono::seconds(5);
        for(;;) {
            if(stop_ || !healthy())return android::base::Error()<<"MC1 stopped or manager exited";
            if(done())return {};
            if(std::chrono::steady_clock::now()>=end || !tick())
                return android::base::Error()<<"MC1 original progress deadline/error";
        }
    }
    const bool& stop_;
    const int expected_mode_;
    android::init::Service* manager_=nullptr;
    bool active_=false,closing_=false,manager_failed_=false,client_done_=false,client_ok_=false;
};
}
