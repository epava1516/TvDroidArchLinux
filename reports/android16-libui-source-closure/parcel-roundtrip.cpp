// Diagnostic regression using original generated codecs and original NDK Parcel.
// No service, hardware buffer, GPU, HWC device or APK compatibility is implemented here.
#include <aidl/android/hardware/common/NativeHandle.h>
#include <aidl/android/hardware/graphics/common/PlaneLayout.h>
#include <android/binder_parcel.h>
#include <sys/mman.h>
#include <unistd.h>
#include <fcntl.h>
#include <errno.h>
#include <stdio.h>
#include <string.h>
using aidl::android::hardware::common::NativeHandle;
using aidl::android::hardware::graphics::common::PlaneLayout;
using aidl::android::hardware::graphics::common::PlaneLayoutComponent;
int main() {
 setvbuf(stdout,nullptr,_IONBF,0);
 const char payload[]="archtv-original-aidl-fd";
 int fd=memfd_create("archtv-aidl-regression",MFD_CLOEXEC);
 if(fd<0||write(fd,payload,sizeof(payload))!=sizeof(payload))return 2;
 NativeHandle original;original.fds.emplace_back(fd);original.ints={-7,0,2147483647};
 AParcel* parcel=AParcel_create();if(!parcel)return 3;
 if(original.writeToParcel(parcel)!=STATUS_OK||AParcel_setDataPosition(parcel,0)!=STATUS_OK)return 4;
 NativeHandle decoded;if(decoded.readFromParcel(parcel)!=STATUS_OK||decoded.ints!=original.ints||decoded.fds.size()!=1)return 5;
 int decoded_fd=decoded.fds[0].get();original.fds.clear();errno=0;
 if(fcntl(fd,F_GETFD)!=-1||errno!=EBADF)return 6;
 AParcel_delete(parcel);char observed[sizeof(payload)]={};
 if(pread(decoded_fd,observed,sizeof(observed),0)!=sizeof(observed)||memcmp(observed,payload,sizeof(payload)))return 7;
 decoded.fds.clear();errno=0;if(fcntl(decoded_fd,F_GETFD)!=-1||errno!=EBADF)return 8;
 puts("NATIVE_HANDLE_FD_OWNERSHIP_ROUNDTRIP_OK");
 PlaneLayout input;PlaneLayoutComponent component;component.type.name="archtv.diagnostic.layout";component.type.value=37;component.offsetInBits=0;component.sizeInBits=8;input.components.push_back(component);
 input.offsetInBytes=64;input.sampleIncrementInBits=32;input.strideInBytes=256;input.widthInSamples=64;input.heightInSamples=32;input.totalSizeInBytes=8192;input.horizontalSubsampling=1;input.verticalSubsampling=1;
 parcel=AParcel_create();if(!parcel)return 9;
 if(input.writeToParcel(parcel)!=STATUS_OK||AParcel_setDataPosition(parcel,0)!=STATUS_OK)return 10;
 PlaneLayout output;if(output.readFromParcel(parcel)!=STATUS_OK||!(output==input))return 11;AParcel_delete(parcel);
 puts("PLANE_LAYOUT_NESTED_METADATA_ROUNDTRIP_OK");
 const char* required[]={"/data/android.hardware.common-V2-ndk.so","/data/android.hardware.graphics.common-V7-ndk.so"};bool found[2]={};FILE* maps=fopen("/proc/self/maps","re");if(!maps)return 12;char line[4096];
 while(fgets(line,sizeof(line),maps))for(int i=0;i<2;i++)if(!found[i]&&strstr(line,required[i])){found[i]=true;printf("MAPPED_SOURCE_CODEC=%s\n",required[i]);}
 fclose(maps);return found[0]&&found[1]?0:13;
}
