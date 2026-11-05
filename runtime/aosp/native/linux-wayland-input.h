#pragma once
// Linux seat adapter, not an Android input dispatcher implementation.
#include <input/KeyLayoutMap.h>
#include <input/Keyboard.h>
#include <arpa/inet.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <unistd.h>
#include <array>
#include <deque>
#include <map>
#include <cstdio>
#include <android/log.h>
#include <cstring>
#include <cerrno>
#include <cstddef>
#include <chrono>
#include <algorithm>
#include <functional>
#include <utility>
#include "linux-wayland-task-protocol.h"
namespace archtv::aosp {
class LinuxWaylandInput {
    int fd_=-1,meta_=0;uint32_t sequence_=0,last_ack_=0;size_t offset_=0,ack_bytes_=0;
    std::array<uint32_t,8> ack_{};
    uint32_t last_task_sequence_=0;
    std::function<void(const TaskInputResponse&)> task_focus_;
    std::chrono::steady_clock::time_point next_connect_{};
    std::shared_ptr<android::KeyLayoutMap> layout_;
    std::map<uint32_t,int32_t> held_;
    std::deque<std::array<uint32_t,10>> pending_;
    bool touch_=false;int x_=0,y_=0;
    std::chrono::steady_clock::time_point progress_;
    void Disconnect(){if(fd_>=0)close(fd_);fd_=-1;pending_.clear();offset_=ack_bytes_=0;held_.clear();meta_=0;touch_=false;}
    bool Connect(){
        if(fd_>=0)return true;
        int fd=socket(AF_UNIX,SOCK_STREAM|SOCK_NONBLOCK|SOCK_CLOEXEC,0);if(fd<0)return false;
        sockaddr_un addr{};addr.sun_family=AF_UNIX;const char name[]="archtv-wayland-input-v2";
        memcpy(addr.sun_path+1,name,sizeof(name)-1);
        if(connect(fd,reinterpret_cast<sockaddr*>(&addr),offsetof(sockaddr_un,sun_path)+sizeof(name))!=0){close(fd);return false;}
        ucred peer{};socklen_t n=sizeof(peer);char context[128]{};socklen_t length=sizeof(context)-1;
        if(getsockopt(fd,SOL_SOCKET,SO_PEERCRED,&peer,&n)!=0 || peer.uid!=1000 ||
           getsockopt(fd,SOL_SOCKET,SO_PEERSEC,context,&length)!=0 || std::strcmp(context,"u:object_r:archtv_input_channel:s0")){
            std::fprintf(stderr,"WAYLAND_INPUT_PEER_REJECTED\n");close(fd);return false;
        }
        fd_=fd;last_ack_=sequence_;last_task_sequence_=0;progress_=std::chrono::steady_clock::now();std::fprintf(stderr,"WAYLAND_INPUT_PEER_AUTHENTICATED pid=%d uid=%d context=%s protocol=2\n",peer.pid,peer.uid,context);return true;
    }
    void Emit(uint32_t type,uint32_t code,uint32_t action,uint32_t scan=0){
        if(!Connect()){std::fprintf(stderr,"WAYLAND_INPUT_NOT_DELIVERED errno=%d\n",errno);Disconnect();return;}
        if(pending_.size()>=64){std::fprintf(stderr,"WAYLAND_INPUT_QUEUE_OVERFLOW disconnect\n");Disconnect();return;}
        if(sequence_==UINT32_MAX){Disconnect();sequence_=0;return;}
        std::array<uint32_t,10> packet{0x41544932,type,++sequence_,code,action,uint32_t(meta_),scan,uint32_t(x_),uint32_t(y_),0};
        if(sequence_==last_ack_+1)progress_=std::chrono::steady_clock::now();
        for(auto& v:packet)v=htonl(v);pending_.push_back(packet);Pump();
    }
 public:
    void SetTaskFocusHandler(std::function<void(const TaskInputResponse&)> handler){task_focus_=std::move(handler);}
    ~LinuxWaylandInput(){Disconnect();}
    void Pump(){
        if(fd_<0) {
            auto now=std::chrono::steady_clock::now();if(now<next_connect_)return;
            next_connect_=now+std::chrono::milliseconds(500);if(!Connect())return;
        }
        while(!pending_.empty()){
            auto* bytes=reinterpret_cast<const char*>(pending_.front().data());
            ssize_t n=send(fd_,bytes+offset_,40-offset_,MSG_DONTWAIT|MSG_NOSIGNAL);
            if(n<0 && (errno==EAGAIN||errno==EINTR))break;
            if(n<=0){Disconnect();return;}offset_+=size_t(n);
            if(offset_==40){offset_=0;pending_.pop_front();}
        }
        // Bound each monitor turn even if a peer produces many task changes.
        for(unsigned turn=0;turn<64;++turn){
            ssize_t n=recv(fd_,reinterpret_cast<char*>(ack_.data())+ack_bytes_,sizeof(ack_)-ack_bytes_,MSG_DONTWAIT);
            if(n<0 && (errno==EAGAIN||errno==EINTR))break;
            if(n<=0){Disconnect();return;}
            ack_bytes_+=size_t(n);
            if(ack_bytes_==sizeof(ack_)){
                TaskInputResponse response;ack_bytes_=0;
                if(!DecodeTaskInputResponse(ack_,response)){std::fprintf(stderr,"WAYLAND_INPUT_INVALID_RESPONSE\n");Disconnect();return;}
                if(response.ack) {
                    uint32_t seq=response.sequence,result=response.value;
                    if(seq!=last_ack_+1 || seq>sequence_){std::fprintf(stderr,"WAYLAND_INPUT_INVALID_ACK\n");Disconnect();return;}
                    last_ack_=seq;progress_=std::chrono::steady_clock::now();
                    std::fprintf(stderr,"WAYLAND_INPUT_ORIGINAL_DISPATCH seq=%u accepted=%u\n",seq,result);
                    if(!result){__android_log_print(ANDROID_LOG_ERROR,"ArchTVInput","DISPATCH_REJECTED seq=%u",seq);Disconnect();return;}
                } else {
                    if(response.sequence!=last_task_sequence_+1){std::fprintf(stderr,"WAYLAND_TASK_SEQUENCE_INVALID\n");Disconnect();return;}
                    last_task_sequence_=response.sequence;
                    std::fprintf(stderr,"WAYLAND_TASK_AUTHENTICATED_STATE seq=%u kind=%u display=%d task=%d activity_type=%u NOT_APK_READINESS\n",response.sequence,response.value,response.display,response.task,response.activity_type);
                    if(task_focus_)task_focus_(response);
                    // Task notifications must not mask an outstanding input ACK timeout.
                }
            }
        }
        // The display/Wayland thread may have been busy while a valid ACK
        // reached the socket. Drain it before testing inactivity; never drop
        // acknowledged input merely because Pump was scheduled late.
        if(sequence_!=last_ack_ && std::chrono::steady_clock::now()-progress_>std::chrono::seconds(5)){
            __android_log_print(ANDROID_LOG_ERROR,"ArchTVInput","ACK_TIMEOUT sent=%u ack=%u pending=%zu",sequence_,last_ack_,pending_.size());
            std::fprintf(stderr,"WAYLAND_INPUT_ACK_TIMEOUT disconnect\n");Disconnect();return;
        }
    }
    void Key(uint32_t scan,bool down){
        if(!layout_){auto result=android::KeyLayoutMap::load("/vendor/usr/keylayout/Generic.kl");if(!result.ok()){std::fprintf(stderr,"WAYLAND_INPUT_ORIGINAL_KEYLAYOUT_UNAVAILABLE\n");return;}layout_=*result;}
        int32_t code=0;uint32_t flags=0;
        if(layout_->mapKey(scan,0,&code,&flags)!=android::OK || code==0){std::fprintf(stderr,"WAYLAND_INPUT_UNMAPPED_SCAN %u\n",scan);return;}
        if(down){if(held_.count(scan))return;held_[scan]=code;}else if(!held_.erase(scan))return;
        meta_=android::updateMetaState(code,down,meta_);Emit(1,code,down?0:1,scan);
    }
    void Move(double x,double y){x_=int(std::clamp(x,0.0,8192.0)*1000);y_=int(std::clamp(y,0.0,8192.0)*1000);if(touch_)Emit(2,0,2);}
    void Button(uint32_t button,bool down){if(button!=0x110 || down==touch_)return;touch_=down;Emit(2,0,down?0:1);}
    void Reset(){
        auto keys=held_;for(auto [scan,code]:keys)Key(scan,false);
        if(touch_){touch_=false;Emit(2,0,3);}meta_=0;
    }
};
}
