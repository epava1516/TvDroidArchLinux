from pathlib import Path
import os,subprocess,json,ctypes
repo=Path('/home/tv/repositorio-principal');source=repo/'dist/aosp16/factory-inputs-2/root';out=repo/'dist/aosp16/linkerconfig-2';runtime=out/'runtime';runtime.mkdir()
def mount(*args):subprocess.run(['/usr/bin/mount',*map(str,args)],check=True,stdout=subprocess.DEVNULL)
mount('--bind',source,runtime);mount('-o','remount,bind,ro',runtime);mount('-t','proc','proc',runtime/'proc');mount('-t','tmpfs','-o','mode=755,size=16m','tmpfs',runtime/'dev')
(runtime/'dev/__properties__').mkdir();mount('--bind','/tmp/archtv-a16-property-area-3/properties-privileged',runtime/'dev/__properties__');mount('-o','remount,bind,ro',runtime/'dev/__properties__')
(runtime/'dev/kmsg').touch();mount('--bind',out/'private-kmsg',runtime/'dev/kmsg');(runtime/'dev/null').touch();mount('--bind','/dev/null',runtime/'dev/null')
mount('--bind',out/'generated',runtime/'linkerconfig')
for directory in ['tmp','data']:mount('-t','tmpfs','-o','mode=1777,size=16m','tmpfs',runtime/directory)
os.chroot(runtime);os.chdir('/data');os.setgroups([]);os.setgid(10000);os.setuid(10000);libc=ctypes.CDLL(None,use_errno=True)
if libc.prctl(38,1,0,0,0):raise OSError(ctypes.get_errno(),'PR_SET_NO_NEW_PRIVS')
print('PREEXEC_STATUS '+json.dumps([x for x in Path('/proc/self/status').read_text().splitlines() if x.startswith(('Uid:','Gid:','Groups:','CapEff:','CapPrm:','NoNewPrivs:'))]),flush=True)
env={'LD_LIBRARY_PATH':'/apex/com.android.runtime/lib64:/apex/com.android.runtime/lib64/bionic:/system/lib64'}
os.execve('/apex/com.android.runtime/bin/linkerconfig',['linkerconfig','--target','/linkerconfig'],env)
