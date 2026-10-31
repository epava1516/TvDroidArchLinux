// Loader/initializer regression only, not a graphics device or APK test.
#include <dlfcn.h>
#include <stdio.h>
int main() {
 void* h=dlopen("/probe/libhwc2on1adapter.so",RTLD_NOW|RTLD_LOCAL);
 if(!h){fprintf(stderr,"dlopen: %s\n",dlerror());return 2;}
 puts("ORIGINAL_ADAPTER_DLOPEN_NOW_OK");
 if(dlclose(h)!=0){fprintf(stderr,"dlclose: %s\n",dlerror());return 3;}
 puts("ORIGINAL_ADAPTER_DLCLOSE_OK");return 0;
}
