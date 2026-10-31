#pragma once
// One Bionic coordinator per process. The Epoll must outlive this object and
// be disposed after Close; restart uses a fresh process, as the upstream FD is cached.
#include "epoll.h"
#include "service.h"
#include "sigchld_handler.h"
#include <android-base/logging.h>
#include <android-base/unique_fd.h>
#include <sys/signalfd.h>
#include <fcntl.h>
#include <signal.h>
#include <unistd.h>
#include <functional>
#include <set>
namespace archtv::aosp {
class LinuxChildReaper {
 public:
    using Observer = std::function<void(const std::set<pid_t>&)>;
    explicit LinuxChildReaper(android::init::Epoll& loop, Observer observer = {})
        : loop_(loop), observer_(std::move(observer)) {}
    LinuxChildReaper(const LinuxChildReaper&) = delete;
    LinuxChildReaper& operator=(const LinuxChildReaper&) = delete;
    ~LinuxChildReaper() { auto result=Close();if(!result.ok())LOG(ERROR)<<result.error(); }
    android::base::Result<void> Attach() {
        if(claimed_)return android::base::Error()<<"Original SIGCHLD descriptor already claimed";
        if(sigprocmask(SIG_SETMASK,nullptr,&old_mask_)!=0)return android::base::ErrnoError()<<"Read signal mask";
        mask_saved_=true;claimed_=true;
        fd_.reset(android::init::Service::GetSigchldFd()); // Upstream enforces ThreadCount()==1.
        int flags=fcntl(fd_.get(),F_GETFL);
        if(flags<0 || fcntl(fd_.get(),F_SETFL,flags|O_NONBLOCK)<0)return android::base::ErrnoError()<<"Nonblocking SIGCHLD descriptor";
        auto result=loop_.RegisterHandler(fd_.get(),[this]{Drain();});
        registered_=result.ok();return result;
    }
    android::base::Result<void> Close() {
        if(registered_){auto result=loop_.UnregisterHandler(fd_.get());if(!result.ok())return result;registered_=false;}
        fd_.reset();
        if(mask_saved_){if(sigprocmask(SIG_SETMASK,&old_mask_,nullptr)!=0)return android::base::ErrnoError()<<"Restore coordinator signal mask";mask_saved_=false;}
        return {};
    }
    bool healthy() const {return healthy_;}
 private:
    void Drain() {
        bool signaled=false;
        for(int turn=0;turn<64;++turn){
            signalfd_siginfo info{};ssize_t n=read(fd_.get(),&info,sizeof(info));
            if(n<0 && errno==EINTR)continue;
            if(n<0 && errno==EAGAIN)break;
            if(n!=static_cast<ssize_t>(sizeof(info)) || info.ssi_signo!=SIGCHLD){healthy_=false;return;}
            signaled=true;
        }
        if(signaled){auto reaped=android::init::ReapAnyOutstandingChildren();if(observer_)observer_(reaped);}
    }
    inline static bool claimed_=false; // Serialized coordinator calls only.
    android::init::Epoll& loop_;
    Observer observer_;
    android::base::unique_fd fd_;
    sigset_t old_mask_{};
    bool mask_saved_=false,registered_=false,healthy_=true;
};
}
