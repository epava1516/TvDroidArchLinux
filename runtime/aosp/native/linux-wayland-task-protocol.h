#pragma once
#include <array>
#include <cstdint>
#include <arpa/inet.h>

namespace archtv::aosp {
struct TaskInputResponse {
    bool ack=false;
    uint32_t sequence=0,value=0,activity_type=0;
    int32_t display=-1,task=-1;
};
// V2 response is exactly eight network-order words. Task state is separate
// from input ACK and never supplies an input-success or APK-readiness result.
inline bool DecodeTaskInputResponse(const std::array<uint32_t,8>& wire,TaskInputResponse& out) {
    std::array<uint32_t,8> v{};
    for(std::size_t i=0;i<v.size();++i)v[i]=ntohl(wire[i]);
    if(v[0]!=0x41545232 || v[2]==0 || v[7]!=0)return false;
    TaskInputResponse result;result.sequence=v[2];result.value=v[3];
    if(v[1]==1) {
        if(v[3]>1 || v[4]!=0 || v[5]!=0 || v[6]!=0)return false;
        result.ack=true;
    } else if(v[1]==2) {
        if(v[3]>2)return false;
        result.display=static_cast<int32_t>(v[4]);result.task=static_cast<int32_t>(v[5]);result.activity_type=v[6];
        if(v[3]==0) {
            if(result.display!=-1 || result.task!=-1 || v[6]!=0)return false;
        } else if(result.display<0 || result.task<0 || v[6]>6 || ((v[3]==2)!=(v[6]==2)))return false;
    } else return false;
    out=result;return true;
}
}
