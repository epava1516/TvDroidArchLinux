#include "property_service.h"
#include "persistent_properties.h"
#include "proto_utils.h"
#include "system/core/init/property_service.pb.h"
#include <sys/stat.h>
#include <dirent.h>
#include <fcntl.h>
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
static size_t count_entries(const char* path){DIR* d=opendir(path);REQUIRE(d!=nullptr);size_t count=0;while(auto* e=readdir(d))if(std::strcmp(e->d_name,".") && std::strcmp(e->d_name,".."))++count;closedir(d);return count;}
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
 REQUIRE(argc==1);REQUIRE(mkdir("/data/property",0700)==0);PersistentProperties seed;auto* record=seed.add_properties();record->set_name("persist.archtv.loaded");record->set_value("original-init-message");REQUIRE(android::init::WritePersistentPropertyFile(seed).ok());android::init::PropertyInit();REQUIRE(__system_property_find("persist.archtv.loaded")==nullptr);REQUIRE(__system_property_find(name)==nullptr);const char* async="ro.property_service.async_persist_writes";REQUIRE(__system_property_find(async)==nullptr);REQUIRE(__system_property_add(async,std::strlen(async),"true",4)==0);std::puts("TRUSTED_TEST_INITIALIZER_CONFIGURES_ASYNC_WRITER_NOT_PEER_WRITE");size_t baseline_threads=count_entries("/proc/self/task");size_t baseline_fds=count_entries("/proc/self/fd");int initfd=-1;android::init::StartPropertyService(&initfd);REQUIRE(initfd>=0);InitMessage message;message.set_load_persistent_properties(true);uint32_t serial=__system_property_area_serial();REQUIRE(android::init::SendMessage(initfd,message).ok());
 for(int attempt=0;attempt<4 && __system_property_find("ro.persistent_properties.ready")==nullptr;++attempt){uint32_t next=serial;timespec timeout{2,0};REQUIRE(__system_property_wait(nullptr,serial,&next,&timeout));serial=next;}
 char ready[PROP_VALUE_MAX]={};char loaded[PROP_VALUE_MAX]={};REQUIRE(__system_property_get("ro.persistent_properties.ready",ready)>0);REQUIRE(std::strcmp(ready,"true")==0);REQUIRE(__system_property_get("persist.archtv.loaded",loaded)>0);REQUIRE(std::strcmp(loaded,"original-init-message")==0);std::puts("ORIGINAL_INITMESSAGE_LOAD_AND_BIONIC_SERIAL_WAIT_OK");std::puts("PERSISTENT_FILE_VALUE_LOADED_IN_ORIGINAL_PROPERTY_AREA");std::puts("ORIGINAL_PROPERTY_SERVICE_THREADS_AND_SOCKETS_STARTED_NOT_MANAGER_READINESS");std::fflush(nullptr);
 pid_t child=fork();REQUIRE(child>=0);if(child==0){execl("/data/property-shutdown-probe","property-socket-probe","client",nullptr);_exit(127);}int status=0;REQUIRE(waitpid(child,&status,0)==child);REQUIRE(WIFEXITED(status)&&WEXITSTATUS(status)==0);REQUIRE(__system_property_find(name)==nullptr);std::puts("REJECTED_PROPERTY_ABSENT_AFTER_REAL_SOCKET_REQUESTS");size_t active_threads=count_entries("/proc/self/task");REQUIRE(active_threads>=baseline_threads+3);REQUIRE(android::init::StopPropertyService().ok());REQUIRE(android::init::StopPropertyService().ok());REQUIRE(fcntl(initfd,F_GETFD)>=0);close(initfd);struct stat st{};REQUIRE(lstat("/dev/socket/property_service",&st)==-1 && errno==ENOENT);REQUIRE(lstat("/dev/socket/property_service_for_system",&st)==-1 && errno==ENOENT);size_t remaining_threads=count_entries("/proc/self/task");size_t remaining_fds=count_entries("/proc/self/fd");std::printf("SHUTDOWN_COUNTS threads_before=%zu active=%zu after=%zu fds_before=%zu after=%zu\n",baseline_threads,active_threads,remaining_threads,baseline_fds,remaining_fds);REQUIRE(remaining_threads==baseline_threads);REQUIRE(remaining_fds==baseline_fds);std::puts("PROPERTY_SOCKET_WORKERS_AND_IDLE_WRITER_JOINED_SOCKETS_REMOVED_CALLER_FD_OWNERSHIP_OK");std::fflush(nullptr);return 0;
}
