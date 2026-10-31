from pathlib import Path
import subprocess,os,ctypes,json
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/linux-failure-sink-oversize-1';root=out/'root';root.mkdir();original=r/'dist/aosp16/factory-inputs-3/root'
for n in ['system','apex','linkerconfig','data','vendor','odm','dev','proc']:(root/n).mkdir()
def mount(*a):subprocess.run(['/usr/bin/mount',*map(str,a)],check=True,stdout=subprocess.DEVNULL)
for n in ['system','apex']:
 mount('--bind',original/n,root/n);mount('-o','remount,bind,ro',root/n)
for n in ['product','system_ext']:(root/n).symlink_to('/system/'+n)
mount('--bind',out/'vendor',root/'vendor');mount('-o','remount,bind,ro',root/'vendor');(root/'etc').symlink_to('/system/etc');mount('--bind',r/'dist/aosp16/linkerconfig-2/generated',root/'linkerconfig');mount('-o','remount,bind,ro',root/'linkerconfig');mount('--bind',out/'data',root/'data');mount('-t','proc','proc',root/'proc')
(root/'dev/socket').mkdir();(root/'dev/null').touch();mount('--bind','/dev/null',root/'dev/null');os.chroot(root);os.chdir('/data');os.setgroups([])
# This is privileged initialization of a private property area, never an app.
libc=ctypes.CDLL(None,use_errno=True);assert libc.prctl(38,1,0,0,0)==0
s={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path('/proc/self/status').read_text().splitlines()};print('INITIALIZER_SECURITY '+json.dumps({k:s[k] for k in ['Uid','Gid','Groups','CapPrm','CapEff','NoNewPrivs']}),flush=True);os.execve('/data/failure-probe',['/data/failure-probe','oversize'],{'ANDROID_ROOT':'/system','ANDROID_DATA':'/data','ARCHTV_NATIVE_CONTROL_FD':os.environ['ARCHTV_NATIVE_CONTROL_FD']})
