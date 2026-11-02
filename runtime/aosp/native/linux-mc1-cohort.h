#pragma once
// One bounded MC1 functional experiment, using original service lifecycle code.
// No boot scripts, synthesized readiness, control backend or APK acceptance.
#include "init.h"
#include "builtins.h"
#include "service.h"
#include "service_list.h"
#include "parser.h"
#include "mount_namespace.h"
#include "util.h"
#include <sys/mount.h>
#include "action.h"
#include "action_manager.h"
#include <android-base/file.h>
#include <android-base/properties.h>
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
#include <sstream>

namespace archtv::aosp {
class LinuxMc1Cohort {
 public:
    using Tick = std::function<bool()>;
    LinuxMc1Cohort(const bool& stop,int expected_mode,bool hardware=false,bool graphics=false,bool surfaceflinger=false,bool selected=false,bool apex=false)
        : stop_(stop),expected_mode_(expected_mode),hardware_requested_(hardware),graphics_requested_(graphics),surfaceflinger_requested_(surfaceflinger),selected_requested_(selected),apex_requested_(apex) {}
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
        if(apex_requested_ && selected_requested_) {
            if(auto result=StartHardware(tick,true);!result.ok())return result;
            if(auto result=StartVold(tick);!result.ok())return result;
        }
        if(apex_requested_) { if(auto result=StartApex(tick);!result.ok())return result; }
        if(hardware_requested_)return apex_requested_ && selected_requested_ ? StartGraphics(tick) : StartHardware(tick);
        return {};
    }
    bool vold_cancelled() const { return vold_cancelled_; }
    bool apex_cancelled() const { return apex_cancelled_; }
    bool healthy() const { return !manager_failed_ && (!netd_ || netd_->IsRunning()) && (!statsd_ || statsd_->IsRunning()) && (!health_ || health_->IsRunning()) && (!zygote_ || zygote_->IsRunning()) && (!vold_ || vold_->IsRunning()) && (!manager_ || manager_->IsRunning()) && (!hardware_ || hardware_->IsRunning()) && (!allocator_ || allocator_->IsRunning()) && (!composer_ || composer_->IsRunning()) && (!surfaceflinger_ || surfaceflinger_->IsRunning()) && (!bootanimation_started_ || (bootanimation_ && bootanimation_->IsRunning())) && (!selected_ || selected_->IsRunning()) && (!suspend_ || suspend_->IsRunning()) && (!installd_ || installd_->IsRunning()) && (!apexd_ || apexd_->IsRunning()); }
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
        hardware_=nullptr;
        allocator_=nullptr;
        composer_=nullptr;
        surfaceflinger_=nullptr;
        bootanimation_=nullptr;
        bootanimation_started_=false;
        netd_=nullptr;
        statsd_=nullptr;
        health_=nullptr;
        selected_=nullptr;
        suspend_=nullptr;
        installd_=nullptr;
        apexd_=nullptr;
        services.RemoveServiceIf([](const auto& service){return !service->IsRunning();});
        active_=false;
        int observed_mode=security_getenforce();
        std::fprintf(stderr,"MC1_CLOSE_OBSERVED enforcing=%d expected=%d\n",observed_mode,expected_mode_);
        if(observed_mode!=expected_mode_)return android::base::Error()<<"MC1 security mode changed during close";
        return {};
    }
 private:
    android::base::Result<void> StartVold(const Tick& tick) {
        using namespace android::init;
        auto& services=ServiceList::GetInstance();
        auto parser=CreateParser(ActionManager::GetInstance(),services);
        auto parsed=parser.ParseConfigFile("/system/etc/init/vold.rc");
        if(!parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original vold RC rejected";
        vold_=services.FindService("vold");
        if(!vold_ || vold_->args().empty() || vold_->args().front()!="/system/bin/vold")return android::base::Error()<<"Original vold executable rejected";
        vold_->AddReapCallback([this](const siginfo_t& info){
            std::fprintf(stderr,"STORAGE_VOLD_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
            if(closing_ && stop_ && info.si_code==CLD_KILLED && info.si_status==SIGKILL)vold_cancelled_=true;
            if(!closing_)manager_failed_=true;
        });
        if(auto started=vold_->Start();!started.ok())return started;
        std::fprintf(stderr,"SELECTED_VOLD_STARTED pid=%d NOT_REGISTERED\n",vold_->pid());
        return {};
    }
    android::base::Result<void> StartApex(const Tick& tick) {
        using namespace android::init;
        auto& services=ServiceList::GetInstance();
        if(!android::base::GetProperty("apexd.status","").empty())
            return android::base::Error()<<"Refusing stale APEX status";
        auto parser=CreateParser(ActionManager::GetInstance(),services);
        auto parsed=parser.ParseConfigFile("/system/etc/init/apexd.rc");
        if(!parsed.ok() || parser.parse_error_count()!=0)
            return android::base::Error()<<"Original APEX service profile rejected";
        apexd_=services.FindService("apexd");
        if(!apexd_ || apexd_->args()!=std::vector<std::string>{"/system/bin/apexd"})
            return android::base::Error()<<"Unexpected original apexd executable";
        apexd_->AddReapCallback([this](const siginfo_t& info) {
            std::fprintf(stderr,"APEX_DAEMON_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
            if(closing_ && stop_ && info.si_code==CLD_KILLED && info.si_status==SIGKILL)apex_cancelled_=true;
            if(!closing_)manager_failed_=true;
        });
        if(auto result=apexd_->Start();!result.ok())return result;
        std::fprintf(stderr,"APEX_DAEMON_STARTED pid=%d NOT_REGISTERED\n",apexd_->pid());
        if(auto result=Wait(tick,[]{return android::base::GetProperty("apexd.status","")=="activated";},100);!result.ok())return result;
        // Original normal activation followed by original DE snapshot phase.
        // Status and mount inventory are written exclusively by original apexd.
        auto* snapshot=services.FindService("apexd-snapshotde");
        if(!snapshot || snapshot->args()!=std::vector<std::string>{"/system/bin/apexd","--snapshotde"})
            return android::base::Error()<<"Unexpected original APEX snapshot executable";
        client_done_=false;client_ok_=false;
        snapshot->AddReapCallback([this](const siginfo_t& info) {
            client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;
            std::fprintf(stderr,"APEX_SNAPSHOT_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
        });
        if(auto result=snapshot->Start();!result.ok())return result;
        std::fprintf(stderr,"APEX_SNAPSHOT_STARTED pid=%d NOT_READY\n",snapshot->pid());
        if(auto result=Wait(tick,[this]{return client_done_;},25);!result.ok())return result;
        if(!client_ok_ || android::base::GetProperty("apexd.status","")!="ready")
            return android::base::Error()<<"Original snapshot phase did not publish ready";
        client_done_=false;client_ok_=false;
        auto client=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","root","root","--",
            "/system/bin/sh","-c",
            "umask 077; /system/bin/service check apexservice > /data/local/tmp/archtv-mc1/apex-query.txt 2>&1; "
            "/system/bin/cmd apexservice getActivePackages > /data/local/tmp/archtv-mc1/apex-active.txt 2>&1 && "
            "/apex/com.android.sdkext/bin/derive_classpath /data/local/tmp/archtv-mc1/classpath && "
            "/system/bin/chown 0:1000 /data/local/tmp/archtv-mc1/classpath && /system/bin/chmod 0640 /data/local/tmp/archtv-mc1/classpath"});
        if(!client.ok())return client.error();
        auto* process=client->get();
        process->AddReapCallback([this](const siginfo_t& info) {
            client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;
        });
        services.AddService(std::move(*client));
        if(auto result=process->ExecStart();!result.ok())return result;
        if(auto result=Wait(tick,[this]{return client_done_;},10);!result.ok())return result;
        if(!client_ok_)return android::base::Error()<<"Original APEX inventory client failed";
        std::string active_output;
        if(!android::base::ReadFileToString("/data/local/tmp/archtv-mc1/apex-active.txt",&active_output))return android::base::Error()<<"Original APEX inventory output missing";
        std::istringstream active_lines(active_output);std::string active_line;size_t active_count=0;
        while(std::getline(active_lines,active_line))if(active_line.rfind("Module: ",0)==0)++active_count;
        // Early completeness gate only. Existing independent verification still
        // must match every module/version/XML/mount; count is not acceptance.
        if(active_count!=41)return android::base::Error()<<"Original active APEX inventory incomplete: "<<active_count<<" expected41";
        std::fprintf(stderr,"APEX_ORIGINAL_CLIENT_RETURNED REQUIRES_EXTERNAL_COMPLETE_INVENTORY_CHECK\n");
        if(selected_requested_) {
            // Linux has already activated the complete APEX set. Preserve that
            // real view for bootstrap, then use original namespace setup and
            // switching; never assign the readiness flag ourselves.
            if(mount("/apex","/bootstrap-apex",nullptr,MS_BIND|MS_REC,nullptr)!=0)
                return android::base::ErrnoError()<<"Preserve actual APEX bootstrap view";
            if(!SetupMountNamespaces())return android::base::Error()<<"Original mount namespace setup failed";
            auto actual_namespace=GetCurrentMountNamespace();
            if(!actual_namespace.ok() || *actual_namespace!=NS_BOOTSTRAP)return android::base::Error()<<"Original bootstrap namespace not entered";
            std::fprintf(stderr,"APEX_ORIGINAL_BOOTSTRAP_NAMESPACE_ENTERED NOT_LINKER_READINESS\n");
            const std::vector<std::string> export_args={"load_exports","/data/local/tmp/archtv-mc1/classpath"};
            auto loader=GetBuiltinFunctionMap().Find(export_args);
            if(!loader.ok())return loader.error();
            const std::string context="u:r:init:s0";
            if(auto loaded=loader->function(BuiltinArguments{export_args,context});!loaded.ok())return loaded;
            std::fprintf(stderr,"PACKAGES_ORIGINAL_LOAD_EXPORTS_RETURNED NOT_JAVA_SERVICE_AVAILABILITY\n");
            auto config=GetBuiltinFunctionMap().Find({"perform_apex_config"});
            if(!config.ok())return config.error();
            if(auto configured=config->function(BuiltinArguments{{"perform_apex_config"},context});!configured.ok())return configured;
            std::fprintf(stderr,"APEX_ORIGINAL_BOOTSTRAP_CONFIG_RETURNED NOT_DEFAULT_READINESS\n");
            if(auto entered=SwitchToMountNamespaceIfNeeded(NS_DEFAULT);!entered.ok())return entered;
            auto default_namespace=GetCurrentMountNamespace();
            if(!default_namespace.ok() || *default_namespace!=NS_DEFAULT)return android::base::Error()<<"Original default namespace not entered";
            // Original parser skips bootstrap APEXes here because their real
            // configs were just parsed. It generates default linker config and
            // sets readiness itself; do not set a flag or property manually.
            if(auto configured=config->function(BuiltinArguments{{"perform_apex_config"},context});!configured.ok())return configured;
            if(!IsDefaultMountNamespaceReady())return android::base::Error()<<"Original default namespace not ready";
            std::fprintf(stderr,"APEX_ORIGINAL_DEFAULT_CONFIG_RETURNED REQUIRES_SERVICE_OPERATIONS\n");
            client_done_=false;client_ok_=false;
            auto storage=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","root","root","--","/system/bin/sh","-c",
                "umask 077; /system/bin/service check vold > /data/local/tmp/archtv-mc1/vold-query.txt 2>&1; /system/bin/vdc cryptfs init_user0 > /data/local/tmp/archtv-mc1/vold-user0.txt 2>&1"});
            if(!storage.ok())return storage.error();
            auto* storage_peer=storage->get();
            storage_peer->AddReapCallback([this](const siginfo_t& info){client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;});
            services.AddService(std::move(*storage));
            if(auto started=storage_peer->ExecStart();!started.ok())return started;
            if(auto waited=Wait(tick,[this]{return client_done_;},25);!waited.ok())return waited;
            if(!client_ok_)return android::base::Error()<<"Original vold init_user0 failed";
            std::fprintf(stderr,"STORAGE_ORIGINAL_USER0_RETURNED REQUIRES_FILES_AND_PERMISSION_PERSISTENCE\n");
            if(auto network=StartNetwork(tick);!network.ok())return network;

        }

        return {};
    }
    android::base::Result<void> StartNetwork(const Tick& tick) {
        using namespace android::init;
        auto& services=ServiceList::GetInstance();
        auto parser=CreateParser(ActionManager::GetInstance(),services);
        // Same Android16 APEX ELF, upstream nonroot coexistence role. Do not
        // start root netbpfload: it assumes ownership of global Linux BPF IDs.
        auto parsed=parser.ParseConfigFile("/apex/com.android.tethering/etc/netbpfload.33rc");
        if(!parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original nonroot network loader RC rejected";
        parsed=parser.ParseConfigFile("/vendor/etc/init/archtv-platform-bpfloader.rc");
        if(!parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Platform BPF loader Linux role rejected";
        for(const auto& name:std::vector<std::string>{"mdnsd_netbpfload","archtv-platform-bpfloader"}) {
            auto* loader=services.FindService(name);
            const std::string executable=name=="mdnsd_netbpfload"?"/apex/com.android.tethering/bin/netbpfload":"/archtv/bin/archtv-platform-bpfloader";
            if(!loader || loader->args()!=std::vector<std::string>{executable})return android::base::Error()<<"Unexpected network loader executable";
            client_done_=false;client_ok_=false;
            loader->AddReapCallback([this,name](const siginfo_t& info){client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;std::fprintf(stderr,"NETWORK_LOADER_EXIT name=%s pid=%d code=%d status=%d\n",name.c_str(),info.si_pid,info.si_code,info.si_status);});
            if(auto started=loader->Start();!started.ok())return started;
            std::fprintf(stderr,"NETWORK_LOADER_STARTED name=%s pid=%d uid=%u NOT_READY\n",name.c_str(),loader->pid(),loader->uid());
            if(auto waited=Wait(tick,[this]{return client_done_;},30);!waited.ok())return waited;
            if(!client_ok_)return android::base::Error()<<"Original network loader failed: "<<name;
            struct stat ready{};
            if(stat("/sys/fs/bpf/netd_shared/mainline_done",&ready)!=0 || !S_ISDIR(ready.st_mode))return android::base::Error()<<"Original mainline loader did not complete";
        }
        if(android::base::GetProperty("bpf.progs_loaded","")!="1")return android::base::Error()<<"Original platform loader did not publish completion";
        parsed=parser.ParseConfigFile("/vendor/etc/init/archtv-netd.rc");
        if(!parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original netd RC rejected";
        netd_=services.FindService("netd");
        if(!netd_ || netd_->args()!=std::vector<std::string>{"/system/bin/netd"})return android::base::Error()<<"Unexpected netd executable";
        netd_->AddReapCallback([this](const siginfo_t& info){std::fprintf(stderr,"NETWORK_NETD_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);if(!closing_)manager_failed_=true;});
        if(auto started=netd_->Start();!started.ok())return started;
        std::fprintf(stderr,"NETWORK_NETD_STARTED pid=%d NOT_REGISTERED\n",netd_->pid());
        client_done_=false;client_ok_=false;
        auto query=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","root","root","--","/system/bin/sh","-c",
            "umask 077; i=0; while [ $$i -lt 12 ]; do /system/bin/service check netd > /data/local/tmp/archtv-mc1/netd-query.txt 2>&1; if /system/bin/grep -qx 'Service netd: found' /data/local/tmp/archtv-mc1/netd-query.txt; then exit 0; fi; i=$$((i+1)); /system/bin/sleep 1; done; exit 1"});
        if(!query.ok())return query.error();
        auto* peer=query->get();peer->AddReapCallback([this](const siginfo_t& info){client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;});services.AddService(std::move(*query));
        if(auto started=peer->ExecStart();!started.ok())return started;
        if(auto waited=Wait(tick,[this]{return client_done_;},16);!waited.ok())return waited;
        if(!client_ok_)return android::base::Error()<<"Original netd Binder/interface query failed";
        std::fprintf(stderr,"NETWORK_NETD_REGISTRATION_ONLY NOT_INTERFACE_OR_PERMISSION_ACCEPTANCE\n");
        return {};
    }
    android::base::Result<void> StartHardware(const Tick& tick,bool defer_graphics=false) {
        using namespace android::init;
        auto& services=ServiceList::GetInstance();
        char value[PROP_VALUE_MAX]={};
        if((__system_property_get("hwservicemanager.ready",value)>0 && std::string(value)=="true") ||
           (__system_property_get("hwservicemanager.disabled",value)>0 && std::string(value)=="true"))
            return android::base::Error()<<"MC1 hardware manager stale ready or disabled by original configuration";
        auto parser=CreateParser(ActionManager::GetInstance(),services);
        const auto existing_services=services.size();
        auto parsed=parser.ParseConfigFile("/system/system_ext/etc/init/hwservicemanager.rc");
        if(!parsed.ok() || parser.parse_error_count()!=0 || services.size()!=existing_services+1)
            return android::base::Error()<<"MC1 hardware manager original profile rejected";
        hardware_=services.FindService("hwservicemanager");
        if(!hardware_ || hardware_->args()!=std::vector<std::string>{"/system/system_ext/bin/hwservicemanager"})
            return android::base::Error()<<"MC1 hardware manager unexpected executable";
        hardware_->AddReapCallback([this](const siginfo_t& info) {
            std::fprintf(stderr,"MC1_HWMANAGER_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
            if(!closing_)manager_failed_=true;
        });
        if(auto result=hardware_->Start();!result.ok())return result;
        std::fprintf(stderr,"MC1_HWMANAGER_STARTED pid=%d uid=%u gid=%u\n",hardware_->pid(),hardware_->uid(),hardware_->gid());
        if(auto result=Wait(tick,[]{char v[PROP_VALUE_MAX]={};return __system_property_get("hwservicemanager.ready",v)>0 && std::string(v)=="true";});!result.ok())return result;
        client_done_=false;client_ok_=false;
        auto client=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","shell","shell","--",
            "/system/bin/sh","-c","/system/bin/lshal debug -E android.hidl.manager@1.0::IServiceManager/default > /data/local/tmp/archtv-mc1/hardware-query.txt 2>&1"});
        if(!client.ok())return client.error();
        auto* process=client->get();
        process->AddReapCallback([this](const siginfo_t& info) {
            client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;
            std::fprintf(stderr,"MC1_HARDWARE_CLIENT_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
        });
        services.AddService(std::move(*client));
        if(auto result=process->ExecStart();!result.ok())return result;
        if(auto result=Wait(tick,[this]{return client_done_;});!result.ok())return result;
        if(!client_ok_)return android::base::Error()<<"MC1 original hardware client failed";
        // Original lshal NO_INTERFACE is 1<<7 (utils.h at the pinned revision).
        // Require its exact absence result; a crash/transaction error is not it.
        missing_done_=false;missing_ok_=false;
        auto missing=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","shell","shell","--",
            "/system/bin/sh","-c","/system/bin/lshal debug android.hidl.manager@1.2::IServiceManager/archtv-missing > /data/local/tmp/archtv-mc1/hardware-missing.txt 2>&1"});
        if(!missing.ok())return missing.error();
        auto* missing_process=missing->get();
        missing_process->AddReapCallback([this](const siginfo_t& info) {
            missing_done_=true;missing_ok_=info.si_code==CLD_EXITED && info.si_status==128;
            std::fprintf(stderr,"MC1_HARDWARE_MISSING_INSTANCE_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
        });
        services.AddService(std::move(*missing));
        if(auto result=missing_process->ExecStart();!result.ok())return result;
        if(auto result=Wait(tick,[this]{return missing_done_;});!result.ok())return result;
        if(!missing_ok_)return android::base::Error()<<"MC1 missing instance did not return original NO_INTERFACE";
        int observed_mode=security_getenforce();
        if(observed_mode!=expected_mode_)return android::base::Error()<<"MC1 hardware security mode changed";
        std::fprintf(stderr,"MC1_HARDWARE_CLIENT_EXIT0_REQUIRES_EXTERNAL_VERIFICATION enforcing=%d\n",observed_mode);
        if(graphics_requested_ && !defer_graphics)return StartGraphics(tick);
        return {};
    }
    android::base::Result<void> StartGraphics(const Tick& tick) {
        using namespace android::init;
        auto& services=ServiceList::GetInstance();
        // Parse the upstream RCs intact: the payload supplies their executable
        // paths. Original Service owns UID/groups/caps, transitions and cgroups.
        auto parser=CreateParser(ActionManager::GetInstance(),services);
        for(const char* path:{"/vendor/etc/init/allocator.rc","/vendor/etc/init/hwcomposer3.rc"}) {
            auto parsed=parser.ParseConfigFile(path);
            if(!parsed.ok() || parser.parse_error_count()!=0)
                return android::base::Error()<<"MC3 original graphics RC rejected: "<<path;
        }
        allocator_=services.FindService("vendor.graphics.allocator");
        composer_=services.FindService("vendor.hwcomposer-3");
        if(!allocator_ || !composer_ ||
           allocator_->args()!=std::vector<std::string>{"/vendor/bin/hw/android.hardware.graphics.allocator-service.minigbm"} ||
           composer_->args()!=std::vector<std::string>{"/vendor/bin/hw/android.hardware.graphics.composer3-service.ranchu"})
            return android::base::Error()<<"MC3 unexpected original graphics service profile";
        for(auto* service:{allocator_,composer_}) {
            service->AddReapCallback([this](const siginfo_t& info) {
                std::fprintf(stderr,"MC3_GRAPHICS_SERVICE_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
                if(!closing_)manager_failed_=true;
            });
            if(auto result=service->Start();!result.ok())return result;
            std::fprintf(stderr,"MC3_GRAPHICS_SERVICE_STARTED name=%s pid=%d uid=%u gid=%u NOT_REGISTERED\n",
                         service->name().c_str(),service->pid(),service->uid(),service->gid());
        }
        if(surfaceflinger_requested_)return StartSurfaceFlinger(tick);
        client_done_=false;client_ok_=false;
        // Explicit experimental API client in the original SF client domain;
        // this is not SurfaceFlinger or an APK. No readiness property is set.
        auto client=Service::MakeTemporaryOneshotService({"exec","u:r:surfaceflinger:s0","system","graphics","--",
            "/vendor/bin/hw/archtv-graphics-client"});
        if(!client.ok())return client.error();
        auto* process=client->get();
        process->AddReapCallback([this](const siginfo_t& info) {
            client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;
            std::fprintf(stderr,"MC3_GRAPHICS_CLIENT_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
        });
        services.AddService(std::move(*client));
        if(auto result=process->ExecStart();!result.ok())return result;
        if(auto result=Wait(tick,[this]{return client_done_;});!result.ok())return result;
        if(!client_ok_)return android::base::Error()<<"MC3 graphics client failed";
        if(security_getenforce()!=expected_mode_)return android::base::Error()<<"MC3 security mode changed";
        return {};
    }
    android::base::Result<void> StartSurfaceFlinger(const Tick& tick) {
        using namespace android::init;
        auto& services=ServiceList::GetInstance();
        auto parser=CreateParser(ActionManager::GetInstance(),services);
        for(const char* path:{"/system/etc/init/surfaceflinger.rc","/system/etc/init/bootanim.rc"}) {
            auto parsed=parser.ParseConfigFile(path);
            if(!parsed.ok() || parser.parse_error_count()!=0)
                return android::base::Error()<<"MC3 original SF/client RC rejected: "<<path;
        }
        surfaceflinger_=services.FindService("surfaceflinger");
        bootanimation_=services.FindService("bootanim");
        if(!surfaceflinger_ || !bootanimation_ ||
           surfaceflinger_->args()!=std::vector<std::string>{"/system/bin/surfaceflinger"} ||
           bootanimation_->args()!=std::vector<std::string>{"/system/bin/bootanimation"})
            return android::base::Error()<<"MC3 unexpected original SF/client executable";
        for(auto* service:{surfaceflinger_,bootanimation_}) {
            service->AddReapCallback([this](const siginfo_t& info) {
                std::fprintf(stderr,"MC3_SF_SERVICE_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
                if(!closing_)manager_failed_=true;
            });
        }
        if(auto result=surfaceflinger_->Start();!result.ok())return result;
        std::fprintf(stderr,"MC3_ORIGINAL_SF_STARTED pid=%d NOT_REGISTERED\n",surfaceflinger_->pid());
        client_done_=false;client_ok_=false;
        // Poll actual original Binder CLI results, not the CLI exit code alone.
        // ctl.start/lazy-service backend remains fail-closed; this cohort starts
        // the original RC services explicitly, without Android boot dispatch.
        auto client=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","shell","shell","--",
            "/system/bin/sh","-c",
            "umask 077; i=0; while [ $$i -lt 30 ]; do "
            "/system/bin/service check SurfaceFlinger > /data/local/tmp/archtv-mc1/sf-query.txt 2>&1; "
            "/system/bin/service check SurfaceFlingerAIDL > /data/local/tmp/archtv-mc1/sf-aidl-query.txt 2>&1; "
            "if /system/bin/grep -qx 'Service SurfaceFlinger: found' /data/local/tmp/archtv-mc1/sf-query.txt && "
            "/system/bin/grep -qx 'Service SurfaceFlingerAIDL: found' /data/local/tmp/archtv-mc1/sf-aidl-query.txt; then exit 0; fi; "
            "i=$$((i+1)); /system/bin/sleep 1; done; exit 1"});
        if(!client.ok())return client.error();
        auto* process=client->get();
        process->AddReapCallback([this](const siginfo_t& info) {
            client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;
            std::fprintf(stderr,"MC3_ORIGINAL_SF_QUERY_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
        });
        services.AddService(std::move(*client));
        if(auto result=process->ExecStart();!result.ok())return result;
        if(auto result=Wait(tick,[this]{return client_done_;},35);!result.ok())return result;
        if(!client_ok_)return android::base::Error()<<"MC3 original SF service queries failed";
        if(auto result=bootanimation_->Start();!result.ok())return result;
        bootanimation_started_=true;
        std::fprintf(stderr,"MC3_ORIGINAL_BOOTANIMATION_STARTED pid=%d NOT_PIXEL_ACCEPTANCE\n",bootanimation_->pid());
        if(selected_requested_)return StartSelectedDisplay(tick);
        if(security_getenforce()!=expected_mode_)return android::base::Error()<<"MC3 security mode changed";
        return {};
    }
    android::base::Result<void> StartSelectedDisplay(const Tick& tick) {
        std::fprintf(stderr,"SELECTED_SHADER_PRIMING_PROPERTY actual=%s NO_RENDER_ACCEPTANCE\n",android::base::GetProperty("service.sf.prime_shader_cache", "unset").c_str());
        using namespace android::init;
        auto& services=ServiceList::GetInstance();
        auto parser=CreateParser(ActionManager::GetInstance(),services);
        // Original upstream SystemSuspend keeps its own real wakelock counter
        // when Linux owns host sleep. No /sys/power controls are exposed here.
        if(apex_requested_) {
            statsd_=services.FindService("statsd");
            if(!statsd_ || statsd_->args()!=std::vector<std::string>{"/apex/com.android.os.statsd/bin/statsd"})return android::base::Error()<<"Original perform_apex_config did not register expected statsd";
            statsd_->AddReapCallback([this](const siginfo_t& info){std::fprintf(stderr,"SELECTED_STATSD_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);if(!closing_)manager_failed_=true;});
            if(auto started=statsd_->Start();!started.ok())return started;
            std::fprintf(stderr,"SELECTED_STATSD_STARTED pid=%d NOT_REGISTERED\n",statsd_->pid());
            auto health_parsed=parser.ParseConfigFile("/vendor/etc/init/archtv-health.rc");
            if(!health_parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original health RC rejected";
            health_=services.FindService("vendor.health-default");
            if(!health_ || health_->args()!=std::vector<std::string>{"/vendor/bin/hw/android.hardware.health-service.example"})return android::base::Error()<<"Unexpected original health provider";
            health_->AddReapCallback([this](const siginfo_t& info){std::fprintf(stderr,"SELECTED_HEALTH_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);if(!closing_)manager_failed_=true;});
            if(auto started=health_->Start();!started.ok())return started;
            std::fprintf(stderr,"SELECTED_HEALTH_STARTED pid=%d NOT_REGISTERED\n",health_->pid());
            client_done_=false;client_ok_=false;
            auto health_client=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","shell","shell","--","/system/bin/sh","-c",
                "umask 077; i=0; while [ $$i -lt 12 ]; do /system/bin/service check android.hardware.health.IHealth/default > /data/local/tmp/archtv-mc1/health-query.txt 2>&1; /system/bin/service check stats > /data/local/tmp/archtv-mc1/stats-query.txt 2>&1; if /system/bin/grep -qx 'Service stats: found' /data/local/tmp/archtv-mc1/stats-query.txt && /system/bin/grep -qx 'Service android.hardware.health.IHealth/default: found' /data/local/tmp/archtv-mc1/health-query.txt; then /system/bin/dumpsys android.hardware.health.IHealth/default > /data/local/tmp/archtv-mc1/health-dump.txt 2>&1; exit $$?; fi; i=$$((i+1)); /system/bin/sleep 1; done; exit 1"});
            if(!health_client.ok())return health_client.error();
            auto* health_peer=health_client->get();health_peer->AddReapCallback([this](const siginfo_t& info){client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;});services.AddService(std::move(*health_client));
            if(auto started=health_peer->ExecStart();!started.ok())return started;
            if(auto waited=Wait(tick,[this]{return client_done_;},16);!waited.ok())return waited;
            if(!client_ok_)return android::base::Error()<<"Original IHealth query/dump failed";
            std::fprintf(stderr,"HEALTH_ORIGINAL_BINDER_CLIENT_RETURNED REQUIRES_VALUE_VERIFICATION\n");
            auto zygote_parsed=parser.ParseConfigFile("/vendor/etc/init/archtv-app-zygote.rc");
            if(!zygote_parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Application zygote profile rejected";
            zygote_=services.FindService("zygote");
            if(!zygote_ || zygote_->args().empty() || zygote_->args().front()!="/system/bin/app_process64")return android::base::Error()<<"Unexpected zygote executable";
            for(const auto& argument:zygote_->args())if(argument=="--start-system-server")return android::base::Error()<<"Full SystemServer startup prohibited";
            zygote_->AddReapCallback([this](const siginfo_t& info){
                std::fprintf(stderr,"SELECTED_ZYGOTE_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
                if(!closing_)manager_failed_=true;
            });
            if(auto started=zygote_->Start();!started.ok())return started;
            std::fprintf(stderr,"SELECTED_ZYGOTE_STARTED pid=%d NOT_APP_LAUNCH\n",zygote_->pid());
        }
        auto native_parsed=parser.ParseConfigFile("/system/etc/init/android.system.suspend-service.rc");
        if(!native_parsed.ok() || parser.parse_error_count()!=0)
            return android::base::Error()<<"Original SystemSuspend RC rejected";
        suspend_=services.FindService("system_suspend");
        if(!suspend_ || suspend_->args()!=std::vector<std::string>{"/system/bin/hw/android.system.suspend-service"})
            return android::base::Error()<<"Unexpected original SystemSuspend executable";
        suspend_->AddReapCallback([this](const siginfo_t& info) {
            std::fprintf(stderr,"SELECTED_SUSPEND_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
            if(!closing_)manager_failed_=true;
        });
        if(auto result=suspend_->Start();!result.ok())return result;
        std::fprintf(stderr,"SELECTED_SUSPEND_STARTED pid=%d NOT_REGISTERED\n",suspend_->pid());
        auto installer_parsed=parser.ParseConfigFile("/system/etc/init/installd.rc");
        if(!installer_parsed.ok() || parser.parse_error_count()!=0)
            return android::base::Error()<<"Original installd RC rejected";
        installd_=services.FindService("installd");
        if(!installd_ || installd_->args()!=std::vector<std::string>{"/system/bin/installd"})
            return android::base::Error()<<"Unexpected original installd executable";
        installd_->AddReapCallback([this](const siginfo_t& info) {
            std::fprintf(stderr,"SELECTED_INSTALLD_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
            if(!closing_)manager_failed_=true;
        });
        if(auto result=installd_->Start();!result.ok())return result;
        std::fprintf(stderr,"SELECTED_INSTALLD_STARTED pid=%d NOT_REGISTERED\n",installd_->pid());
        auto parsed=parser.ParseConfigFile("/vendor/etc/init/archtv-selected-services.rc");
        if(!parsed.ok() || parser.parse_error_count()!=0)
            return android::base::Error()<<"Selected original service orchestration RC rejected";
        selected_=services.FindService("archtv-selected-services");
        if(!selected_ || selected_->args().empty() || (selected_->args().front()!="/system/bin/app_process64" && !(apex_requested_ && selected_->args().front()=="/system/bin/sh")))
            return android::base::Error()<<"Unexpected selected service runtime";
        selected_->AddReapCallback([this](const siginfo_t& info) {
            std::fprintf(stderr,"SELECTED_SERVICES_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
            if(!closing_)manager_failed_=true;
        });
        if(auto result=selected_->Start();!result.ok())return result;
        std::fprintf(stderr,"SELECTED_SERVICES_STARTED pid=%d NOT_REGISTERED\n",selected_->pid());
        client_done_=false;client_ok_=false;
        auto client=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","shell","shell","--",
            "/system/bin/sh","-c",
            "umask 077; i=0; while [ $$i -lt 30 ]; do "
            "/system/bin/service check installd > /data/local/tmp/archtv-mc1/installd-query.txt 2>&1; "
            "/system/bin/service check display > /data/local/tmp/archtv-mc1/display-query.txt 2>&1; "
            "if /system/bin/grep -qx 'Service display: found' /data/local/tmp/archtv-mc1/display-query.txt && "
            "/system/bin/grep -qx 'Service installd: found' /data/local/tmp/archtv-mc1/installd-query.txt; then "
            "/system/bin/dumpsys display > /data/local/tmp/archtv-mc1/display-dump.txt 2>&1; "
            "/system/bin/cmd display get-displays --ids-only > /data/local/tmp/archtv-mc1/display-ids.txt 2>&1; "
            "if /system/bin/grep -qx '0' /data/local/tmp/archtv-mc1/display-ids.txt; then exit 0; fi; fi; "
            "i=$$((i+1)); /system/bin/sleep 1; done; exit 1"});
        if(!client.ok())return client.error();
        auto* process=client->get();
        process->AddReapCallback([this](const siginfo_t& info) {
            client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;
            std::fprintf(stderr,"SELECTED_DISPLAY_CLIENT_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
        });
        services.AddService(std::move(*client));
        if(auto result=process->ExecStart();!result.ok())return result;
        if(auto result=Wait(tick,[this]{return client_done_;},35);!result.ok())return result;
        if(!client_ok_)return android::base::Error()<<"Original display CLI did not find default display";
        if(apex_requested_) {
            // Root's original netd permission check requires the real AMS
            // permission controller. Do not bypass it or report Binder lookup
            // as a successful netd operation.
            client_done_=false;client_ok_=false;
            auto network_query=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","root","root","--","/system/bin/sh","-c",
                "umask 077; i=0; while [ $$i -lt 12 ]; do /system/bin/service check permission > /data/local/tmp/archtv-mc1/netd-permission-query.txt 2>&1; if /system/bin/grep -qx 'Service permission: found' /data/local/tmp/archtv-mc1/netd-permission-query.txt; then /system/bin/ndc interface list > /data/local/tmp/archtv-mc1/netd-interfaces.txt 2>&1; /system/bin/grep -qx '200 0 Interface list completed' /data/local/tmp/archtv-mc1/netd-interfaces.txt && /system/bin/grep -qx '110 0 lo' /data/local/tmp/archtv-mc1/netd-interfaces.txt; exit $$?; fi; i=$$((i+1)); /system/bin/sleep 1; done; exit 1"});
            if(!network_query.ok())return network_query.error();
            auto* network_peer=network_query->get();network_peer->AddReapCallback([this](const siginfo_t& info){client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;});services.AddService(std::move(*network_query));
            if(auto started=network_peer->ExecStart();!started.ok())return started;
            if(auto waited=Wait(tick,[this]{return client_done_;},16);!waited.ok())return waited;
            if(!client_ok_)return android::base::Error()<<"Original authorized netd interface operation failed";
            std::fprintf(stderr,"NETWORK_NETD_ORIGINAL_INTERFACE_LIST_PASSED NOT_INTERNET_OR_TENANT_PERMISSION_ACCEPTANCE\n");
        }
        if(apex_requested_) {
            client_done_=false;client_ok_=false;
            auto package_client=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","shell","shell","--",
                "/system/bin/sh","-c","umask 077; i=0; while [ $$i -lt 30 ]; do /system/bin/service check package > /data/local/tmp/archtv-mc1/package-query.txt 2>&1; /system/bin/service check activity > /data/local/tmp/archtv-mc1/activity-query.txt 2>&1; /system/bin/service check mount > /data/local/tmp/archtv-mc1/mount-query.txt 2>&1; if /system/bin/grep -qx 'Service package: found' /data/local/tmp/archtv-mc1/package-query.txt && /system/bin/grep -qx 'Service activity: found' /data/local/tmp/archtv-mc1/activity-query.txt && /system/bin/grep -qx 'Service mount: found' /data/local/tmp/archtv-mc1/mount-query.txt; then /system/bin/cmd package list packages --user 0 > /data/local/tmp/archtv-mc1/package-list.txt 2>&1; /system/bin/cmd package path --user 0 net.gsantner.markor > /data/local/tmp/archtv-mc1/markor-path.txt 2>&1; if /system/bin/grep -q '^package:/data/app/' /data/local/tmp/archtv-mc1/markor-path.txt && /system/bin/grep -qx 'Status: ok' /data/local/tmp/archtv-mc1/markor-launch.txt; then /system/bin/dumpsys package net.gsantner.markor > /data/local/tmp/archtv-mc1/markor-dump.txt 2>&1; exit $$?; fi; fi; i=$$((i+1)); /system/bin/sleep 1; done; exit 1"});
            if(!package_client.ok())return package_client.error();
            auto* peer=package_client->get();
            peer->AddReapCallback([this](const siginfo_t& info){client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;});
            services.AddService(std::move(*package_client));
            if(auto result=peer->ExecStart();!result.ok())return result;
            if(auto result=Wait(tick,[this]{return client_done_;},35);!result.ok())return result;
            if(!client_ok_)return android::base::Error()<<"Original package client did not observe installed Markor";
            std::fprintf(stderr,"PACKAGES_ORIGINAL_BINDER_QUERY_RETURNED REQUIRES_INSTALL_LAUNCH\n");
        }
        if(security_getenforce()!=expected_mode_)return android::base::Error()<<"Selected display security mode changed";
        return {};
    }
    android::base::Result<void> Wait(const Tick& tick,const std::function<bool()>& done,int seconds=5) {
        const auto end=std::chrono::steady_clock::now()+std::chrono::seconds(seconds);
        for(;;) {
            if(stop_ || !healthy())return android::base::Error()<<"MC1 stopped or manager exited";
            if(done())return {};
            if(std::chrono::steady_clock::now()>=end || !tick())
                return android::base::Error()<<"MC1 original progress deadline/error";
        }
    }
    const bool& stop_;
    const int expected_mode_;
    const bool hardware_requested_;
    const bool graphics_requested_;
    const bool surfaceflinger_requested_;
    const bool selected_requested_;
    const bool apex_requested_;
    android::init::Service* netd_=nullptr;
    android::init::Service* statsd_=nullptr;
    android::init::Service* health_=nullptr;
    android::init::Service* zygote_=nullptr;
    android::init::Service* vold_=nullptr;
    android::init::Service* manager_=nullptr;
    android::init::Service* hardware_=nullptr;
    android::init::Service* allocator_=nullptr;
    android::init::Service* composer_=nullptr;
    android::init::Service* surfaceflinger_=nullptr;
    android::init::Service* bootanimation_=nullptr;
    android::init::Service* selected_=nullptr;
    android::init::Service* suspend_=nullptr;
    android::init::Service* installd_=nullptr;
    android::init::Service* apexd_=nullptr;
    bool bootanimation_started_=false;
    bool missing_done_=false,missing_ok_=false;
    bool apex_cancelled_=false,vold_cancelled_=false;
    bool active_=false,closing_=false,manager_failed_=false,client_done_=false,client_ok_=false;
};
}
