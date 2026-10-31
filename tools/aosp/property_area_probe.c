/* Controlled target-only bootstrap diagnostic. Calls original Bionic APIs.
 * C signatures are checked against the pinned libc headers/API source; no host
 * headers, glibc objects, property implementation, APK or server are substituted.
 * Loaded by the original linker before the launcher main; always exits here.
 */
#ifndef __ANDROID__
#error This diagnostic must be compiled for Android Bionic
#endif
typedef __SIZE_TYPE__ size_t;
typedef __PTRDIFF_TYPE__ ssize_t;
typedef __UINT32_TYPE__ uint32_t;
typedef struct prop_info prop_info;
extern unsigned getuid(void), geteuid(void), getgid(void), getegid(void);
extern int open(const char*, int, ...), close(int), dprintf(int, const char*, ...);
extern ssize_t read(int, void*, size_t);
extern void _exit(int) __attribute__((noreturn));
extern char *getenv(const char*), *strchr(const char*, int);
extern size_t strlen(const char*);
extern int strcmp(const char*, const char*);
extern int *__errno(void);
extern int __system_property_area_init(void);
extern int __system_property_add(const char*, unsigned, const char*, unsigned);
extern int __system_property_foreach(void (*)(const prop_info*, void*), void*);
extern void __system_property_read_callback(const prop_info*, void (*)(void*, const char*, const char*, uint32_t), void*);
extern int __system_property_set(const char*, const char*);
static unsigned seen;
static void value(void* cookie, const char* name, const char* text, uint32_t serial) {
  (void)cookie; (void)serial;
  dprintf(1, "PROPERTY %s=%s\n", name, text); ++seen;
}
static void entry(const prop_info* pi, void* cookie) {
  __system_property_read_callback(pi, value, cookie);
}
__attribute__((constructor)) static void probe(void) {
  const char* mode = getenv("ARCHTV_PROPERTY_PROBE_MODE");
  if (!mode) _exit(90);
  dprintf(1, "IDENTITY ruid=%u euid=%u rgid=%u egid=%u\n", getuid(), geteuid(), getgid(), getegid());
  if (!strcmp(mode, "writer")) {
    if (getuid() || geteuid() || getgid() || getegid()) _exit(91);
    *__errno() = 0;
    int result = __system_property_area_init();
    dprintf(1, "AREA_INIT result=%d errno=%d\n", result, *__errno());
    if (result) _exit(10);
    int fd = open("/system/build.prop", 0);
    if (fd < 0) _exit(11);
    char input[65536]; size_t total = 0; ssize_t count;
    while ((count = read(fd, input + total, sizeof(input)-1-total)) > 0) {
      total += (size_t)count;
      if (total == sizeof(input)-1) _exit(12);
    }
    close(fd);
    if (count < 0) _exit(13);
    input[total] = 0;
    unsigned added = 0;
    for (char* line = input; line;) {
      char* next = strchr(line, '\n');
      if (next) *next++ = 0;
      if (*line && *line != '#') {
        char* equal = strchr(line, '=');
        if (!equal) _exit(14);
        *equal++ = 0;
        result = __system_property_add(line, (unsigned)strlen(line), equal, (unsigned)strlen(equal));
        if (result) {
          dprintf(1, "ADD_FAILED name=%s result=%d errno=%d\n", line, result, *__errno());
          _exit(15);
        }
        ++added;
      }
      line = next;
    }
    dprintf(1, "ADDED count=%u\n", added);
  } else if (!strcmp(mode, "reader")) {
    if (getuid() != 10000 || geteuid() != 10000 || getgid() != 10000 || getegid() != 10000) _exit(92);
    *__errno() = 0;
    int fd = open("/dev/__properties__/properties_serial", 2);
    dprintf(1, "OPEN_WRITE fd=%d errno=%d\n", fd, *__errno());
    if (fd >= 0) { close(fd); _exit(16); }
    *__errno() = 0;
    int result = __system_property_set("archtv.probe.absent_service", "1");
    dprintf(1, "SET_WITHOUT_SERVER result=%d errno=%d\n", result, *__errno());
    if (result == 0) _exit(17);
  } else _exit(93);
  int result = __system_property_foreach(entry, 0);
  dprintf(1, "FOREACH result=%d count=%u\n", result, seen);
  _exit(result == 0 && seen ? 0 : 18);
}
