#include <android/log.h>
#include <cstdio>
static void observe(const struct __android_log_message* m) {
    std::fprintf(stderr,"ANDROID_LOG priority=%d tag=%s message=%s\n",m->priority,m->tag?m->tag:"",m->message?m->message:"");
}
__attribute__((constructor)) static void install() {
    __android_log_set_logger(observe);
    std::fprintf(stderr,"DIAGNOSTIC_LOG_OBSERVER_INSTALLED\n");
}
