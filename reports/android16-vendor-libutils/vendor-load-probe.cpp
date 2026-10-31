// Namespace diagnostic only; no HWC device/service is provided or opened.
#include <android/dlext.h>
#include <vndksupport/linker.h>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>
extern "C" android_namespace_t* android_get_exported_namespace(const char*);
int main() {
 auto* ns=android_get_exported_namespace("sphal");
 printf("SPHAL_NAMESPACE_VISIBLE=%d\n",ns!=nullptr);
 if(!ns)return 4; // no fallback to open namespace allowed in this diagnostic
 void* h=android_load_sphal_library("/vendor/lib64/libhwc2on1adapter.so",RTLD_NOW);
 if(!h){
  puts("ORIGINAL_SPHAL_LOAD_FAILED");
  // Original wrapper consumes dlerror while logging. Repeat direct equivalent
  // namespace call only to retrieve its loader diagnostic, not to relax isolation.
  android_dlextinfo info={};info.flags=ANDROID_DLEXT_USE_NAMESPACE;info.library_namespace=ns;
  void* diagnostic=android_dlopen_ext("/vendor/lib64/libhwc2on1adapter.so",RTLD_NOW,&info);
  if(!diagnostic){const char* error=dlerror();printf("DIRECT_SPHAL_ERROR=%s\n",error?error:"unavailable");}
  else{puts("DIRECT_SPHAL_RETRY_UNEXPECTEDLY_SUCCEEDED");dlclose(diagnostic);return 5;}
  return 2;
 }
 puts("ORIGINAL_SPHAL_LOAD_OK");
 const char* required[]={"libhwc2on1adapter.so","libutils.so","libcutils.so","libhardware.so","libbase.so","libc++.so"};
 bool found[6]={};FILE* maps=fopen("/proc/self/maps","re");if(!maps)return 6;
 char line[4096];while(fgets(line,sizeof(line),maps)){
  for(int i=0;i<6;i++){char path[256];snprintf(path,sizeof(path),"/vendor/lib64/%s",required[i]);
   if(!found[i]&&strstr(line,path)){found[i]=true;printf("MAPPED_VENDOR_LIB=%s\n",path);}
  }
 }
 fclose(maps);for(int i=0;i<6;i++)if(!found[i]){printf("MISSING_VENDOR_MAPPING=%s\n",required[i]);return 7;}

 if(android_unload_sphal_library(h)!=0)return 3;
 puts("ORIGINAL_SPHAL_UNLOAD_OK");return 0;
}
