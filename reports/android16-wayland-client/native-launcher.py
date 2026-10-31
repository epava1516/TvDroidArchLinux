from pathlib import Path
import os,sys,subprocess,socket,tempfile,ctypes,json,stat
r=Path('/home/tv/repositorio-principal');root=Path(tempfile.mkdtemp(prefix='archtv-wl-native-',dir=r/'dist/aosp16'));peer=socket.socket(socket.AF_UNIX,socket.SOCK_STREAM);peer.connect(sys.argv[1]);fd=peer.detach();os.set_inheritable(fd,True)
def mount(*a):subprocess.run(['/usr/bin/mount',*map(str,a)],check=True)
mount('--make-rprivate','/');mount('-t','tmpfs','-o','mode=0755,size=64m','tmpfs',root)
for n in ['system','apex','apex/com.android.runtime','data','dev','proc']:(root/n).mkdir()
gsi=root/'original';gsi.mkdir();mount('-o','loop,ro,noload','/home/tv/.cache/archtv/aosp16-qpr2/artifact-selection/gsi-original/system.img',gsi);mount('--bind',gsi/'system',root/'system');mount('-o','remount,bind,ro',root/'system');mount('-o','loop,ro,noload',r/'dist/aosp16/factory-inputs-3/com.android.runtime.payload.img',root/'apex/com.android.runtime')
(root/'data/client').touch();mount('--bind',r/'dist/aosp16/wayland-output-3/wayland-output-client',root/'data/client');mount('-o','remount,bind,ro',root/'data/client');mount('-t','proc','proc',root/'proc');os.mknod(root/'dev/null',stat.S_IFCHR|0o666,os.makedev(1,3))
os.chroot(root);os.chdir('/');os.setgroups([]);os.setgid(10000);os.setuid(10000);libc=ctypes.CDLL(None,use_errno=True);assert libc.prctl(38,1,0,0,0)==0
status={l.split(':',1)[0]:l.split(':',1)[1].strip() for l in Path('/proc/self/status').read_text().splitlines()};print('OBSERVED_BEFORE_ASSERT '+json.dumps({n:status[n] for n in ['Uid','Gid','Groups','CapEff','CapPrm','CapInh','CapAmb','NoNewPrivs']}),flush=True);assert all(int(status[n],16)==0 for n in ['CapEff','CapPrm','CapInh','CapAmb']) and status['NoNewPrivs']=='1';assert list(map(int,status['Uid'].split()))==[10000]*4
print('NATIVE_WAYLAND_DIAGNOSTIC_IDENTITY '+json.dumps({n:status[n] for n in ['Uid','Gid','Groups','CapEff','CapPrm','NoNewPrivs']}),flush=True);print('ACTUAL_SID '+Path('/proc/self/attr/current').read_text().rstrip('\0'),flush=True)
os.execve('/data/client',['/data/client',str(fd)],{'ANDROID_ROOT':'/system','ANDROID_DATA':'/data','PATH':'/system/bin'})
