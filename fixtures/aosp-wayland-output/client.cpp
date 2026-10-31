#include "linux-wayland-output.h"
#include <cstdio>
#include <cstdlib>
#include <cerrno>
#include <vector>
#include <unistd.h>
#include <cstring>
int main(int argc,char** argv) {
    if(argc!=2)return 64;
    char* end=nullptr;long fd=std::strtol(argv[1],&end,10);
    if(!end || *end || fd<3 || fd>65535)return 64;
    FILE* status=std::fopen("/proc/self/status","r");if(!status)return 1;
    char line[1024];int checked=0;
    while(std::fgets(line,sizeof(line),status)) {
        if(!std::strncmp(line,"Uid:",4) || !std::strncmp(line,"Gid:",4)) {
            unsigned a,b,c,d;if(std::sscanf(line+4,"%u %u %u %u",&a,&b,&c,&d)!=4 || a!=10000 || b!=10000 || c!=10000 || d!=10000)return 1;
            std::printf("NATIVE_POSTEXEC %s",line);++checked;
        } else if(!std::strncmp(line,"CapEff:",7) || !std::strncmp(line,"CapPrm:",7) || !std::strncmp(line,"CapInh:",7) || !std::strncmp(line,"CapAmb:",7)) {
            if(std::strtoull(line+7,nullptr,16)!=0)return 1;std::printf("NATIVE_POSTEXEC %s",line);++checked;
        } else if(!std::strncmp(line,"NoNewPrivs:",11)) {
            if(std::strtol(line+11,nullptr,10)!=1)return 1;std::printf("NATIVE_POSTEXEC %s",line);++checked;
        }
    }
    std::fclose(status);if(checked!=7)return 1;
    FILE* context=std::fopen("/proc/self/attr/current","r");if(!context)return 1;
    size_t count=std::fread(line,1,sizeof(line)-1,context);std::fclose(context);if(!count)return 1;line[count]=0;std::printf("NATIVE_POSTEXEC_SID %s\n",line);
    archtv::aosp::LinuxWaylandOutput output;
    if(!output.Connect(static_cast<int>(fd))){std::perror("WAYLAND_CONNECT_FAILED");return 1;}
    int w=output.width(),h=output.height();
    if(w<=0 || h<=0 || size_t(w)*h>16777216)return 1;
    std::vector<uint32_t> image(size_t(w)*h);
    for(int frame=0;frame<3;++frame) {
        for(int y=0;y<h;++y)for(int x=0;x<w;++x)
            image[size_t(y)*w+x]=frame<2?0xff203040u:((x<w/2)?(y<h/2?0xffff0000u:0xff0000ffu):(y<h/2?0xff00ff00u:0xffffffffu));
        if(!output.CommitCpu(image.data(),w,h,w)){std::perror("WAYLAND_COMMIT_FAILED");return 1;}
    }
    std::printf("BIONIC_WAYLAND_THREE_CALLBACKS width=%d height=%d NO_NATIVE_FENCE_OR_APK_ACCEPTANCE\n",w,h);std::fflush(stdout);
    sleep(8);return 0;
}
