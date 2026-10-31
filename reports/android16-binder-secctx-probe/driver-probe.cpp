// Diagnostic only: a context node, NOT a service registry or APK runtime.
#include <linux/android/binder.h>
#include <sys/ioctl.h>
#include <sys/mman.h>
#include <sys/wait.h>
#include <unistd.h>
#include <fcntl.h>
#include <poll.h>
#include <errno.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <stdint.h>
static int open_driver() {
 int fd=open("/dev/binder",O_RDWR|O_CLOEXEC);
 if(fd<0){perror("open binder");exit(2);}
 void* p=mmap(nullptr,1024*1024,PROT_READ,MAP_PRIVATE|MAP_NORESERVE,fd,0);
 if(p==MAP_FAILED){perror("mmap binder");exit(2);} // check actual MAP_FAILED
 return fd;
}
struct __attribute__((packed)) Message {uint32_t command; binder_transaction_data data;};
static int exchange(int fd,void* w,size_t n,unsigned char* r,size_t cap,binder_write_read* out) {
 *out={};out->write_buffer=(uintptr_t)w;out->write_size=n;
 out->read_buffer=(uintptr_t)r;out->read_size=cap;
 int rc=ioctl(fd,BINDER_WRITE_READ,out);
 if(rc<0&&errno!=EAGAIN){perror("BINDER_WRITE_READ");return -1;}return rc;
}
int main(int argc,char** argv) {
 setvbuf(stdout,nullptr,_IONBF,0);alarm(8);bool sid=argc==2&&!strcmp(argv[1],"sid");
 int fd=open_driver();flat_binder_object obj={};obj.hdr.type=BINDER_TYPE_BINDER;
 obj.binder=0x1234;obj.cookie=0x5678;obj.flags=sid?FLAT_BINDER_FLAG_TXN_SECURITY_CTX:0;
 int rc=ioctl(fd,BINDER_SET_CONTEXT_MGR_EXT,&obj);
 printf("{\"event\":\"context_node\",\"request_sid\":%s,\"ioctl_rc\":%d,\"errno\":%d,\"uid\":%u}\n",sid?"true":"false",rc,rc<0?errno:0,getuid());
 if(rc<0)return 2;
 pid_t child=fork();if(child<0)return 2;
 if(child==0){close(fd);int c=open_driver();Message m={};m.command=BC_TRANSACTION;m.data.code=0x11223344;
  alignas(8) unsigned char buf[4096];binder_write_read b;
  for(int round=0;round<4;round++){
   exchange(c,round==0?&m:nullptr,round==0?sizeof(m):0,buf,sizeof(buf),&b);
   for(size_t p=0;p<b.read_consumed;){uint32_t cmd;memcpy(&cmd,buf+p,4);p+=4;
    printf("{\"event\":\"client_command\",\"command\":%u,\"pid\":%d,\"uid\":%u}\n",cmd,getpid(),getuid());
    if(cmd==BR_REPLY){binder_transaction_data tr;memcpy(&tr,buf+p,sizeof(tr));printf("{\"event\":\"reply\",\"size\":%llu}\n",(unsigned long long)tr.data_size);_exit(0);}
    if(cmd==BR_FAILED_REPLY||cmd==BR_DEAD_REPLY){binder_extended_error ee={};int er=ioctl(c,BINDER_GET_EXTENDED_ERROR,&ee);printf("{\"event\":\"extended_error\",\"ioctl_rc\":%d,\"command\":%u,\"param\":%d}\n",er,ee.command,ee.param);_exit(10);}
    size_t len=_IOC_SIZE(cmd);if(p+len>b.read_consumed)_exit(3);p+=len;
   }
   pollfd pf={c,POLLIN,0};if(poll(&pf,1,1500)<=0)_exit(11);
  }_exit(12);
 }
 uint32_t enter=BC_ENTER_LOOPER;binder_write_read enter_result;exchange(fd,&enter,sizeof(enter),nullptr,0,&enter_result);
 fcntl(fd,F_SETFL,O_NONBLOCK);bool received=false;int status=0;bool done=false;
 for(int rounds=0;rounds<12;rounds++){
  pollfd pf={fd,POLLIN,0};int ready=poll(&pf,1,250);
  if(ready>0){alignas(8) unsigned char buf[4096];binder_write_read b;exchange(fd,nullptr,0,buf,sizeof(buf),&b);
   for(size_t p=0;p<b.read_consumed;){uint32_t cmd;memcpy(&cmd,buf+p,4);p+=4;
    if(cmd==BR_TRANSACTION||cmd==BR_TRANSACTION_SEC_CTX){binder_transaction_data tr;memcpy(&tr,buf+p,sizeof(tr));
     printf("{\"event\":\"server_transaction\",\"security_command\":%s,\"sender_pid\":%d,\"expected_child_pid\":%d,\"sender_uid\":%u,\"expected_uid\":%u,\"code\":%u}\n",cmd==BR_TRANSACTION_SEC_CTX?"true":"false",tr.sender_pid,child,tr.sender_euid,getuid(),tr.code);
     if(tr.sender_pid!=child||tr.sender_euid!=getuid()||tr.code!=0x11223344)return 4;
     received=true;Message reply={};reply.command=BC_REPLY;binder_write_read wb;exchange(fd,&reply,sizeof(reply),nullptr,0,&wb);
    }
    size_t len=_IOC_SIZE(cmd);if(p+len>b.read_consumed)return 3;p+=len;
   }
  }
  if(waitpid(child,&status,WNOHANG)==child){done=true;break;}
 }
 if(!done){kill(child,SIGKILL);waitpid(child,&status,0);}
 int exitcode=WIFEXITED(status)?WEXITSTATUS(status):128+WTERMSIG(status);
 printf("{\"event\":\"result\",\"request_sid\":%s,\"received_transaction\":%s,\"child_exit\":%d,\"child_reaped\":true}\n",sid?"true":"false",received?"true":"false",exitcode);
 // Exit reflects raw outcome, not an assumed expected failure.
 return received&&exitcode==0?0:20;
}
