#include "persistent_properties.h"
#include <android-base/logging.h>
#include <sys/stat.h>
#include <sys/wait.h>
#include <unistd.h>
#include <cerrno>
#include <cstdlib>
#include <cstdio>
#include <string>
#define REQUIRE(x) do { if (!(x)) { std::fprintf(stderr,"FAILED %s errno=%d\n",#x,errno); return 1; } } while(0)
using namespace android::init;
static const char* key="persist.archtv.regression";
int main(int argc,char** argv) {
 android::base::InitLogging(argv,android::base::StderrLogger);
 if(argc==3) {
  std::string mode=argv[1]; std::string value=argv[2];
  if(mode=="initial") { PersistentProperties p;auto* x=p.add_properties();x->set_name(key);x->set_value(value);auto result=WritePersistentPropertyFile(p);REQUIRE(result.ok());std::puts("ORIGINAL_PROTOBUF_WRITE_OK");return 0; }
  if(mode=="update") { auto result=TryWritePersistentProperty(key,value);REQUIRE(result.ok());std::puts("ADAPTED_CHECKED_UPDATE_OK_REQUIRES_RELOAD");return 0; }
  if(mode=="fsync_file" || mode=="fsync_directory") { REQUIRE(setenv("ARCHTV_TEST_FSYNC_FAILURE",mode=="fsync_file"?"file":"directory",1)==0);auto result=TryWritePersistentProperty(key,value);REQUIRE(!result.ok());REQUIRE(result.error().code()==EIO);std::printf("ADAPTED_FSYNC_EIO_PROPAGATED kind=%s\n",mode.c_str());return 0; }
  if(mode=="read") { auto p=LoadPersistentPropertyFile();REQUIRE(p.ok());REQUIRE(p->properties_size()==1);REQUIRE(p->properties(0).name()==key);REQUIRE(p->properties(0).value()==value);std::printf("SEPARATE_PROCESS_READ_OK value=%s\n",value.c_str());return 0; }
  if(mode=="denied") { PersistentProperties p;auto* x=p.add_properties();x->set_name(key);x->set_value(value);auto result=WritePersistentPropertyFile(p);REQUIRE(!result.ok());REQUIRE(result.error().code()==EACCES);std::puts("ORIGINAL_DIRECT_WRITE_EACCES_OBSERVED");auto checked=TryWritePersistentProperty(key,value);REQUIRE(!checked.ok());REQUIRE(checked.error().code()==EACCES);std::puts("ADAPTED_CHECKED_UPDATE_EACCES_PROPAGATED");WritePersistentProperty(key,value);std::puts("ORIGINAL_VOID_UPDATE_RETURNED_AFTER_STORAGE_FAILURE");return 0; }
  return 2;
 }
 REQUIRE(argc==1);REQUIRE(mkdir("/data/property",0755)==0);
 auto run=[&](const char* mode,const char* value) { pid_t p=fork();if(p<0)return false;if(p==0) {execl("/data/persistence-probe","persistence-probe",mode,value,nullptr);_exit(127);}int status=0;if(waitpid(p,&status,0)!=p)return false;return WIFEXITED(status)&&WEXITSTATUS(status)==0; };
 REQUIRE(run("initial","first"));REQUIRE(run("read","first"));
 REQUIRE(run("update","second"));REQUIRE(run("read","second"));
 REQUIRE(chmod("/data/property",0555)==0);REQUIRE(run("denied","must-not-persist"));REQUIRE(run("read","second"));REQUIRE(chmod("/data/property",0755)==0);
 REQUIRE(run("fsync_file","file-must-not-persist"));REQUIRE(run("read","second"));
 REQUIRE(run("fsync_directory","directory-visible-but-not-durable"));REQUIRE(run("read","directory-visible-but-not-durable"));
 std::puts("PERSISTENCE_ERROR_PROPAGATION_OK_NOT_SERVER_OR_POWER_LOSS");return 0;
}
