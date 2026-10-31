#include <unistd.h>
#include <sys/syscall.h>
#include <sys/stat.h>
#include <cerrno>
#include <cstdlib>
#include <cstring>
#include <cstdio>
extern "C" int fsync(int fd) {
 const char* mode=getenv("ARCHTV_TEST_FSYNC_FAILURE");
 struct stat st{};
 if(mode && fstat(fd,&st)==0 && ((strcmp(mode,"file")==0 && S_ISREG(st.st_mode)) || (strcmp(mode,"directory")==0 && S_ISDIR(st.st_mode)))) {
  std::fprintf(stderr,"INJECTED_FSYNC_EIO kind=%s\n",mode);errno=EIO;return -1;
 }
 return static_cast<int>(syscall(__NR_fsync,fd));
}
