// Read-only observation of genuine original AOSP libselinux under the current kernel.
#include <selinux/selinux.h>
#include <selinux/avc.h>
#include <cstdio>
#include <initializer_list>
#include <cerrno>
#include <unistd.h>
int main() {
    std::printf("ORIGINAL_SELINUX enabled=%d enforce=%d uid=%u\n",is_selinux_enabled(),security_getenforce(),getuid());
    char* context=nullptr;errno=0;int rc=getcon(&context);int error=errno;
    std::printf("GETCON rc=%d errno=%d context=%s\n",rc,rc<0?error:0,context?context:"<absent>");
    if(context)freecon(context);
    context=nullptr;errno=0;rc=getfilecon("/system/bin/servicemanager",&context);error=errno;
    std::printf("GETFILECON rc=%d errno=%d context=%s\n",rc,rc<0?error:0,context?context:"<absent>");
    if(context)freecon(context);
    errno=0;rc=selinux_status_open(0);error=errno;
    std::printf("ORIGINAL_STATUS_OPEN_NO_FALLBACK rc=%d errno=%d\n",rc,rc<0?error:0);
    if(rc==0)std::printf("ORIGINAL_STATUS_UPDATED rc=%d\n",selinux_status_updated());
    // Android exports open/updated; mapping lifetime ends with this diagnostic process.
    for(const char* name:{"process","binder","service_manager","property_service"})
        std::printf("ORIGINAL_CLASS name=%s value=%u\n",name,string_to_security_class(name));
    std::puts("READ_ONLY_INSPECTION_COMPLETED_NOT_RUNTIME_READINESS");
    return 0;
}
