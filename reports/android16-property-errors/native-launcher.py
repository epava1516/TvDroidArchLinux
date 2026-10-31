from pathlib import Path
import os,subprocess,ctypes,fcntl,struct,json
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/property-errors-fsync-execution-1';root=out/'runtime';root.mkdir();original=r/'dist/aosp16/factory-inputs-3/root'
for name in ('system','apex','linkerconfig','data','dev','proc','probe','tmp'):(root/name).mkdir()
def mount(*args):subprocess.run(['/usr/bin/mount',*map(str,args)],check=True,stdout=subprocess.DEVNULL)
mount('--make-rprivate','/')
for name in ('system','apex'):
 mount('--bind',original/name,root/name);mount('-o','remount,bind,ro',root/name)
for name in ('product','system_ext'):(root/name).symlink_to('/system/'+name)
(root/'etc').symlink_to('/system/etc');mount('--bind',r/'dist/aosp16/linkerconfig-2/generated',root/'linkerconfig');mount('-o','remount,bind,ro',root/'linkerconfig');mount('--bind',out/'data',root/'data');mount('--bind',out/'app',root/'probe');mount('-o','remount,bind,ro',root/'probe');mount('-t','proc','proc',root/'proc');mount('-t','tmpfs','-o','mode=1777,size=32m','tmpfs',root/'tmp');(root/'dev/__properties__').mkdir();mount('--bind',r/'dist/aosp16/propertyinit-execution-2/root/dev/__properties__',root/'dev/__properties__');mount('-o','remount,bind,ro',root/'dev/__properties__');(root/'dev/null').touch();mount('--bind','/dev/null',root/'dev/null');(root/'dev/binderfs').mkdir();mount('-t','binder','-o','max=1','binder',root/'dev/binderfs');fd=os.open(root/'dev/binderfs/binder-control',os.O_RDWR|os.O_CLOEXEC);request=bytearray(struct.pack('256sII',b'binder',0,0))
try:fcntl.ioctl(fd,(3<<30)|(len(request)<<16)|(ord('b')<<8)|1,request,True)
finally:os.close(fd)
os.chmod(root/'dev/binderfs/binder',0o666);(root/'dev/binder').symlink_to('/dev/binderfs/binder');print('PRIVATE_BINDER '+json.dumps({'major':struct.unpack('256sII',request)[1],'minor':struct.unpack('256sII',request)[2]}),flush=True);os.chown(out/'data',10000,10000);os.chroot(root);os.chdir('/data');os.setgroups([]);os.setgid(10000);os.setuid(10000);libc=ctypes.CDLL(None,use_errno=True)
if libc.prctl(38,1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'prctl no_new_privs')
status={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path('/proc/self/status').read_text().splitlines()};assert status['Uid'].split()==['10000']*4 and status['Gid'].split()==['10000']*4 and not status['Groups'] and status['NoNewPrivs']=='1';assert all(int(status[k],16)==0 for k in ('CapEff','CapPrm','CapInh','CapAmb'));print('PREEXEC_SECURITY '+json.dumps({k:status[k] for k in ('Uid','Gid','Groups','CapEff','CapPrm','CapInh','CapAmb','NoNewPrivs')}),flush=True)
os.execve('/data/persistence-probe',['/data/persistence-probe'],{'ANDROID_ROOT':'/system','ANDROID_DATA':'/data','LD_LIBRARY_PATH':'/data','LD_PRELOAD':'/data/fsync-fault.so'})
