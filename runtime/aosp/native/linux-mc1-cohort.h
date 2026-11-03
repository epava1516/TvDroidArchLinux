#include <private/android_filesystem_config.h>
#pragma once
// One bounded MC1 functional experiment, using original service lifecycle code.
// No boot scripts, synthesized readiness, general control backend or APK acceptance.
#include "init.h"
#include "builtins.h"
#include "service.h"
#include "service_list.h"
#include "parser.h"
#include "mount_namespace.h"
#include "util.h"
#include <sys/mount.h>
#include <fcntl.h>
#include <sys/statvfs.h>
#include <dlfcn.h>
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
#include <utility>
#include <memory>
#include <chrono>
#include <functional>
#include <string>
#include <sstream>

namespace archtv::aosp {
class LinuxMc1Cohort {
 public:
    using Tick = std::function<bool()>;
    LinuxMc1Cohort(android::init::Epoll* epoll,const bool& stop,int expected_mode,bool hardware=false,bool graphics=false,bool surfaceflinger=false,bool selected=false,bool apex=false,int wayland_fd=-1)
        : epoll_(epoll),stop_(stop),expected_mode_(expected_mode),hardware_requested_(hardware),graphics_requested_(graphics),surfaceflinger_requested_(surfaceflinger),selected_requested_(selected),apex_requested_(apex),wayland_channel_(wayland_fd) {}
    android::base::Result<void> Start(const Tick& tick) {
        using namespace android::init;
        auto& services=ServiceList::GetInstance();
        if(services.size()!=0) return android::base::Error()<<"MC1 requires a fresh service list";
        if(expected_mode_==1) {
            // Linux's PID1 supervises this private runtime. Its mount view may
            // contain host control resources and must stay inaccessible even
            // while original init opens its own namespace for APEX setup.
            if(getpid()==1)return android::base::Error()<<"Expected separate Linux PID1 supervisor";
            errno=0;
            int control_namespace=open("/proc/1/ns/mnt",O_RDONLY|O_CLOEXEC);
            int denied_errno=errno;
            if(control_namespace>=0) {
                close(control_namespace);
                return android::base::Error()<<"Linux supervisor namespace unexpectedly accessible";
            }
            if(denied_errno!=EACCES)return android::base::Error()<<"Supervisor namespace negative inconclusive: "<<denied_errno;
            std::fprintf(stderr,"MAC_NEGATIVE_LINUX_SUPERVISOR_NAMESPACE_DENIED errno=13 NOT_GENERAL_ISOLATION_ACCEPTANCE\n");
        }
        active_=true;
        Action::set_function_map(&GetBuiltinFunctionMap());
        if(apex_requested_ && selected_requested_) {
            if(auto bootstrap=BootstrapOriginalApex(tick);!bootstrap.ok())return bootstrap;
            if(auto logging=StartOriginalLogging(tick);!logging.ok())return logging;
        }
        auto parser=CreateParser(ActionManager::GetInstance(),services);
        auto parsed=parser.ParseConfigFile("/system/etc/init/servicemanager.rc");
        if(!parsed.ok() || parser.parse_error_count()!=0)
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
        client_done_=false;client_ok_=false;
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
        struct stat keystore_profile_info{};
        const char* keystore_profile="/vendor/etc/archtv-keystore-component";
        if(lstat(keystore_profile,&keystore_profile_info)==0) {
            std::string profile;
            if(!apex_requested_ || !S_ISREG(keystore_profile_info.st_mode) || keystore_profile_info.st_uid!=0 ||
               !android::base::ReadFileToString(keystore_profile,&profile) || profile!="software-keystore-v1\n")
                return android::base::Error()<<"Invalid Linux Keystore diagnostic profile";
            std::string platform_profile;
            if(android::base::ReadFileToString("/vendor/etc/archtv-software-security",&platform_profile)) {
                if(platform_profile!="software-platform-v1\n")return android::base::Error()<<"Unknown software platform profile";
                software_security_=true;
            }
            if(auto software=RunOriginalSoftwareKeystore(tick);!software.ok())return software;
            if(!software_security_)return {};
        } else if(errno!=ENOENT)return android::base::Error()<<"Cannot inspect Linux Keystore diagnostic profile";
        // Explicit immutable Linux diagnostic profile, not an Android readiness flag.
        const char* keymint_profile="/vendor/etc/archtv-keymint-component";
        struct stat profile_info{};
        if(lstat(keymint_profile,&profile_info)==0) {
            std::string profile;
            if(!apex_requested_ || !S_ISREG(profile_info.st_mode) || profile_info.st_uid!=0 ||
               !android::base::ReadFileToString(keymint_profile,&profile) || profile!="software-crypto-v1\n")
                return android::base::Error()<<"Invalid Linux KeyMint diagnostic profile";
            auto component=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","root","root","--",
                "/system/bin/sh","-c","umask 077; /archtv/bin/archtv-keymint-probe write /data/local/tmp/archtv-mc1/keymint-private-test-state.bin > /data/local/tmp/archtv-mc1/keymint-component.txt 2>&1 && /archtv/bin/archtv-keymint-probe read /data/local/tmp/archtv-mc1/keymint-private-test-state.bin >> /data/local/tmp/archtv-mc1/keymint-component.txt 2>&1"});
            if(!component.ok())return component.error();
            auto* process=component->get();client_done_=false;client_ok_=false;
            process->AddReapCallback([this](const siginfo_t& info){client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;});
            services.AddService(std::move(*component));
            if(auto started=process->ExecStart();!started.ok())return started;
            if(auto waited=Wait(tick,[this]{return client_done_;},35);!waited.ok())return waited;
            if(!client_ok_)return android::base::Error()<<"Original software KeyMint component failed; inspect actual output";
            std::fprintf(stderr,"KEYMINT_COMPONENT_RETURNED REQUIRES_OUTPUT_VERIFICATION_NOT_KEYSTORE_OR_APK_ACCEPTANCE\n");
            return {};
        }
        if(errno!=ENOENT)return android::base::Error()<<"Cannot inspect Linux KeyMint diagnostic profile";
        if(hardware_requested_)return apex_requested_ && selected_requested_ ? StartGraphics(tick) : StartHardware(tick);
        return {};
    }
    bool vold_cancelled() const { return vold_cancelled_; }
    bool apex_cancelled() const { return apex_cancelled_; }
    bool apex_exited_cleanly() const {
        // Close clears the pointer only after every service has been reaped.
        return apex_clean_exit_ && (!apexd_ || !apexd_->IsRunning());
    }
    bool healthy() const { return (!logd_ || logd_->IsRunning()) && (!logcat_ || logcat_->IsRunning()) && !manager_failed_ && (!storaged_ || storaged_->IsRunning()) && (!swcodec_ || swcodec_->IsRunning()) && (!idmap_ || idmap_->IsRunning()) && (!gatekeeper_hal_ || gatekeeper_hal_->IsRunning()) && (!gatekeeper_ || gatekeeper_->IsRunning()) && (!keystore_ || keystore_->IsRunning()) && (!keymint_ || keymint_->IsRunning()) && (!aconfig_system_ || aconfig_system_->IsRunning() || aconfig_system_clean_exit_) && (!aconfig_mainline_ || aconfig_mainline_->IsRunning() || aconfig_mainline_clean_exit_) && (!audioserver_ || audioserver_->IsRunning()) && (!lmkd_ || lmkd_->IsRunning()) && (!netd_ || netd_->IsRunning()) && (!statsd_ || statsd_->IsRunning()) && (!health_ || health_->IsRunning()) && (!zygote_ || zygote_->IsRunning()) && (!vold_ || vold_->IsRunning()) && (!manager_ || manager_->IsRunning()) && (!hardware_ || hardware_->IsRunning()) && (!allocator_ || allocator_->IsRunning()) && (!composer_ || composer_->IsRunning()) && (!surfaceflinger_ || surfaceflinger_->IsRunning()) && (!bootanimation_started_ || (bootanimation_ && (bootanimation_->IsRunning() || bootanimation_clean_exit_))) && (!selected_ || selected_->IsRunning()) && (!suspend_ || suspend_->IsRunning()) && (!installd_ || installd_->IsRunning()) && (!apexd_ || apexd_->IsRunning() || apex_clean_exit_); }
    android::base::Result<void> Close(const Tick& tick) {
        using namespace android::init;
        if(!active_) return {};
        closing_=true;
        if(auto revoked=RevokeLinuxLazyInterfaces(epoll_);!revoked.ok())return revoked;
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
        manager_=nullptr;logd_=nullptr;logcat_=nullptr;
        hardware_=nullptr;
        allocator_=nullptr;
        composer_=nullptr;
        surfaceflinger_=nullptr;
        bootanimation_=nullptr;
        bootanimation_started_=false;
        aconfig_system_=nullptr;aconfig_mainline_=nullptr;
        aconfig_system_clean_exit_=false;aconfig_mainline_clean_exit_=false;
        audioserver_=nullptr;
        storaged_=nullptr;swcodec_=nullptr;idmap_=nullptr;
        lmkd_=nullptr;
        netd_=nullptr;
        statsd_=nullptr;
        health_=nullptr;
        selected_=nullptr;
        suspend_=nullptr;
        installd_=nullptr;
        apexd_=nullptr;software_security_=false;gatekeeper_hal_=nullptr;gatekeeper_=nullptr;keystore_=nullptr;keymint_=nullptr;
        services.RemoveServiceIf([](const auto& service){return !service->IsRunning();});
        active_=false;
        int observed_mode=security_getenforce();
        std::fprintf(stderr,"MC1_CLOSE_OBSERVED enforcing=%d expected=%d\n",observed_mode,expected_mode_);
        if(observed_mode!=expected_mode_)return android::base::Error()<<"MC1 security mode changed during close";
        return {};
    }
 private:
    android::base::Result<void> StartOriginalLogging(const Tick& tick) {
        using namespace android::init;
        if(android::base::GetProperty("ro.logd.kernel","")!="false" || android::base::GetProperty("ro.logd.auditd","")!="false")
            return android::base::Error()<<"Original logd must preserve Linux kernel/audit ownership";
        auto& services=ServiceList::GetInstance();
        auto parser=CreateParser(ActionManager::GetInstance(),services);
        auto parsed=parser.ParseConfigFile("/vendor/etc/init/archtv-logd.rc");
        if(!parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original logd RC rejected";
        logd_=services.FindService("logd");
        if(!logd_ || logd_->args()!=std::vector<std::string>{"/system/bin/logd"} || logd_->uid()!=1036)
            return android::base::Error()<<"Unexpected original logd entry";
        if(android::base::GetProperty("logd.ready","")=="true")return android::base::Error()<<"Stale logd readiness";
        logd_->AddReapCallback([this](const siginfo_t& info){std::fprintf(stderr,"ORIGINAL_LOGD_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);if(!closing_)manager_failed_=true;});
        if(auto started=logd_->Start();!started.ok())return started;
        std::fprintf(stderr,"ORIGINAL_LOGD_STARTED pid=%d NOT_READY\n",logd_->pid());
        if(auto waited=Wait(tick,[]{return android::base::GetProperty("logd.ready","")=="true";});!waited.ok())return waited;
        // Real shell client with original log group; no invented sender GID.
        // Continuous original reader preserves startup failures before shutdown.
        auto reader=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","shell","shell","log","--",
            "/system/bin/sh","-c","umask 077; exec /system/bin/logcat -b all -v threadtime -v uid > /data/local/tmp/archtv-mc1/original-logcat.txt 2>&1"});
        if(!reader.ok())return reader.error();
        logcat_=reader->get();
        logcat_->AddReapCallback([this](const siginfo_t& info){std::fprintf(stderr,"ORIGINAL_LOGCAT_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);if(!closing_)manager_failed_=true;});
        services.AddService(std::move(*reader));
        if(auto started=logcat_->Start();!started.ok())return started;
        std::fprintf(stderr,"ORIGINAL_LOGD_READY_REQUIRES_CLIENT_OUTPUT logcat_pid=%d\n",logcat_->pid());
        return {};
    }
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
    android::base::Result<void> BootstrapOriginalApex(const Tick& tick) {
        using namespace android::init;
        auto& services=ServiceList::GetInstance();
        if(!SetupMountNamespaces())return android::base::Error()<<"Original pre-bootstrap namespace setup failed";
        auto current=GetCurrentMountNamespace();
        if(!current.ok() || *current!=NS_BOOTSTRAP)return android::base::Error()<<"Original bootstrap namespace missing";
        auto parser=CreateParser(ActionManager::GetInstance(),services);
        auto parsed=parser.ParseConfigFile("/system/etc/init/apexd.rc");
        if(!parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original bootstrap APEX RC rejected";
        auto* bootstrap=services.FindService("apexd-bootstrap");
        if(!bootstrap || bootstrap->args()!=std::vector<std::string>{"/system/bin/apexd","--bootstrap"})
            return android::base::Error()<<"Original bootstrap executable/arguments missing";
        client_done_=false;client_ok_=false;
        bootstrap->AddReapCallback([this](const siginfo_t& info){
            client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;
            std::fprintf(stderr,"APEX_BOOTSTRAP_ORIGINAL_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
        });
        if(auto started=bootstrap->ExecStart();!started.ok())return started;
        std::fprintf(stderr,"APEX_BOOTSTRAP_STARTED pid=%d NOT_FULL_INVENTORY\n",bootstrap->pid());
        if(auto waited=Wait(tick,[this]{return client_done_;},100);!waited.ok())return waited;
        if(!client_ok_)return android::base::Error()<<"Original APEX bootstrap failed";
        auto config=GetBuiltinFunctionMap().Find({"perform_apex_config"});
        if(!config.ok())return config.error();
        if(auto configured=config->function(BuiltinArguments{{"perform_apex_config"},"u:r:init:s0"});!configured.ok())return configured;
        apex_bootstrap_prepared_=true;
        std::fprintf(stderr,"APEX_BOOTSTRAP_ORIGINAL_CONFIG_RETURNED NOT_DEFAULT_READINESS\n");
        return {};
    }
    android::base::Result<void> StartApex(const Tick& tick) {
        using namespace android::init;
        auto& services=ServiceList::GetInstance();
        if(!android::base::GetProperty("apexd.status","").empty())
            return android::base::Error()<<"Refusing stale APEX status";
        if(!apex_bootstrap_prepared_) {
            auto parser=CreateParser(ActionManager::GetInstance(),services);
            auto parsed=parser.ParseConfigFile("/system/etc/init/apexd.rc");
            if(!parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original APEX service profile rejected";
        } else {
            auto enter=GetBuiltinFunctionMap().Find({"enter_default_mount_ns"});
            if(!enter.ok())return enter.error();
            if(auto entered=enter->function(BuiltinArguments{{"enter_default_mount_ns"},"u:r:init:s0"});!entered.ok())return entered;
            auto current=GetCurrentMountNamespace();
            if(!current.ok() || *current!=NS_DEFAULT)return android::base::Error()<<"Original default namespace missing before normal APEX";
        }
        apexd_=services.FindService("apexd");
        if(!apexd_ || apexd_->args()!=std::vector<std::string>{"/system/bin/apexd"})
            return android::base::Error()<<"Unexpected original apexd executable";
        apexd_->AddReapCallback([this](const siginfo_t& info) {
            std::fprintf(stderr,"APEX_DAEMON_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
            if(closing_ && stop_ && info.si_code==CLD_KILLED && info.si_status==SIGKILL)apex_cancelled_=true;
            // Original apexd enables lazy Binder shutdown after boot cleanup.
            // Its normal exit does not unmount the verified active modules.
            apex_clean_exit_=apex_activation_observed_ && info.si_code==CLD_EXITED && info.si_status==0
                && android::base::GetProperty("apexd.status","")=="ready";
            std::fprintf(stderr,"APEX_LAZY_EXIT_OBSERVED clean=%d NOT_LAZY_RESTART_OR_APK_ACCEPTANCE\n",apex_clean_exit_);
            if(!closing_ && !apex_clean_exit_)manager_failed_=true;
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
        // Original init.rc does not query apexservice through an unauthorized
        // root/shell diagnostic before derive_classpath. Original ApexManager
        // in system_server is the later authorized Binder consumer. The Linux
        // verifier checks original XML/versions/mounts; do not invent inventory
        // or grant shell access to a protected service for a diagnostic gate.
        apex_activation_observed_=true;
        std::fprintf(stderr,"APEX_ORIGINAL_ACTIVATION_OBSERVED REQUIRES_FRAMEWORK_QUERY_AND_EXTERNAL_INVENTORY\n");
        if(selected_requested_) {
            if(!apex_bootstrap_prepared_)return android::base::Error()<<"Original bootstrap phase missing";
            const std::string context="u:r:init:s0";
            auto config=GetBuiltinFunctionMap().Find({"perform_apex_config"});
            if(!config.ok())return config.error();
            if(auto configured=config->function(BuiltinArguments{{"perform_apex_config"},context});!configured.ok())return configured;
            if(!IsDefaultMountNamespaceReady())return android::base::Error()<<"Original default namespace not ready";
            std::fprintf(stderr,"APEX_ORIGINAL_DEFAULT_CONFIG_RETURNED REQUIRES_SERVICE_OPERATIONS\n");
            if(auto derived=DeriveOriginalClasspath(tick,true);!derived.ok())return derived;
            const std::vector<std::string> export_args={"load_exports","/data/system/environ/classpath"};
            auto loader=GetBuiltinFunctionMap().Find(export_args);
            if(!loader.ok())return loader.error();
            if(auto loaded=loader->function(BuiltinArguments{export_args,context});!loaded.ok())return loaded;
            if(auto evidence=ObserveOriginalApexNamespace();!evidence.ok())return evidence;
            std::fprintf(stderr,"PACKAGES_ORIGINAL_LOAD_EXPORTS_RETURNED NOT_JAVA_SERVICE_AVAILABILITY\n");
            if(auto flags=StartAconfig(tick);!flags.ok())return flags;
            // Reuse original init_user0 -> ExecVdcRebootOnFailure. A root
            // shell retains shell SID and is not the authorized VDC caller.
            // Attach our observation before the next reap tick, preserving
            // the original failure callback and transition/identity contract.
            const std::vector<std::string> storage_args={"/system/bin/vdc","--wait","cryptfs","init_user0"};
            if(services.FindService(storage_args,&Service::args))
                return android::base::Error()<<"Unexpected preexisting original init_user0 client";
            auto initialize=GetBuiltinFunctionMap().Find({"init_user0"});
            if(!initialize.ok())return initialize.error();
            if(auto initialized=initialize->function(BuiltinArguments{{"init_user0"},context});!initialized.ok())return initialized;
            auto* storage_peer=services.FindService(storage_args,&Service::args);
            if(!storage_peer || storage_peer->pid()<=0 || storage_peer->uid()!=0 || storage_peer->gid()!=0)
                return android::base::Error()<<"Original init_user0 client identity/entry missing";
            client_done_=false;client_ok_=false;
            storage_peer->AddReapCallback([this](const siginfo_t& info){
                client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;
                std::fprintf(stderr,"STORAGE_ORIGINAL_USER0_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
            });
            std::fprintf(stderr,"STORAGE_ORIGINAL_USER0_STARTED pid=%d ORIGINAL_BUILTIN_NOT_RETURNED\n",storage_peer->pid());
            if(auto waited=Wait(tick,[this]{return client_done_;},25);!waited.ok())return waited;
            if(!client_ok_)return android::base::Error()<<"Original vold init_user0 failed";
            std::fprintf(stderr,"STORAGE_ORIGINAL_USER0_RETURNED REQUIRES_FILES_AND_PERMISSION_PERSISTENCE\n");
            if(auto network=StartNetwork(tick);!network.ok())return network;
        } else {
            if(auto derived=DeriveOriginalClasspath(tick,false);!derived.ok())return derived;
        }
        return {};
    }
    android::base::Result<void> ObserveOriginalApexNamespace() {
        using namespace android::init;
        auto current=GetCurrentMountNamespace();
        if(!current.ok() || *current!=NS_DEFAULT || security_getenforce()!=expected_mode_)
            return android::base::Error()<<"APEX evidence namespace/mode mismatch";
        for(const auto& item:std::vector<std::pair<std::string,std::string>>{
                {"XML","/apex/apex-info-list.xml"},{"MOUNTS","/proc/self/mountinfo"}}) {
            std::string bytes;
            if(!android::base::ReadFileToString(item.second,&bytes) || bytes.empty() || bytes.size()>1048576)
                return android::base::Error()<<"Original namespace evidence unreadable: "<<item.second;
            std::fprintf(stderr,"APEX_NATIVE_%s_BEGIN pid=%d enforcing=%d bytes=%zu\n",item.first.c_str(),getpid(),expected_mode_,bytes.size());
            std::fwrite(bytes.data(),1,bytes.size(),stderr);
            if(bytes.back()!='\n')std::fputc('\n',stderr);
            std::fprintf(stderr,"APEX_NATIVE_%s_END\n",item.first.c_str());
        }
        std::string exports;
        if(!android::base::ReadFileToString("/data/system/environ/classpath",&exports))return android::base::Error()<<"Original exports unreadable for evidence";
        std::istringstream rows(exports);std::string row;
        while(std::getline(rows,row)) {
            std::istringstream parts(row);std::string operation,name,value;
            if(!(parts>>operation>>name>>value) || operation!="export")return android::base::Error()<<"Original export syntax invalid";
            std::istringstream paths(value);std::string path;
            while(std::getline(paths,path,':')) {
                if(path.rfind("/apex/",0)!=0 && path.rfind("/system/",0)!=0)return android::base::Error()<<"Original JAR path outside profile";
                struct stat info{};
                if(stat(path.c_str(),&info)!=0 || !S_ISREG(info.st_mode))return android::base::Error()<<"Original JAR missing: "<<path;
                std::fprintf(stderr,"APEX_NATIVE_JAR path=%s device=%llu inode=%llu size=%llu\n",path.c_str(),
                    static_cast<unsigned long long>(info.st_dev),static_cast<unsigned long long>(info.st_ino),static_cast<unsigned long long>(info.st_size));
            }
        }
        if(security_getenforce()!=expected_mode_)return android::base::Error()<<"APEX evidence mode changed";
        std::fprintf(stderr,"APEX_NATIVE_EVIDENCE_COMPLETE pid=%d enforcing=%d NS_DEFAULT_NOT_BINDER_OR_APK_ACCEPTANCE\n",getpid(),expected_mode_);
        return {};
    }
    android::base::Result<void> DeriveOriginalClasspath(const Tick& tick,bool parsed_by_original_apex_config) {
        using namespace android::init;
        auto& services=ServiceList::GetInstance();
        if(!parsed_by_original_apex_config) {
            auto parser=CreateParser(ActionManager::GetInstance(),services);
            auto parsed=parser.ParseConfigFile("/apex/com.android.sdkext/etc/derive_classpath.rc");
            if(!parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original derive_classpath RC rejected";
        }
        auto* derive=services.FindService("derive_classpath");
        if(!derive || derive->args()!=std::vector<std::string>{"/apex/com.android.sdkext/bin/derive_classpath"}
            || derive->uid()!=1000 || derive->gid()!=1000)
            return android::base::Error()<<"Original derive_classpath identity/entry missing";
        struct stat prior_export{};
        bool had_export=lstat("/data/system/environ/classpath",&prior_export)==0;
        if(!had_export && errno!=ENOENT)return android::base::ErrnoError()<<"Inspect original classpath destination";
        if(had_export && !S_ISREG(prior_export.st_mode))return android::base::Error()<<"Original classpath destination is not regular";
        client_done_=false;client_ok_=false;
        derive->AddReapCallback([this](const siginfo_t& info){
            client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;
            std::fprintf(stderr,"DERIVE_ORIGINAL_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
        });
        if(auto started=derive->ExecStart();!started.ok())return started;
        std::fprintf(stderr,"APEX_DERIVE_STARTED pid=%d uid=%u gid=%u NOT_CLASSPATH_READINESS\n",derive->pid(),derive->uid(),derive->gid());
        if(auto waited=Wait(tick,[this]{return client_done_;},25);!waited.ok())return waited;
        if(!client_ok_)return android::base::Error()<<"Original derive_classpath service failed";
        std::string exports;
        if(!android::base::ReadFileToString("/data/system/environ/classpath",&exports) || exports.empty())
            return android::base::Error()<<"Original classpath exports missing";
        struct stat actual_export{};
        if(lstat("/data/system/environ/classpath",&actual_export)!=0 || !S_ISREG(actual_export.st_mode)
            || actual_export.st_uid!=1000 || actual_export.st_gid!=1000 || (actual_export.st_mode&0022)!=0)
            return android::base::Error()<<"Original classpath output ownership rejected";
        if(had_export && prior_export.st_dev==actual_export.st_dev && prior_export.st_ino==actual_export.st_ino)
            return android::base::Error()<<"Original classpath atomic replacement not observed";
        std::fprintf(stderr,"DERIVE_ORIGINAL_OUTPUT uid=%u gid=%u mode=%o inode=%llu replaced=%d\n",
            actual_export.st_uid,actual_export.st_gid,actual_export.st_mode&0777,
            static_cast<unsigned long long>(actual_export.st_ino),had_export);
        std::fprintf(stderr,"DERIVE_ORIGINAL_RETURNED REQUIRES_EXPORTS_AND_JAVA_VERIFICATION\n");
        return {};
    }
    android::base::Result<void> StartAconfig(const Tick& tick) {
        using namespace android::init;
        auto& services=ServiceList::GetInstance();
        auto parser=CreateParser(ActionManager::GetInstance(),services);
        auto parsed=parser.ParseConfigFile("/system/etc/init/aconfigd.rc");
        if(!parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original aconfig RC rejected";
        const std::vector<std::vector<std::string>> stages={
            {"early_system_aconfigd_platform_init","/system/bin/aconfigd-system","early-platform-init"},
            {"system_aconfigd_platform_init","/system/bin/aconfigd-system","platform-init"},
            {"mainline_aconfigd_init","/apex/com.android.configinfrastructure/bin/aconfigd-mainline","init"}};
        for(const auto& stage:stages) {
            auto* job=services.FindService(stage[0]);
            const std::vector<std::string> expected(stage.begin()+1,stage.end());
            if(!job || job->args()!=expected)return android::base::Error()<<"Unexpected original aconfig initializer "<<stage[0];
            client_done_=false;client_ok_=false;
            auto actual_exit=std::make_shared<siginfo_t>();
            job->AddReapCallback([this,name=stage[0],actual_exit](const siginfo_t& info){
                *actual_exit=info;
                client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;
                std::fprintf(stderr,"ACONFIG_ORIGINAL_INIT_EXIT name=%s pid=%d code=%d status=%d\n",name.c_str(),info.si_pid,info.si_code,info.si_status);
            });
            if(auto started=job->ExecStart();!started.ok())return started;
            if(auto waited=Wait(tick,[this]{return client_done_;},20);!waited.ok())return waited;
            if(!client_ok_) {
                // Original init.Reap unblocks exec_start on nonzero exit when
                // the original RC has no reboot_on_failure/critical contract.
                // Preserve this observed partial result, never rewrite it as 0
                // or manufacture vendor flags. Unexpected failures still stop.
                std::string original_rc;
                bool nonfatal=android::base::ReadFileToString("/system/etc/init/aconfigd.rc",&original_rc) &&
                    original_rc.find("reboot_on_failure")==std::string::npos && original_rc.find("    critical")==std::string::npos;
                bool vendor_absent=access("/vendor/etc/aconfig/package.map",F_OK)!=0 && errno==ENOENT;
                bool actual_platform_files=true;
                for(const auto* container:{"system","system_ext","product"}) {
                    for(const auto* suffix:{".package.map",".flag.map"})
                        actual_platform_files=actual_platform_files && access((std::string("/metadata/aconfig/maps/")+container+suffix).c_str(),R_OK)==0;
                    actual_platform_files=actual_platform_files && access((std::string("/metadata/aconfig/boot/")+container+".val").c_str(),R_OK)==0;
                }
                bool known_partial=stage[0]=="system_aconfigd_platform_init" && actual_exit->si_code==CLD_EXITED &&
                    actual_exit->si_status==6 && nonfatal && vendor_absent && actual_platform_files;
                if(!known_partial)return android::base::Error()<<"Original aconfig initializer failed: "<<stage[0];
                std::fprintf(stderr,"ACONFIG_ORIGINAL_PLATFORM_PARTIAL exit=6 vendor_absent ORIGINAL_NONFATAL_EXEC_CONTRACT NOT_COMPLETE_FLAG_ACCEPTANCE\n");
            }
        }
        aconfig_system_=services.FindService("system_aconfigd_socket_service");
        aconfig_mainline_=services.FindService("mainline_aconfigd_socket_service");
        if(!aconfig_system_ || aconfig_system_->args()!=std::vector<std::string>{"/system/bin/aconfigd-system","start-socket"} ||
           !aconfig_mainline_ || aconfig_mainline_->args()!=std::vector<std::string>{"/apex/com.android.configinfrastructure/bin/aconfigd-mainline","start-socket"})
            return android::base::Error()<<"Original aconfig socket services absent or changed";
        for(auto* service:{aconfig_system_,aconfig_mainline_}) {
            service->AddReapCallback([this,service](const siginfo_t& info){
                bool clean=info.si_code==CLD_EXITED && info.si_status==0;
                if(service==aconfig_system_)aconfig_system_clean_exit_=clean;
                if(service==aconfig_mainline_)aconfig_mainline_clean_exit_=clean;
                std::fprintf(stderr,"ACONFIG_ORIGINAL_SOCKET_EXIT pid=%d code=%d status=%d ONESHOT_NOT_SOCKET_AVAILABILITY\n",info.si_pid,info.si_code,info.si_status);
                if(!closing_ && !clean)manager_failed_=true;
            });
            if(auto started=service->Start();!started.ok())return started;
        }
        std::fprintf(stderr,"SELECTED_ACONFIG_SYSTEM_STARTED pid=%d NOT_FLAG_OR_PERMISSION_ACCEPTANCE\n",aconfig_system_->pid());
        std::fprintf(stderr,"SELECTED_ACONFIG_MAINLINE_STARTED pid=%d NOT_FLAG_OR_PERMISSION_ACCEPTANCE\n",aconfig_mainline_->pid());
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
            // Original NetBpfLoad creates mainline_done before its successful
            // nonroot return. Android init has only mounton on fs_bpf: it is
            // not the map consumer. Do not give init new BPF traversal rights
            // for this added diagnostic. Keep original producer exit, platform
            // completion property and subsequent original netd operations.
            std::fprintf(stderr,"NETWORK_ORIGINAL_LOADER_EXIT0 name=%s REQUIRES_ORIGINAL_CONSUMER_OPERATIONS\n",name.c_str());
        }
        if(android::base::GetProperty("bpf.progs_loaded","")!="1")return android::base::Error()<<"Original platform loader did not publish completion";
        parsed=parser.ParseConfigFile("/vendor/etc/init/archtv-netd.rc");
        if(!parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original netd RC rejected";
        netd_=services.FindService("netd");
        if(!netd_ || netd_->args()!=std::vector<std::string>{"/system/bin/netd"})return android::base::Error()<<"Unexpected netd executable";
        netd_->AddReapCallback([this](const siginfo_t& info){std::fprintf(stderr,"NETWORK_NETD_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);if(!closing_)manager_failed_=true;});
        if(auto started=netd_->Start();!started.ok())return started;
        std::fprintf(stderr,"NETWORK_NETD_STARTED pid=%d NOT_REGISTERED\n",netd_->pid());
        std::fprintf(stderr,"SELECTED_NETD_STARTED pid=%d NOT_REGISTERED\n",netd_->pid());
        // Original AOSP excludes shell from netd_service discovery. Do not
        // mint a shell permission or treat a Linux diagnostic as a consumer.
        // Start is lifecycle admission only; keep reap/healthy guards and
        // require the authorized original system_server operation later.
        std::fprintf(stderr,"NETWORK_NETD_LIFECYCLE_ONLY REQUIRES_AUTHORIZED_ORIGINAL_CONSUMER NOT_REGISTERED_OR_OPERATION_ACCEPTANCE\n");
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
            const bool handoff=service==composer_ && wayland_channel_.get()>=0;
            if(handoff) {
                if(getenv("ARCHTV_WAYLAND_FD") || fcntl(wayland_channel_.get(),F_GETFD)!=FD_CLOEXEC)
                    return android::base::Error()<<"Wayland capability was not sealed for other services";
                if(setenv("ARCHTV_WAYLAND_FD",std::to_string(wayland_channel_.get()).c_str(),1)!=0 ||
                   fcntl(wayland_channel_.get(),F_SETFD,0)!=0)return android::base::ErrnoError()<<"Wayland HWC publication failed";
            }
            auto started=service->Start();
            if(handoff) {
                unsetenv("ARCHTV_WAYLAND_FD");
                if(fcntl(wayland_channel_.get(),F_SETFD,FD_CLOEXEC)!=0)return android::base::ErrnoError()<<"Wayland capability reseal failed";
                wayland_channel_.reset();
                std::fprintf(stderr,"WAYLAND_CAPABILITY_PUBLISHED_ONLY_HWC pid=%d parent_copy_closed=1 NOT_PROTOCOL_ACCEPTANCE\n",service->pid());
            }
            if(!started.ok())return started;
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
        surfaceflinger_->AddReapCallback([this](const siginfo_t& info) {
            std::fprintf(stderr,"MC3_SF_SERVICE_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
            if(!closing_)manager_failed_=true;
        });
        bootanimation_->AddReapCallback([this](const siginfo_t& info) {
            char requested[PROP_VALUE_MAX]={};
            __system_property_get("service.bootanim.exit",requested);
            bootanimation_clean_exit_=info.si_code==CLD_EXITED && info.si_status==0 && std::string(requested)=="1";
            std::fprintf(stderr,"MC3_BOOTANIMATION_EXIT pid=%d code=%d status=%d original_exit_request=%s clean=%d NOT_BOOT_OR_APK_ACCEPTANCE\n",
                info.si_pid,info.si_code,info.si_status,requested,bootanimation_clean_exit_);
            if(!closing_ && !bootanimation_clean_exit_)manager_failed_=true;
        });
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
    android::base::Result<void> ApplyLinuxApplicationView() {
        // Owner is already in the original default APEX mount namespace. Only
        // this cohort's view changes; original image/APK bytes remain untouched.
        auto ns=android::init::GetCurrentMountNamespace();
        if(!ns.ok() || *ns!=android::init::NS_DEFAULT)return android::base::Error()<<"APK profile requires actual default namespace";
        std::string data;
        if(!android::base::ReadFileToString("/vendor/etc/archtv-initial-apk-profile.tsv",&data) || data.size()>16384)
            return android::base::Error()<<"Missing or excessive selected APK view";
        // Original Bionic libcrypto export, not a replacement hash implementation.
        void* crypto=dlopen("libcrypto.so",RTLD_NOW|RTLD_LOCAL);
        if(!crypto)return android::base::Error()<<"Original libcrypto unavailable for APK identity";
        using Sha256=unsigned char*(*)(const unsigned char*,size_t,unsigned char*);
        auto sha256=reinterpret_cast<Sha256>(dlsym(crypto,"SHA256"));
        if(!sha256){dlclose(crypto);return android::base::Error()<<"Original SHA256 export absent";}
        struct CryptoOwner { void* value; ~CryptoOwner(){dlclose(value);} } crypto_owner{crypto};
        std::istringstream input(data);std::string line;size_t count=0;
        while(std::getline(input,line)) {
            std::istringstream fields(line);std::string package,dir,name,expected,extra;uint64_t bytes=0;unsigned uid=0,gid=0,directory_uid=0,directory_gid=0;
            if(!(fields>>package>>dir>>name>>expected>>bytes>>uid>>gid>>directory_uid>>directory_gid) || (fields>>extra) ||
               !(dir.rfind("/system/",0)==0 || dir.rfind("/apex/",0)==0) ||
               dir.find("..")!=std::string::npos || (dir.find("/priv-app/")==std::string::npos && dir.find("/app/")==std::string::npos) ||
               name.find('/')!=std::string::npos || name.size()<5 || name.substr(name.size()-4)!=".apk" ||
               expected.size()!=64 || bytes==0 || bytes>128*1024*1024)
                return android::base::Error()<<"Invalid selected APK directory entry";
            const auto apk=dir+"/"+name;
            struct stat file{},directory{};
            if(lstat(apk.c_str(),&file)!=0 || !S_ISREG(file.st_mode) || file.st_uid!=uid || file.st_gid!=gid || static_cast<uint64_t>(file.st_size)!=bytes ||
               lstat(dir.c_str(),&directory)!=0 || !S_ISDIR(directory.st_mode) || directory.st_uid!=directory_uid || directory.st_gid!=directory_gid)
                return android::base::Error()<<"Selected original APK identity metadata mismatch: "<<package;
            std::string original;
            if(!android::base::ReadFileToString(apk,&original) || original.size()!=bytes)
                return android::base::Error()<<"Cannot read selected original APK: "<<package;
            unsigned char digest[32];if(!sha256(reinterpret_cast<const unsigned char*>(original.data()),original.size(),digest))
                return android::base::Error()<<"Original SHA256 failed";
            std::string actual;const char hex[]="0123456789abcdef";
            for(auto v:digest){actual+=hex[v>>4];actual+=hex[v&15];}
            if(actual!=expected)return android::base::Error()<<"Original APK hash mismatch: "<<package;
            char* raw_context=nullptr;
            if(getfilecon(dir.c_str(),&raw_context)<0)return android::base::Error()<<"Missing original directory label";
            std::string context(raw_context);freecon(raw_context);
            // The shared host kernel defaults tmpfs to Linux's filesystem SID.
            // This fresh private view belongs to Android; retain the original
            // directory label atomically at mount, not a later relabel grant.
            if(context.empty() || context.find_first_of(",\"\r\n")!=std::string::npos)
                return android::base::Error()<<"Invalid original private APK mount context";
            const int enforcing=security_getenforce();
            if(enforcing<0)return android::base::ErrnoError()<<"Cannot determine private mount MAC mode";
            if(count==0 && enforcing==1) {
                // Check the boundary on the actual private target: admitting
                // Android fscontext must not admit a generic Linux mount.
                errno=0;
                const int unlabelled=mount("archtv-private-negative",dir.c_str(),"tmpfs",MS_RDONLY|MS_NOSUID|MS_NODEV|MS_NOEXEC,"size=4096,mode=0755");
                const int denied_errno=errno;
                if(unlabelled==0) {
                    const int cleanup=umount2(dir.c_str(),MNT_DETACH);
                    std::fprintf(stderr,"PRIVATE_APK_GENERIC_FS_UNEXPECTED cleanup=%d errno=%d\n",cleanup,cleanup<0?errno:0);
                    return android::base::Error()<<"Generic Linux private mount unexpectedly admitted";
                }
                if(denied_errno!=EACCES && denied_errno!=EPERM)
                    return android::base::Error()<<"Unexpected private mount negative result: "<<denied_errno;
                std::fprintf(stderr,"PRIVATE_APK_GENERIC_FS_DENIED errno=%d NOT_FULL_ISOLATION_ACCEPTANCE\n",denied_errno);
            }
            char directory_mode[16];std::snprintf(directory_mode,sizeof(directory_mode),"%o",static_cast<unsigned>(directory.st_mode&07777));
            const std::string mount_options="size=4096,mode="+std::string(directory_mode)+",uid="+std::to_string(directory_uid)+",gid="+std::to_string(directory_gid)+",fscontext=u:object_r:archtv_apk_view_fs:s0,rootcontext="+context;
            if(mount("archtv-initial-apk-profile",dir.c_str(),"tmpfs",MS_NOSUID|MS_NODEV|MS_NOEXEC,mount_options.c_str())!=0 ||
               mount(nullptr,dir.c_str(),nullptr,MS_REMOUNT|MS_RDONLY|MS_NOSUID|MS_NODEV|MS_NOEXEC,nullptr)!=0)
                return android::base::ErrnoError()<<"Private selected APK directory mount failed: "<<package;
            char* mounted_context=nullptr;
            if(getfilecon(dir.c_str(),&mounted_context)<0)return android::base::Error()<<"Cannot verify private APK root context";
            const bool same_context=context==mounted_context;freecon(mounted_context);
            if(!same_context)return android::base::Error()<<"Private APK root context changed: "<<package;
            struct stat mounted_directory{};
            if(lstat(dir.c_str(),&mounted_directory)!=0 || mounted_directory.st_uid!=directory_uid || mounted_directory.st_gid!=directory_gid ||
               (mounted_directory.st_mode&07777)!=(directory.st_mode&07777))
                return android::base::Error()<<"Private APK root ownership or mode changed: "<<package;
            struct statvfs view{};errno=0;
            if(access(apk.c_str(),F_OK)==0 || errno!=ENOENT || statvfs(dir.c_str(),&view)!=0 || !(view.f_flag&ST_RDONLY))
                return android::base::Error()<<"Selected APK remains available or view writable: "<<package;
            std::fprintf(stderr,"LINUX_APK_VIEW_EXCLUDED package=%s original=%s sha256=%s bytes=%llu readonly=1 uid=%u gid=%u mode=%o inode_context=%s NOT_FEATURE_COMPATIBILITY\n",package.c_str(),apk.c_str(),actual.c_str(),static_cast<unsigned long long>(bytes),mounted_directory.st_uid,mounted_directory.st_gid,static_cast<unsigned>(mounted_directory.st_mode&07777),context.c_str());
            ++count;
        }
        if(count!=7)return android::base::Error()<<"Unexpected selected initial APK view size";
        return {};
    }
    android::base::Result<void> RunOriginalSoftwareKeystore(const Tick& tick) {
        using namespace android::init;
        auto& services=ServiceList::GetInstance();
        auto parser=CreateParser(ActionManager::GetInstance(),services);
        for(const char* path:{"/vendor/etc/init/archtv-keymint-software.rc","/vendor/etc/init/archtv-keystore-software.rc"}) {
            auto parsed=parser.ParseConfigFile(path);
            if(!parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Software service RC rejected: "<<path;
        }
        keymint_=services.FindService("archtv-keymint-software");
        auto* keystore=services.FindService("archtv-keystore2");
        if(!keymint_ || keymint_->uid()!=AID_NOBODY || keymint_->args()!=std::vector<std::string>{"/archtv-android/archtv-keymint-software"} ||
           !keystore || keystore->uid()!=1017 || keystore->args()!=std::vector<std::string>{"/system/bin/keystore2","/data/misc/keystore"})
            return android::base::Error()<<"Software security identity/executable contract mismatch";
        for(auto* service:{keymint_,keystore})service->AddReapCallback([this](const siginfo_t& info){
            std::fprintf(stderr,"SOFTWARE_SECURITY_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
            if(!closing_)manager_failed_=true;
        });
        auto client=[&](const std::string& command)->android::base::Result<void> {
            auto temporary=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","shell","shell","--","/system/bin/sh","-c","umask 077; "+command});
            if(!temporary.ok())return temporary.error();
            auto* process=temporary->get();client_done_=false;client_ok_=false;
            process->AddReapCallback([this](const siginfo_t& info){client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;});
            services.AddService(std::move(*temporary));
            if(auto started=process->ExecStart();!started.ok())return started;
            if(auto waited=Wait(tick,[this]{return client_done_;},60);!waited.ok())return waited;
            if(!client_ok_)return android::base::Error()<<"Original software Binder client failed; inspect actual output";
            return {};
        };
        if(software_security_) {
            auto parsed=parser.ParseConfigFile("/vendor/etc/init/archtv-gatekeeper-software.rc");
            if(!parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original software GateKeeper RC rejected";
            gatekeeper_hal_=services.FindService("vendor.gatekeeper_nonsecure");
            if(!gatekeeper_hal_ || gatekeeper_hal_->uid()!=1000 || gatekeeper_hal_->args()!=std::vector<std::string>{"/archtv-android/archtv-gatekeeper-software"})return android::base::Error()<<"Original GateKeeper identity/entry mismatch";
            gatekeeper_hal_->AddReapCallback([this](const siginfo_t& info){
                std::fprintf(stderr,"SOFTWARE_GATEKEEPER_HAL_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
                if(!closing_)manager_failed_=true;
            });
            if(auto started=gatekeeper_hal_->Start();!started.ok())return started;
            std::fprintf(stderr,"SELECTED_GATEKEEPER_HAL_STARTED pid=%d NOT_REGISTERED_OR_AUTHENTICATION\n",gatekeeper_hal_->pid());
        }
        if(auto started=keymint_->Start();!started.ok())return started;
        std::fprintf(stderr,"SELECTED_KEYMINT_STARTED pid=%d\n",keymint_->pid());
        if(!software_security_) {
            if(auto observed=client("/archtv-android/archtv-keystore-client provider unused > /data/local/tmp/archtv-mc1/keymint-provider.txt 2>&1");!observed.ok())return observed;
        }
        keystore_=keystore;
        if(auto started=keystore_->Start();!started.ok())return started;
        std::fprintf(stderr,"SELECTED_KEYSTORE_STARTED pid=%d\n",keystore_->pid());
        if(software_security_) {
            // Functional startup uses original Keystore/gatekeeper/framework
            // consumers. Shell has no original KeyMint lookup permission.
            // Isolated Binder/JCA fixtures remain diagnostic profiles only.
            std::fprintf(stderr,"SECURITY_DAEMONS_LIFECYCLE_ONLY REQUIRES_ORIGINAL_CONSUMER_OPERATION NOT_CRYPTO_OR_AUTH_ACCEPTANCE\n");
            return {};
        }

        if(auto observed=client("/archtv-android/archtv-keystore-client write /data/local/tmp/archtv-mc1/keystore-ciphertext.bin > /data/local/tmp/archtv-mc1/keystore-component.txt 2>&1 && /archtv-android/archtv-keystore-client read /data/local/tmp/archtv-mc1/keystore-ciphertext.bin >> /data/local/tmp/archtv-mc1/keystore-component.txt 2>&1");!observed.ok())return observed;
        std::string java_profile;
        if(android::base::ReadFileToString("/vendor/etc/archtv-keystore-java",&java_profile)) {
            if(java_profile!="software-java-profile-v1\n")return android::base::Error()<<"Unknown Java Keystore profile";
            for(const char* directory:{"/apex/com.android.art","/apex/com.android.i18n","/apex/com.android.tzdata"}) {
                struct stat actual{};
                if(stat(directory,&actual)!=0 || !S_ISDIR(actual.st_mode))return android::base::ErrnoError()<<"Original Java APEX root absent: "<<directory;
            }
            const std::string entry="ANDROID_ART_ROOT=/apex/com.android.art ANDROID_I18N_ROOT=/apex/com.android.i18n ANDROID_TZDATA_ROOT=/apex/com.android.tzdata CLASSPATH=/vendor/framework/archtv-keystore-probe.jar /system/bin/app_process64 -Xmx128m -Xnoimage-dex2oat /system/bin --application org.archtv.keystoreprobe.OriginalJavaProviderProbe ";
            if(auto observed=client(entry+"write /data/local/tmp/archtv-mc1/java-ciphertext.bin > /data/local/tmp/archtv-mc1/keystore-java.txt 2>&1 && "+entry+"read /data/local/tmp/archtv-mc1/java-ciphertext.bin >> /data/local/tmp/archtv-mc1/keystore-java.txt 2>&1");!observed.ok())return observed;
        }
        std::fprintf(stderr,"KEYSTORE_COMPONENT_RETURNED REQUIRES_OUTPUT_VERIFICATION_NOT_APK_OR_MAC_ACCEPTANCE\n");
        return {};
    }
    android::base::Result<void> StartSelectedDisplay(const Tick& tick) {
        std::fprintf(stderr,"SELECTED_SHADER_PRIMING_PROPERTY actual=%s NO_RENDER_ACCEPTANCE\n",android::base::GetProperty("service.sf.prime_shader_cache", "unset").c_str());
        using namespace android::init;
        if(apex_requested_) { if(auto view=ApplyLinuxApplicationView();!view.ok())return view; }
        auto& services=ServiceList::GetInstance();
        auto parser=CreateParser(ActionManager::GetInstance(),services);
        // Original upstream SystemSuspend keeps its own real wakelock counter
        // when Linux owns host sleep. No /sys/power controls are exposed here.
        if(apex_requested_) {
            // Reuse original security daemons and their original UID/rlimit
            // contracts. Registration is not proof of a working HAL or keys.
            for(const char* path:{"/system/etc/init/gatekeeperd.rc","/system/etc/init/keystore2.rc"}) {
                if(software_security_ && std::string(path)=="/system/etc/init/keystore2.rc")continue;
                auto parsed=parser.ParseConfigFile(path);
                if(!parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original security RC rejected: "<<path;
            }
            gatekeeper_=services.FindService("gatekeeperd");
            if(!software_security_)keystore_=services.FindService("keystore2");
            else if(!keystore_ || !keystore_->IsRunning())return android::base::Error()<<"Software Keystore stopped before platform integration";
            if(!gatekeeper_ || gatekeeper_->args()!=std::vector<std::string>{"/system/bin/gatekeeperd","/data/misc/gatekeeper"} || gatekeeper_->uid()!=1000 ||
               !keystore_ || keystore_->args()!=std::vector<std::string>{"/system/bin/keystore2","/data/misc/keystore"} || keystore_->uid()!=1017)
                return android::base::Error()<<"Original security daemon contract mismatch";
            for(auto* service:{gatekeeper_,keystore_}) {
                if(software_security_ && service==keystore_)continue;
                service->AddReapCallback([this](const siginfo_t& info) {
                    std::fprintf(stderr,"ORIGINAL_SECURITY_DAEMON_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
                    if(!closing_)manager_failed_=true;
                });
                if(auto started=service->Start();!started.ok())return started;
                std::fprintf(stderr,"ORIGINAL_SECURITY_DAEMON_STARTED name=%s pid=%d NOT_HAL_OR_KEY_ACCEPTANCE\n",service->name().c_str(),service->pid());
                if(software_security_ && service==gatekeeper_)std::fprintf(stderr,"SELECTED_GATEKEEPER_STARTED pid=%d NOT_AUTHENTICATION\n",service->pid());
            }
            auto memory_parsed=parser.ParseConfigFile("/system/etc/init/lmkd.rc");
            if(!memory_parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original lmkd RC rejected";
            lmkd_=services.FindService("lmkd");
            if(!lmkd_ || lmkd_->args()!=std::vector<std::string>{"/system/bin/lmkd"})return android::base::Error()<<"Unexpected original lmkd executable";
            lmkd_->AddReapCallback([this](const siginfo_t& info){std::fprintf(stderr,"SELECTED_LMKD_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);if(!closing_)manager_failed_=true;});
            if(auto started=lmkd_->Start();!started.ok())return started;
            std::fprintf(stderr,"SELECTED_LMKD_STARTED pid=%d NOT_SOCKET_OR_PRESSURE_ACCEPTANCE\n",lmkd_->pid());
            // Complete original storage/codec/overlay backends. The media APEX
            // profile was registered by original perform_apex_config already.
            for(const char* path:{"/system/etc/init/storaged.rc","/system/etc/init/idmap2d.rc"}) {
                auto parsed=parser.ParseConfigFile(path);
                if(!parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original storage/overlay RC rejected: "<<path;
            }
            storaged_=services.FindService("storaged");
            idmap_=services.FindService("idmap2d");
            swcodec_=services.FindService("media.swcodec");
            if(!storaged_ || storaged_->args()!=std::vector<std::string>{"/system/bin/storaged"} || storaged_->uid()!=AID_ROOT || storaged_->gid()!=AID_PACKAGE_INFO ||
               !idmap_ || idmap_->args()!=std::vector<std::string>{"/system/bin/idmap2d"} || idmap_->uid()!=AID_SYSTEM || idmap_->gid()!=AID_SYSTEM ||
               !swcodec_ || swcodec_->args()!=std::vector<std::string>{"/apex/com.android.media.swcodec/bin/mediaswcodec"} || swcodec_->uid()!=AID_MEDIA_CODEC || swcodec_->gid()!=AID_CAMERA)
                return android::base::Error()<<"Original storage/codec/overlay profile mismatch";
            for(auto* service:{storaged_,idmap_,swcodec_}) {
                service->AddReapCallback([this](const siginfo_t& info){
                    std::fprintf(stderr,"ORIGINAL_STORAGE_BACKEND_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);
                    if(!closing_)manager_failed_=true;
                });
                if(auto started=service->Start();!started.ok())return started;
            }
            std::fprintf(stderr,"SELECTED_STORAGED_STARTED pid=%d NOT_STORAGE_ACCEPTANCE\n",storaged_->pid());
            std::fprintf(stderr,"SELECTED_IDMAP_STARTED pid=%d NOT_OVERLAY_OPERATION_ACCEPTANCE\n",idmap_->pid());
            std::fprintf(stderr,"SELECTED_SWCODEC_STARTED pid=%d NOT_MEDIA_PLAYBACK_ACCEPTANCE\n",swcodec_->pid());
            // Linux admits native audio when an actual provider is configured.
            // AudioService keeps its original unavailable/recovery behavior;
            // absence of a HAL is never reported as working playback.
            const bool native_audio_configured = services.FindService("vendor.audio-hal-aidl") ||
                services.FindService("vendor.audio-hal") || services.FindService("vendor.audio-hal-4-0-msd");
            if (native_audio_configured) {
                // Parse the intact audio daemon contract; do not substitute a Java
                // manager whose native policy/mixer dependencies are missing.
                auto audio_parsed=parser.ParseConfigFile("/system/etc/init/audioserver.rc");
                if(!audio_parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Original audioserver RC rejected";
                audioserver_=services.FindService("audioserver");
                if(!audioserver_ || audioserver_->args()!=std::vector<std::string>{"/system/bin/audioserver"})return android::base::Error()<<"Unexpected original audioserver executable";
                audioserver_->AddReapCallback([this](const siginfo_t& info){std::fprintf(stderr,"SELECTED_AUDIOSERVER_EXIT pid=%d code=%d status=%d\n",info.si_pid,info.si_code,info.si_status);if(!closing_)manager_failed_=true;});
                if(auto started=audioserver_->Start();!started.ok())return started;
                std::fprintf(stderr,"SELECTED_AUDIOSERVER_STARTED pid=%d NOT_AUDIO_OR_POLICY_ACCEPTANCE\n",audioserver_->pid());
            } else {
                std::fprintf(stderr,"SELECTED_NATIVE_AUDIO_DEFERRED no_original_HAL_configured NOT_AUDIO_AVAILABILITY\n");
            }
            auto* artd=services.FindInterface("aidl/artd");
            if(!artd || artd!=services.FindService("artd") ||
               artd->args()!=std::vector<std::string>{"/apex/com.android.art/bin/artd"} ||
               artd->uid()!=1082 || artd->gid()!=1082 ||
               !(artd->flags() & SVC_ONESHOT) || !(artd->flags() & SVC_DISABLED))
                return android::base::Error()<<"Original lazy artd profile rejected";
            artd->AddReapCallback([this](const siginfo_t& info){
                const bool idle=info.si_code==CLD_EXITED && info.si_status==0;
                std::fprintf(stderr,"SELECTED_ARTD_EXIT pid=%d code=%d status=%d clean=%d\n",info.si_pid,info.si_code,info.si_status,idle);
                if(!closing_ && !idle)manager_failed_=true;
            });
            if(auto admitted=AdmitLinuxLazyInterface(epoll_,"aidl/artd");!admitted.ok())return admitted;
            std::fprintf(stderr,"SELECTED_ARTD_LAZY_ADMITTED NOT_RUNNING_OR_REGISTERED\n");
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
                "umask 077; if /system/bin/setprop ctl.interface_start aidl/artd_pre_reboot > /data/local/tmp/archtv-mc1/unadmitted-artd-control.txt 2>&1; then exit 97; fi; i=0; while [ $$i -lt 12 ]; do /system/bin/service check android.hardware.health.IHealth/default > /data/local/tmp/archtv-mc1/health-query.txt 2>&1; /system/bin/service check stats > /data/local/tmp/archtv-mc1/stats-query.txt 2>&1; if /system/bin/grep -qx 'Service stats: found' /data/local/tmp/archtv-mc1/stats-query.txt && /system/bin/grep -qx 'Service android.hardware.health.IHealth/default: found' /data/local/tmp/archtv-mc1/health-query.txt; then /system/bin/dumpsys android.hardware.health.IHealth/default > /data/local/tmp/archtv-mc1/health-dump.txt 2>&1; exit $$?; fi; i=$$((i+1)); /system/bin/sleep 1; done; exit 1"});
            if(!health_client.ok())return health_client.error();
            auto* health_peer=health_client->get();health_peer->AddReapCallback([this](const siginfo_t& info){client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;});services.AddService(std::move(*health_client));
            if(auto started=health_peer->ExecStart();!started.ok())return started;
            if(auto waited=Wait(tick,[this]{return client_done_;},16);!waited.ok())return waited;
            if(!client_ok_)return android::base::Error()<<"Original IHealth query/dump failed";
            auto* rejected=services.FindInterface("aidl/artd_pre_reboot");
            if(!rejected || rejected->IsRunning())return android::base::Error()<<"Unadmitted original pre-reboot artd unexpectedly running or absent";
            std::fprintf(stderr,"LINUX_UNADMITTED_ARTD_CONTROL_REJECTED original_profile_present=1 running=0 NOT_MAC_ACCEPTANCE\n");
            std::fprintf(stderr,"HEALTH_ORIGINAL_BINDER_CLIENT_RETURNED REQUIRES_VALUE_VERIFICATION\n");
            auto zygote_parsed=parser.ParseConfigFile("/vendor/etc/init/archtv-app-zygote.rc");
            if(!zygote_parsed.ok() || parser.parse_error_count()!=0)return android::base::Error()<<"Application zygote profile rejected";
            zygote_=services.FindService("zygote");
            if(!zygote_ || zygote_->args().empty() || zygote_->args().front()!="/system/bin/app_process64")return android::base::Error()<<"Unexpected zygote executable";
            for(const auto& argument:zygote_->args())if(argument=="--start-system-server")return android::base::Error()<<"Full SystemServer startup prohibited";
            // Real Linux-owned single-64-bit application Zygote profile, not readiness.
            // ART GetSupportedInstructionSets reads this original build configuration.
            if(zygote_->args()!=std::vector<std::string>{"/system/bin/app_process64","-Xzygote","/system/bin","--zygote","--socket-name=zygote"})
                return android::base::Error()<<"Unsupported Linux application Zygote profile";
            for(const auto& [name,value]:std::vector<std::pair<std::string,std::string>>{
                {"ro.product.cpu.abilist","x86_64"},{"ro.product.cpu.abilist64","x86_64"},
                {"ro.product.cpu.abilist32",""}}) {
                if(android::base::GetProperty(name,"")!=value)
                    return android::base::Error()<<"Declared ABI conflicts with actual single-64-bit Zygote: "<<name;
            }
            std::fprintf(stderr,"SELECTED_ABI_PROFILE actual_original_properties=x86_64 abi32_empty=1 NOT_32BIT_OR_ARM_COMPATIBILITY\n");
            const auto configured_zygote=android::base::GetProperty("ro.zygote","");
            if(!configured_zygote.empty() && configured_zygote!="zygote64")
                return android::base::Error()<<"Existing ro.zygote conflicts with actual selected profile";
            if(configured_zygote.empty() && !android::base::SetProperty("ro.zygote","zygote64"))
                return android::base::Error()<<"Cannot configure original ART Zygote contract";
            if(android::base::GetProperty("ro.zygote","")!="zygote64")
                return android::base::Error()<<"Original ART Zygote configuration readback mismatch";
            std::fprintf(stderr,"SELECTED_ZYGOTE_CONFIGURATION ro.zygote=zygote64 NOT_RUNNING\n");
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
        if(apex_requested_ && !selected_requested_) {
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
            std::fprintf(stderr,"NETWORK_NETD_ROOT_OPERATION_NOT_RETESTED_NOT_CURRENT_OPERATION_ACCEPTANCE\n");
            client_done_=false;client_ok_=false;
            auto package_client=Service::MakeTemporaryOneshotService({"exec","u:r:shell:s0","shell","shell","--",
                "/system/bin/sh","-c","umask 077; i=0; while [ $$i -lt 120 ]; do /system/bin/service check package > /data/local/tmp/archtv-mc1/package-query.txt 2>&1; /system/bin/service check activity > /data/local/tmp/archtv-mc1/activity-query.txt 2>&1; /system/bin/service check mount > /data/local/tmp/archtv-mc1/mount-query.txt 2>&1; if /system/bin/grep -qx 'Service package: found' /data/local/tmp/archtv-mc1/package-query.txt && /system/bin/grep -qx 'Service activity: found' /data/local/tmp/archtv-mc1/activity-query.txt && /system/bin/grep -qx 'Service mount: found' /data/local/tmp/archtv-mc1/mount-query.txt; then /system/bin/cmd package list packages --user 0 > /data/local/tmp/archtv-mc1/package-list.txt 2>&1; /system/bin/cmd package path --user 0 net.gsantner.markor > /data/local/tmp/archtv-mc1/markor-path.txt 2>&1; if /system/bin/grep -q '^package:/data/app/' /data/local/tmp/archtv-mc1/markor-path.txt && /system/bin/grep -qx 'Status: ok' /data/local/tmp/archtv-mc1/markor-launch.txt && /system/bin/test -s /data/local/tmp/archtv-mc1/markor-sf.png; then /system/bin/dumpsys package net.gsantner.markor > /data/local/tmp/archtv-mc1/markor-dump.txt 2>&1; exit $$?; fi; fi; i=$$((i+1)); /system/bin/sleep 1; done; exit 1"});
            if(!package_client.ok())return package_client.error();
            auto* peer=package_client->get();
            peer->AddReapCallback([this](const siginfo_t& info){client_done_=true;client_ok_=info.si_code==CLD_EXITED && info.si_status==0;});
            services.AddService(std::move(*package_client));
            if(auto result=peer->ExecStart();!result.ok())return result;
            if(auto result=Wait(tick,[this]{return client_done_;},180);!result.ok())return result;
            if(!client_ok_)return android::base::Error()<<"Original package client did not observe installed AND launched Markor; inspect original outputs separately";
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
    android::init::Epoll* epoll_;
    const bool& stop_;
    const int expected_mode_;
    const bool hardware_requested_;
    const bool graphics_requested_;
    const bool surfaceflinger_requested_;
    const bool selected_requested_;
    const bool apex_requested_;
    bool apex_bootstrap_prepared_=false;
    android::init::Service* aconfig_system_=nullptr;
    android::init::Service* aconfig_mainline_=nullptr;
    android::init::Service* lmkd_=nullptr;
    android::init::Service* audioserver_=nullptr;
    android::init::Service* storaged_=nullptr;
    android::init::Service* swcodec_=nullptr;
    android::init::Service* idmap_=nullptr;
    android::base::unique_fd wayland_channel_;
    android::init::Service* logd_=nullptr;
    android::init::Service* logcat_=nullptr;
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
    android::init::Service* gatekeeper_hal_=nullptr;
    bool software_security_=false;
    android::init::Service* gatekeeper_=nullptr;
    android::init::Service* keystore_=nullptr;
    android::init::Service* keymint_=nullptr;
    bool aconfig_system_clean_exit_=false,aconfig_mainline_clean_exit_=false;
    bool bootanimation_started_=false,bootanimation_clean_exit_=false;
    bool missing_done_=false,missing_ok_=false;
    bool apex_cancelled_=false,vold_cancelled_=false;
    bool apex_activation_observed_=false,apex_clean_exit_=false;
    bool active_=false,closing_=false,manager_failed_=false,client_done_=false,client_ok_=false;
};
}
