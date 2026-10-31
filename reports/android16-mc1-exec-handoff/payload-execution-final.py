from pathlib import Path
import os,subprocess,ctypes,json,socket,sys
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/mc1-payload-execution-2';out.mkdir();root=out/'root';root.mkdir()
for n in ['system','apex','linkerconfig','data','dev','proc','sys','vendor','odm','archtv']:(root/n).mkdir()
def mount(*a):subprocess.run(['/usr/bin/mount',*map(str,a)],check=True,stdout=subprocess.DEVNULL)
mount('--make-rprivate','/')
gsi=out/'gsi';gsi.mkdir();mount('-o','loop,ro,noload',Path('/home/tv/.cache/archtv/aosp16-qpr2/artifact-selection/gsi-original/system.img'),gsi)
for n,source in [('system',gsi/'system'),('apex',r/'dist/aosp16/factory-inputs-3/root/apex'),('vendor',r/'dist/aosp16/linux-failure-sink-worker-1/vendor'),('linkerconfig',r/'dist/aosp16/linkerconfig-2/generated')]:
 mount('--bind',source,root/n);mount('-o','remount,bind,ro',root/n)
mount('-o','loop,ro,noload',r/'dist/aosp16/linux-selinux-handoff-2/payload-2.ext4',root/'archtv')
for n in ['product','system_ext']:(root/n).symlink_to('/system/'+n)
(root/'etc').symlink_to('/system/etc');mount('-t','proc','proc',root/'proc');(root/'dev/socket').mkdir();(root/'dev/__properties__').mkdir()
for n in ['null','urandom']:
 (root/'dev'/n).touch();mount('--bind','/dev/'+n,root/'dev'/n)
selinux=root/'sys/fs/selinux';selinux.mkdir(parents=True);mount('-t','selinuxfs','selinuxfs',selinux)
for n in ['load','enforce','disable','checkreqprot','commit_pending_bools']:
 p=selinux/n
 if p.exists():mount('--bind',p,p);mount('-o','remount,bind,ro',p)
sys.path.insert(0,str(r/'tools/aosp'));import check_host_security
before=check_host_security.read_status(root);assert before['enforcing']==0 and before['policyload']==0
libc=ctypes.CDLL(None,use_errno=True)
assert libc.prctl(38,1,0,0,0)==0
os.chroot(root);os.chdir('/')
env={'PATH':'/archtv/bin','ANDROID_ROOT':'/system','ANDROID_DATA':'/data'}
for args in [[],['--permissive-integration']]:
 p=subprocess.run(['/archtv/bin/linux-exec-context']+args,capture_output=True,text=True,env=env,timeout=3)
 print('HELPER_NEGATIVE '+json.dumps({'args':args,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr}),flush=True);assert p.returncode==78
control,inherited=socket.socketpair();control.settimeout(3)
p=subprocess.Popen(['/archtv/bin/property-coordinator','--mac-integration'],stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=dict(env,ARCHTV_NATIVE_CONTROL_FD=str(inherited.fileno())),pass_fds=(inherited.fileno(),));inherited.close()
stdout,stderr=p.communicate(timeout=3);frame=control.recv(128);control.close()
print('WORKER_MAC_NEGATIVE '+json.dumps({'exit':p.returncode,'frame':frame.decode(errors='replace'),'stdout':stdout.decode(errors='replace'),'stderr':stderr.decode(errors='replace')}),flush=True);assert p.returncode==78 and not frame
# Legacy diagnostic deliberately has no MAC acceptance: genuine RO selinuxfs
# is not autodetected by original Android libselinux. No readiness forged.
subprocess.run(['/archtv/lib/ld-linux-x86-64.so.2','--help'],stdout=subprocess.DEVNULL,check=True,env=env)
# mount executable was prepared on host; use libc mount after chroot, no host binary copy.
MS_REMOUNT=32;MS_RDONLY=1
assert libc.mount(None,b'/sys/fs/selinux',None,MS_REMOUNT|MS_RDONLY,None)==0,ctypes.get_errno()
p=subprocess.run(['/archtv/bin/native-supervisor','--diagnostic','--observe-ms','150','--','/archtv/bin/property-coordinator','--diagnostic'],capture_output=True,text=True,env=env,timeout=12)
print('DIRECT_LINUX_BIONIC_DIAGNOSTIC '+json.dumps({'exit':p.returncode,'stdout':p.stdout,'stderr_tail':p.stderr[-4000:],'scope':'ABI/path/channel only; not MAC, service availability or APK acceptance'}),flush=True);assert p.returncode==0
state=check_host_security.read_status(Path('/'));assert state['enforcing']==0 and state['policyload']==0
print('SECURITY_UNCHANGED '+json.dumps(state),flush=True)
