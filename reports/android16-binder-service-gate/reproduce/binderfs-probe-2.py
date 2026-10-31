from pathlib import Path
import subprocess,os,fcntl,struct,json,hashlib,ctypes
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/binderfs-probe-2';rows=[]
for name in ['a','b']:
 mount=out/name;mount.mkdir();subprocess.run(['mount','-t','binder','-o','max=3','binder',str(mount)],check=True);fd=os.open(mount/'binder-control',os.O_RDWR|os.O_CLOEXEC)
 try:
  request=bytearray(struct.pack('256sII',b'binder',0,0));fcntl.ioctl(fd,(3<<30)|(len(request)<<16)|(ord('b')<<8)|1,request,True);device,major,minor=struct.unpack('256sII',request)
 finally:os.close(fd)
 os.chmod(mount/'binder',0o666);features={p.name:p.read_text().strip() for p in (mount/'features').glob('*')};rows.append({'mount':name,'major':major,'minor':minor,'features':features})
assert (rows[0]['major'],rows[0]['minor'])!=(rows[1]['major'],rows[1]['minor'])
pid=os.fork()
if pid==0:
 statusfd=os.open('/proc/self/status',os.O_RDONLY);libc=ctypes.CDLL(None);os.chroot(out);os.chdir('/');os.setgroups([]);os.setgid(10000);os.setuid(10000);assert libc.prctl(38,1,0,0,0)==0;status=os.read(statusfd,65536).decode();os.close(statusfd);security={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in status.splitlines()};assert int(security['CapEff'],16)==0 and int(security['CapPrm'],16)==0 and security['NoNewPrivs']=='1';print('PREEXEC_SECURITY '+json.dumps({k:security[k] for k in ['Uid','Gid','Groups','CapEff','CapPrm','NoNewPrivs']}),flush=True);results=[]
 for name in ['a','b']:
  fd=os.open(Path('/')/name/'binder',os.O_RDWR|os.O_CLOEXEC)
  try:
   data=bytearray(4);fcntl.ioctl(fd,(3<<30)|(4<<16)|(ord('b')<<8)|9,data,True);results.append({'mount':name,'protocol_version':struct.unpack('i',data)[0]})
  finally:os.close(fd)
 print('UNPRIVILEGED_BINDER_VERSION '+json.dumps(results),flush=True);os._exit(0)
_,status=os.waitpid(pid,0);result={'scope':'Private Binder device allocation and unprivileged version ioctl only, no transactions/services/policy/APK acceptance','kernel':os.uname().release,'uid':10000,'capabilities_after_setuid':'expected zero; full status asserted in later native framework test','devices':rows,'child_exit':os.waitstatus_to_exitcode(status),'header_source':'original pinned Bionic linux/android/binderfs.h','namespaces':'Private mount/PID/network/IPC/UTS/cgroup, no Android boot; mounts vanish at namespace exit'};(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
