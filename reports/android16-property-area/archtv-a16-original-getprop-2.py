from pathlib import Path
import subprocess,os,json,ctypes
stage=Path('/tmp/archtv-a16-property-area-3');runtime=Path('/tmp/archtv-a16-original-getprop-root-2');runtime.mkdir(exist_ok=False)
def mount(*args):subprocess.run(['/usr/bin/mount',*map(str,args)],check=True,stdout=subprocess.DEVNULL)
mount('--bind','/tmp/archtv-a16-native-root',runtime);mount('-o','remount,bind,ro',runtime)
mount('-t','proc','proc',runtime/'proc');mount('-t','tmpfs','-o','mode=755,size=16m','tmpfs',runtime/'dev')
(runtime/'dev/__properties__').mkdir();mount('--bind',stage/'properties-privileged',runtime/'dev/__properties__');mount('-o','remount,bind,ro',runtime/'dev/__properties__')
mount('--bind',stage/'probe',runtime/'probe');mount('-o','remount,bind,ro',runtime/'probe')
for directory in ['tmp','data']:mount('-t','tmpfs','-o','mode=1777,size=16m','tmpfs',runtime/directory)
os.chroot(runtime);os.chdir('/data');os.setgroups([]);os.setgid(10000);os.setuid(10000)
libc=ctypes.CDLL(None,use_errno=True)
if libc.prctl(38,1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'PR_SET_NO_NEW_PRIVS')
# Record actual kernel credentials before exec; this log stays outside the guest.
status=Path('/proc/self/status').read_text();print('PREEXEC_STATUS '+json.dumps([x for x in status.splitlines() if x.startswith(('Uid:','Gid:','Groups:','CapEff:','CapPrm:','NoNewPrivs:'))]),flush=True)
env={'LD_LIBRARY_PATH':':'.join(['/apex/com.android.art/lib64','/apex/com.android.runtime/lib64/bionic','/system/lib64','/apex/com.android.i18n/lib64','/apex/com.android.conscrypt/lib64','/apex/com.android.os.statsd/lib64'])}
os.execve('/system/bin/getprop',['getprop'],env)
