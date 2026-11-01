// Linux/glibc adapter. Bionic stays in the subsequent executable, never this ABI.
// The factory must supply an immutable labelled filesystem and the actor role.
#define _GNU_SOURCE
#include <selinux/selinux.h>
#include <errno.h>
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <sys/statvfs.h>
#include <sys/vfs.h>
#include <linux/magic.h>
#include <unistd.h>

extern char **environ;
static const char actor[] = "linux.system_u:archtv_launcher_r:archtv_launcher:s0";
static const char target[] = "u:r:init:s0";
static const char image[] = "/archtv/bin/property-coordinator";
static int refused(const char *stage) {
    fprintf(stderr, "LINUX_EXEC_CONTEXT_REFUSED stage=%s; no child startup\n", stage);
    return 78;
}

int main(int argc, char **argv) {
    int apex = argc == 2 && !strcmp(argv[1], "--apex-integration");
    int selected = argc == 2 && !strcmp(argv[1], "--display-integration");
    int surfaceflinger = selected || (argc == 2 && !strcmp(argv[1], "--surfaceflinger-integration"));
    int graphics = surfaceflinger || (argc == 2 && !strcmp(argv[1], "--graphics-integration"));
    int hardware = graphics || (argc == 2 && !strcmp(argv[1], "--hardware-integration"));
    int integration = apex || hardware || (argc == 2 && !strcmp(argv[1], "--permissive-integration"));
    if (argc != 1 && !integration) return 64;
    int enforcing = security_getenforce();
    struct statfs selinux_fs;
    // Linux is_selinux_enabled also tests /etc configuration presence. Check
    // genuine kernel state here, not that Linux installation heuristic.
    if (statfs("/sys/fs/selinux", &selinux_fs) || selinux_fs.f_type != SELINUX_MAGIC ||
        enforcing < 0 || (!integration && enforcing != 1))
        return refused("SELinux-mode");
    const char *classes[] = {"process", "binder", "property_service", "service_manager"};
    for (size_t i = 0; i < sizeof(classes)/sizeof(classes[0]); ++i)
        if (!string_to_security_class(classes[i])) return refused("policy-classes");
    char *context = NULL;
    if (getcon_raw(&context) < 0) return refused("source-context");
    int matches = context && !strcmp(context, actor);
    freecon(context);
    if (!matches) return refused("source-identity");
    int fd = open(image, O_RDONLY | O_NOFOLLOW | O_CLOEXEC);
    if (fd < 0) return refused("coordinator-open");
    struct stat st;
    struct statvfs fs;
    if (fstat(fd, &st) || fstatvfs(fd, &fs) || !S_ISREG(st.st_mode) ||
        st.st_uid != 0 || st.st_gid != 0 || (st.st_mode & 07777) != 0700 ||
        st.st_nlink != 1 || !(fs.f_flag & ST_RDONLY)) return refused("immutable-inode");
    context = NULL;
    if (fgetfilecon_raw(fd, &context) < 0) return refused("coordinator-label");
    matches = context && !strcmp(context, "u:object_r:init_exec:s0");
    freecon(context);
    if (!matches) return refused("coordinator-label");
    // The original setter asks the kernel to validate/write the exec attribute.
    // It does not assign current SID; do not add selinuxfs write grants just for
    // a redundant pre-validation or mistake a library cache for kernel readback.
    if (setexeccon_raw(target) < 0) return refused("setexeccon");
    fprintf(stderr, "LINUX_EXEC_CONTEXT_REQUESTED source=%s target=%s enforcing=%d NOT_STARTUP\n", actor, target, enforcing);
    char *child_args[] = {(char *)image, apex ? "--mc1-apex-integration" : selected ? "--mc3-display-integration" : surfaceflinger ? "--mc3-surfaceflinger-integration" : graphics ? "--mc3-graphics-integration" : hardware ? "--mc1-hardware-integration" : integration ? "--mc1-integration" : NULL, NULL};
    fexecve(fd, child_args, environ);
    return refused("fexecve");
}
