#include "property_service.h"
#include <android-base/logging.h>
#include <sys/system_properties.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/wait.h>
#include <unistd.h>
#include <cstdio>
#include <cstring>
#include <fstream>
#include <string>
#include <grp.h>
#define REQUIRE(x) do { if(!(x)){std::fprintf(stderr,"FAILED %s errno=%d\n",#x,errno);_exit(1);} }while(0)
static const char* name="persist.archtv.rejected";
static bool transfer(int fd,void* data,size_t size,bool writing){char* p=static_cast<char*>(data);while(size){ssize_t n=writing?write(fd,p,size):read(fd,p,size);if(n<0&&errno==EINTR)continue;if(n<=0)return false;p+=n;size-=n;}return true;}
int main(int argc,char** argv){
 android::base::InitLogging(argv,android::base::StderrLogger);
 if(argc==2 && std::strcmp(argv[1],"client")==0){
  REQUIRE(setgroups(0,nullptr)==0);REQUIRE(setgid(10000)==0);REQUIRE(setuid(10000)==0);
  std::ifstream status("/proc/self/status");std::string line;
  while(std::getline(status,line))if(line.rfind("Uid:",0)==0||line.rfind("Gid:",0)==0||line.rfind("Groups:",0)==0||line.rfind("CapEff:",0)==0||line.rfind("CapPrm:",0)==0||line.rfind("NoNewPrivs:",0)==0)std::printf("CLIENT_SECURITY %s\n",line.c_str());
  int restricted=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);REQUIRE(restricted>=0);sockaddr_un system_addr{};system_addr.sun_family=AF_UNIX;std::strcpy(system_addr.sun_path,"/dev/socket/property_service_for_system");int restricted_result=connect(restricted,reinterpret_cast<sockaddr*>(&system_addr),sizeof(system_addr));int restricted_errno=errno;close(restricted);REQUIRE(restricted_result==-1 && restricted_errno==EACCES);std::puts("SYSTEM_PROPERTY_SOCKET_DAC_EACCES_OK");
  int fd=socket(AF_UNIX,SOCK_STREAM|SOCK_CLOEXEC,0);REQUIRE(fd>=0);sockaddr_un addr{};addr.sun_family=AF_UNIX;std::strcpy(addr.sun_path,"/dev/socket/property_service");REQUIRE(connect(fd,reinterpret_cast<sockaddr*>(&addr),sizeof(addr))==0);
  uint32_t command=PROP_MSG_SETPROP2,n=std::strlen(name),v=12;char value[]="not-accepted";
  REQUIRE(transfer(fd,&command,4,true));REQUIRE(transfer(fd,&n,4,true));REQUIRE(transfer(fd,const_cast<char*>(name),n,true));REQUIRE(transfer(fd,&v,4,true));REQUIRE(transfer(fd,value,v,true));uint32_t response=0;REQUIRE(transfer(fd,&response,4,false));close(fd);std::printf("ORIGINAL_SOCKET_REPLY code=%u expected=%u\n",response,PROP_ERROR_PERMISSION_DENIED);REQUIRE(response==PROP_ERROR_PERMISSION_DENIED);
  int result=__system_property_set(name,"not-accepted");std::printf("ORIGINAL_BIONIC_CLIENT_RESULT %d\n",result);REQUIRE(result==-1);std::fflush(nullptr);_exit(0);
 }
 REQUIRE(argc==1);android::init::PropertyInit();REQUIRE(__system_property_find(name)==nullptr);int initfd=-1;android::init::StartPropertyService(&initfd);REQUIRE(initfd>=0);std::puts("ORIGINAL_PROPERTY_SERVICE_THREADS_AND_SOCKETS_STARTED_NOT_READINESS");std::fflush(nullptr);
 pid_t child=fork();REQUIRE(child>=0);if(child==0){execl("/data/property-socket-probe","property-socket-probe","client",nullptr);_exit(127);}int status=0;REQUIRE(waitpid(child,&status,0)==child);REQUIRE(WIFEXITED(status)&&WEXITSTATUS(status)==0);REQUIRE(__system_property_find(name)==nullptr);std::puts("REJECTED_PROPERTY_ABSENT_AFTER_REAL_SOCKET_REQUESTS");std::puts("DIAGNOSTIC_PROCESS_EXIT_NOT_PRODUCTION_SERVICE_SHUTDOWN");std::fflush(nullptr);close(initfd);_exit(0);
}
