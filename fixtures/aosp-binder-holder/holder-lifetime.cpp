#include <cstdint>
#include <cstdio>
#include <cstdlib>
#include <dlfcn.h>
#include <set>
int main(int argc,char** argv) {
    if(argc!=2)return 2;
    void* library=dlopen(argv[1],RTLD_NOW|RTLD_LOCAL);
    if(!library){std::fprintf(stderr,"%s\n",dlerror());return 3;}
    using Create=int64_t(*)(void*,void*);using Finalizer=int64_t(*)(void*,void*);using Release=void(*)(void*);
    auto create=reinterpret_cast<Create>(dlsym(library,"Java_android_os_Binder_getNativeBBinderHolder"));
    auto getFinalizer=reinterpret_cast<Finalizer>(dlsym(library,"Java_android_os_Binder_getNativeFinalizer"));
    if(!create || !getFinalizer)return 4;
    auto finalizer=getFinalizer(nullptr,nullptr);if(!finalizer)return 5;
    auto release=reinterpret_cast<Release>(static_cast<uintptr_t>(finalizer));
    for(int cycle=0;cycle<100;cycle++) {
        std::set<int64_t> live;
        for(int i=0;i<128;i++) {
            auto value=create(nullptr,nullptr);
            if(!value || !live.insert(value).second)return 6;
        }
        if(getFinalizer(nullptr,nullptr)!=finalizer)return 7;
        for(auto value:live)release(reinterpret_cast<void*>(static_cast<uintptr_t>(value)));
    }
    if(dlclose(library))return 8;
    std::puts("NATIVE_BINDER_HOLDER_OK objects=12800 cycles=100");return 0;
}
