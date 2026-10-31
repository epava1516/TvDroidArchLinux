#include "linux-child-reaper.h"
#include <android-base/logging.h>
#include <sys/wait.h>
#include <dirent.h>
#include <cstdio>
#include <cstring>
#include <chrono>
#define REQUIRE(x) do{if(!(x)){std::fprintf(stderr,"FAILED %s errno=%d\n",#x,errno);return 1;}}while(0)
static size_t fds(){DIR* d=opendir("/proc/self/fd");if(!d)return 0;size_t n=0;while(auto* e=readdir(d))if(std::strcmp(e->d_name,".")&&std::strcmp(e->d_name,".."))++n;closedir(d);return n;}
int main(int,char** argv){
 android::base::InitLogging(argv,android::base::StderrLogger);
 sigset_t before{},after{};REQUIRE(sigprocmask(SIG_SETMASK,nullptr,&before)==0);size_t baseline=fds();std::set<pid_t> observed;
 {
  android::init::Epoll loop;REQUIRE(loop.Open().ok());archtv::aosp::LinuxChildReaper children(loop,[&](const std::set<pid_t>& p){observed.insert(p.begin(),p.end());});REQUIRE(children.Attach().ok());
  pid_t good=fork();REQUIRE(good>=0);if(good==0){execl("/system/bin/getprop","getprop","ro.build.version.sdk",nullptr);_exit(127);}
  pid_t bad=fork();REQUIRE(bad>=0);if(bad==0){execl("/system/bin/false","false",nullptr);_exit(127);}
  auto deadline=std::chrono::steady_clock::now()+std::chrono::seconds(5);
  while(observed.size()<2 && std::chrono::steady_clock::now()<deadline){REQUIRE(loop.Wait(std::chrono::milliseconds(100)).ok());REQUIRE(children.healthy());}
  REQUIRE(observed.contains(good)&&observed.contains(bad));int status=0;REQUIRE(waitpid(good,&status,WNOHANG)==-1 && errno==ECHILD);REQUIRE(waitpid(bad,&status,WNOHANG)==-1 && errno==ECHILD);
  std::puts("ORIGINAL_REAPER_COLLECTED_BOTH_EXEC_CHILDREN_WAITPID_ECHILD");REQUIRE(children.Close().ok());REQUIRE(children.Close().ok());
 }
 REQUIRE(sigprocmask(SIG_SETMASK,nullptr,&after)==0);REQUIRE(sigismember(&before,SIGCHLD)==sigismember(&after,SIGCHLD));REQUIRE(fds()==baseline);std::printf("REAPER_CLOSED_MASK_RESTORED_FDS_BEFORE=%zu_AFTER=%zu\n",baseline,fds());return 0;
}
