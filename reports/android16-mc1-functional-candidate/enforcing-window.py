# One finite negative integration trial. No installed daemon or policy changes.
# Parent/watchdog remain outside the candidate PID namespace.
from pathlib import Path
import os,subprocess,ctypes,time,select,json,sys
r=Path('/home/tv/repositorio-principal');m=Path('/tmp/archtv-mc1-enforcing-window');m.mkdir(exist_ok=True)
subprocess.run(['mount','--make-rprivate','/'],check=True);subprocess.run(['mount','-t','selinuxfs','selinuxfs',str(m)],check=True)
assert (m/'enforce').read_text().strip()=='0'
assert Path('/proc/self/attr/current').read_bytes().rstrip(b'\0')==b'linux.system_u:linux.system_r:linux.init_t:s0'
# Exact source/target/class permissions were checked against loaded artifact.
fd=os.open(m/'enforce',os.O_RDWR|os.O_CLOEXEC)
rready,wready=os.pipe();rgo,wgo=os.pipe()
env=dict(os.environ,ARCHTV_MC1_READY_FD=str(wready),ARCHTV_MC1_RELEASE_FD=str(rgo))
args=['/usr/bin/unshare','--mount','--pid','--fork','--net','--ipc','--uts','--cgroup','/usr/bin/python',str(r/'reports/android16-mc1-functional-candidate/execute.py')]
p=subprocess.Popen(args,env=env,pass_fds=(wready,rgo),stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
os.close(wready);os.close(rgo)
assert select.select([rready],[],[],20)[0] and os.read(rready,1)==b'R'
os.close(rready)
# Fork before enforcement. No exec, library loads or filesystem traversal are
# needed by watchdog to restore the pre-opened, policy-allowed kernel control.
watchdog=os.fork()
if watchdog==0:
 time.sleep(4)
 try:
  os.lseek(fd,0,0);os.write(fd,b'0');os._exit(0)
 except BaseException:os._exit(90)
print('ENFORCING_WINDOW_ARMED seconds=4 watchdog_outside_candidate_pid_namespace',flush=True)
try:
 os.lseek(fd,0,0);assert os.write(fd,b'1')==1
 os.lseek(fd,0,0);assert os.read(fd,16).strip()==b'1'
 print('ENFORCING_WINDOW_ACTIVE observed=1',flush=True)
 os.write(wgo,b'G');os.close(wgo)
 output,_=p.communicate(timeout=10)
 print('ENFORCING_CANDIDATE '+json.dumps({'exit':p.returncode,'output':output}),flush=True)
finally:
 os.lseek(fd,0,0);os.write(fd,b'0')
 os.lseek(fd,0,0);state=os.read(fd,16).strip()
 _,status=os.waitpid(watchdog,0)
 print('ENFORCING_WINDOW_RECOVERED '+json.dumps({'enforce':state.decode(),'watchdog_status':status}),flush=True)
 assert state==b'0' and status==0
 os.close(fd)
sys.exit(p.returncode)
