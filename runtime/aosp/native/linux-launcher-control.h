#pragma once
// Blocking original-launcher RPC. Call only from a dedicated bounded worker,
// never the compositor/Wayland/render thread. No mutation retry or shell exec.
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <poll.h>
#include <unistd.h>
#include <array>
#include <algorithm>
#include <chrono>
#include <cstddef>
#include <cstdint>
#include <cstring>
#include <cerrno>
#include <string>
#include <vector>
#include <set>
#include <utility>
#include <mutex>
#include <condition_variable>
#include <thread>
#include <deque>

namespace archtv::aosp {
struct LauncherEntry {std::string component,label,category;};
enum class LauncherStatus {Returned,Rejected,BackendFailure,Unavailable,Indeterminate};
struct LauncherReply {
    LauncherStatus status=LauncherStatus::Unavailable;
    std::vector<LauncherEntry> entries;
    std::string detail;
    // A launch RPC return never asserts presentation or application lifecycle.
    bool launch_request_returned=false;
};
namespace launcher_wire {
constexpr uint32_t kMagic=0x41544c31,kMaximumResponse=262144;
inline bool Utf8(const std::string& text) {
    const auto* b=reinterpret_cast<const unsigned char*>(text.data());
    for(size_t i=0;i<text.size();) {
        unsigned c=b[i++];if(c<0x80)continue;
        unsigned count=0,value=0,minimum=0;
        if(c>=0xc2 && c<=0xdf){count=1;value=c&31;minimum=0x80;}
        else if(c>=0xe0 && c<=0xef){count=2;value=c&15;minimum=0x800;}
        else if(c>=0xf0 && c<=0xf4){count=3;value=c&7;minimum=0x10000;}
        else return false;
        if(count>text.size()-i)return false;
        while(count--){unsigned n=b[i++];if((n&0xc0)!=0x80)return false;value=(value<<6)|(n&63);}
        if(value<minimum || value>0x10ffff || (value>=0xd800 && value<=0xdfff))return false;
    }
    return true;
}
inline bool Component(const std::string& value) {
    auto slash=value.find('/');
    return !value.empty() && value.size()<=1024 && Utf8(value)
        && slash!=std::string::npos && slash>0 && slash+1<value.size()
        && value.find('/',slash+1)==std::string::npos
        && value.find('\0')==std::string::npos;
}
class Reader {
    const std::vector<uint8_t>& bytes_;size_t offset_=0;
 public:
    explicit Reader(const std::vector<uint8_t>& bytes):bytes_(bytes){}
    bool Word(uint32_t& value){if(bytes_.size()-offset_<4)return false;uint32_t wire;std::memcpy(&wire,bytes_.data()+offset_,4);offset_+=4;value=ntohl(wire);return true;}
    bool Text(std::string& value,uint32_t bound){uint32_t length;if(!Word(length)||length>bound||length>bytes_.size()-offset_)return false;value.assign(reinterpret_cast<const char*>(bytes_.data()+offset_),length);offset_+=length;return Utf8(value);}
    bool End() const{return offset_==bytes_.size();}
};
inline bool Catalog(const std::vector<uint8_t>& bytes,std::vector<LauncherEntry>& entries) {
    entries.clear();if(bytes.size()>kMaximumResponse)return false;
    Reader reader(bytes);uint32_t count;if(!reader.Word(count)||count>512)return false;
    std::vector<LauncherEntry> parsed;std::set<std::string> seen;
    for(uint32_t i=0;i<count;++i) {
        LauncherEntry entry;
        if(!reader.Text(entry.component,1024)||!reader.Text(entry.label,4096)||!reader.Text(entry.category,128)
            || !Component(entry.component)||!seen.insert(entry.component).second
            || (entry.category!="android.intent.category.LAUNCHER" && entry.category!="android.intent.category.LEANBACK_LAUNCHER"))return false;
        parsed.push_back(std::move(entry));
    }
    if(!reader.End())return false;
    entries=std::move(parsed);return true;
}
using Deadline=std::chrono::steady_clock::time_point;
inline bool Wait(int fd,short events,Deadline deadline) {
    for(;;) {
        auto remaining=std::chrono::duration_cast<std::chrono::milliseconds>(deadline-std::chrono::steady_clock::now()).count();
        if(remaining<=0){errno=ETIMEDOUT;return false;}
        pollfd p{fd,events,0};int result=poll(&p,1,static_cast<int>(remaining>10000?10000:remaining));
        if(result<0 && errno==EINTR)continue;
        if(result>0 && (p.revents&events))return true;
        if(result==0)errno=ETIMEDOUT;
        return false;
    }
}
inline bool Transfer(int fd,void* bytes,size_t length,bool sending,Deadline deadline,size_t& transferred) {
    transferred=0;
    while(transferred<length) {
        if(!Wait(fd,sending?POLLOUT:POLLIN,deadline))return false;
        auto* data=static_cast<char*>(bytes)+transferred;
        ssize_t n=sending?send(fd,data,length-transferred,MSG_DONTWAIT|MSG_NOSIGNAL):recv(fd,data,length-transferred,MSG_DONTWAIT);
        if(n<0 && (errno==EINTR || errno==EAGAIN))continue;
        if(n<=0)return false;
        transferred+=static_cast<size_t>(n);
    }
    return true;
}
}
inline LauncherReply OriginalLauncherRequest(uint32_t operation,uint32_t sequence,const std::string& component={},
    launcher_wire::Deadline deadline=std::chrono::steady_clock::now()+std::chrono::seconds(10)) {
    using namespace launcher_wire;
    LauncherReply reply;
    if(sequence==0 || (operation!=1 && operation!=2) || (operation==1 && !component.empty())
        || (operation==2 && !Component(component))) {
        reply.status=LauncherStatus::Rejected;reply.detail="Invalid local launcher request";return reply;
    }
    const bool launch=operation==2;
    if(deadline<=std::chrono::steady_clock::now()){reply.detail="Launcher request expired before connection";return reply;}
    int fd=socket(AF_UNIX,SOCK_STREAM|SOCK_NONBLOCK|SOCK_CLOEXEC,0);
    if(fd<0){reply.detail="Launcher socket unavailable";return reply;}
    struct Close {int fd;~Close(){close(fd);}} closer{fd};
    deadline=std::min(deadline,std::chrono::steady_clock::now()+std::chrono::seconds(10));
    sockaddr_un address{};address.sun_family=AF_UNIX;const char name[]="archtv-launcher-control-v1";
    std::memcpy(address.sun_path+1,name,sizeof(name)-1);
    int result=connect(fd,reinterpret_cast<sockaddr*>(&address),offsetof(sockaddr_un,sun_path)+sizeof(name));
    if(result<0) {
        if(errno!=EINPROGRESS || !Wait(fd,POLLOUT,deadline)){reply.detail="Original launcher not connected";return reply;}
        int error=0;socklen_t length=sizeof(error);
        if(getsockopt(fd,SOL_SOCKET,SO_ERROR,&error,&length)!=0 || error!=0){reply.detail="Original launcher connect failed";return reply;}
    }
    ucred peer{};socklen_t length=sizeof(peer);char context[256]{};socklen_t context_length=sizeof(context)-1;
    if(getsockopt(fd,SOL_SOCKET,SO_PEERCRED,&peer,&length)!=0 || length!=sizeof(peer) || peer.uid!=1000 || peer.gid!=1000
        || getsockopt(fd,SOL_SOCKET,SO_PEERSEC,context,&context_length)!=0 || context_length>=sizeof(context)
        || std::strcmp(context,"u:object_r:archtv_input_channel:s0")!=0) {
        reply.detail="Original launcher peer authentication failed";return reply;
    }
    std::array<uint32_t,4> header{htonl(kMagic),htonl(sequence),htonl(operation),htonl(static_cast<uint32_t>(component.size()))};
    size_t transferred=0;
    auto uncertain=[&](){reply.status=launch?LauncherStatus::Indeterminate:LauncherStatus::Unavailable;reply.detail="Launcher transport ended; never automatically retry launch";return reply;};
    if(!Transfer(fd,header.data(),sizeof(header),true,deadline,transferred)) {
        if(transferred==0){reply.detail="Launcher request not written";return reply;}
        return uncertain();
    }
    if(!component.empty() && !Transfer(fd,const_cast<char*>(component.data()),component.size(),true,deadline,transferred))return uncertain();
    if(!Transfer(fd,header.data(),sizeof(header),false,deadline,transferred))return uncertain();
    for(auto& word:header)word=ntohl(word);
    if(header[0]!=kMagic || header[1]!=sequence || header[2]>2 || header[3]>kMaximumResponse)return uncertain();
    std::vector<uint8_t> body(header[3]);
    if(!body.empty() && !Transfer(fd,body.data(),body.size(),false,deadline,transferred))return uncertain();
    if(header[2]!=0) {
        reply.detail.assign(body.begin(),body.end());
        if(!Utf8(reply.detail))return uncertain();
        reply.status=header[2]==1?LauncherStatus::Rejected:LauncherStatus::BackendFailure;return reply;
    }
    if(operation==1) {
        if(!Catalog(body,reply.entries))return uncertain();
    } else {
        reply.detail.assign(body.begin(),body.end());if(!Utf8(reply.detail))return uncertain();
        reply.launch_request_returned=true;
    }
    reply.status=LauncherStatus::Returned;return reply;
}
// One worker owns all original RPCs. The display thread only submits/polls;
// queued time counts against the same absolute ten-second operation deadline.
class LinuxLauncherWorker {
 public:
    struct Completion {uint32_t sequence,operation;LauncherReply reply;};
 private:
    struct Request {uint32_t sequence,operation;std::string component;launcher_wire::Deadline deadline;};
    std::mutex mutex_;std::condition_variable wake_;
    std::deque<Request> pending_;std::deque<Completion> finished_;
    bool stop_=false;uint32_t last_sequence_=0;std::thread thread_;
    void Run() {
        for(;;) {
            Request request;
            {
                std::unique_lock<std::mutex> lock(mutex_);
                wake_.wait(lock,[&]{return stop_ || (!pending_.empty() && finished_.size()<4);});
                if(stop_)return;
                request=std::move(pending_.front());pending_.pop_front();
            }
            auto reply=OriginalLauncherRequest(request.operation,request.sequence,request.component,request.deadline);
            {
                std::lock_guard<std::mutex> lock(mutex_);
                if(stop_)return;
                finished_.push_back({request.sequence,request.operation,std::move(reply)});
            }
        }
    }
 public:
    LinuxLauncherWorker():thread_([this]{Run();}){}
    LinuxLauncherWorker(const LinuxLauncherWorker&)=delete;
    LinuxLauncherWorker& operator=(const LinuxLauncherWorker&)=delete;
    ~LinuxLauncherWorker(){
        {std::lock_guard<std::mutex> lock(mutex_);stop_=true;pending_.clear();}
        wake_.notify_one();thread_.join();
    }
    bool Submit(uint32_t operation,uint32_t sequence,std::string component={}) {
        if(sequence==0 || (operation!=1 && operation!=2) || (operation==1 && !component.empty())
            || (operation==2 && !launcher_wire::Component(component)))return false;
        std::lock_guard<std::mutex> lock(mutex_);
        if(stop_ || sequence<=last_sequence_ || pending_.size()>=4)return false;
        pending_.push_back({sequence,operation,std::move(component),std::chrono::steady_clock::now()+std::chrono::seconds(10)});
        last_sequence_=sequence;wake_.notify_one();return true;
    }
    std::vector<Completion> Poll() {
        std::lock_guard<std::mutex> lock(mutex_);std::vector<Completion> replies;
        while(!finished_.empty()){replies.push_back(std::move(finished_.front()));finished_.pop_front();}
        wake_.notify_one();return replies;
    }
};

}
