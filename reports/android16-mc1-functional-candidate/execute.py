from pathlib import Path
import os,subprocess,ctypes,json,sys,shutil,socket,struct,fcntl,stat,time,threading,re
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16'/('mc1-live-'+str(time.time_ns()));out.mkdir();root=out/'root';root.mkdir()
def mount(*a):subprocess.run(['/usr/bin/mount',*map(str,a)],check=True,stdout=subprocess.DEVNULL)
mount('--make-rprivate','/')
# Fresh private superblock: reuse Android's original filesystem identity for
# Android objects, without changing Linux's global tmpfs labels or host mounts.
mount('-t','tmpfs','-o','mode=0755,fscontext=u:object_r:tmpfs:s0,rootcontext=u:object_r:rootfs:s0','tmpfs',root)
for n in ['system','apex','linkerconfig','data','dev','proc','sys','vendor','odm','archtv']:(root/n).mkdir()
gsi=out/'gsi';gsi.mkdir();mount('-o','loop,ro,noload','/home/tv/.cache/archtv/aosp16-qpr2/artifact-selection/gsi-original/system.img',gsi)
mount('--bind',gsi/'system',root/'system');mount('-o','remount,bind,ro',root/'system')
(root/'etc').symlink_to('/system/etc')
for n in ['product','system_ext']:(root/n).symlink_to('/system/'+n)
for n in ['fs','fs/selinux']:(root/'sys'/n).mkdir()
for n in ['socket','__properties__']:(root/'dev'/n).mkdir()
for n in ['property','local','local/tmp','local/tmp/archtv-mc1']:(root/'data'/n).mkdir(mode=0o700 if n in ['property','local/tmp/archtv-mc1'] else 0o755)
os.chown(root/'data/local/tmp/archtv-mc1',2000,2000)
for n,dev in [('null',(1,3)),('urandom',(1,9))]:os.mknod(root/'dev'/n,stat.S_IFCHR|0o666,os.makedev(*dev))
shutil.copytree(r/'dist/aosp16/linux-failure-sink-worker-1/vendor',root/'vendor',dirs_exist_ok=True)
shutil.copytree(r/'dist/aosp16/linux-selinux-handoff-2/linkerconfig-mc1',root/'linkerconfig',dirs_exist_ok=True)
for p in (r/'dist/aosp16/factory-inputs-3/root/apex').iterdir():
 if p.is_dir():(root/'apex'/p.name).mkdir()
 elif p.is_file():shutil.copyfile(p,root/'apex'/p.name)
# Original textual file_contexts: no SDK stub or hand-made label substitute.
fc=out/'original-file-contexts';shutil.copyfile(root/'system/etc/selinux/plat_file_contexts',fc)
lib=ctypes.CDLL(str(r/'dist/aosp16/linux-selinux-handoff-2/libselinux-3.11/src/libselinux.so.1'),use_errno=True)
class Opt(ctypes.Structure):_fields_=[('type',ctypes.c_int),('value',ctypes.c_char_p)]
lib.selabel_open.argtypes=[ctypes.c_uint,ctypes.POINTER(Opt),ctypes.c_uint];lib.selabel_open.restype=ctypes.c_void_p
lib.selabel_lookup_raw.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_char_p),ctypes.c_char_p,ctypes.c_int]
lib.lsetfilecon_raw.argtypes=[ctypes.c_char_p,ctypes.c_char_p];lib.freecon.argtypes=[ctypes.c_void_p]
opt=Opt(3,str(fc).encode());handle=lib.selabel_open(0,ctypes.byref(opt),1);assert handle,ctypes.get_errno()
def label(p):
 logical='/'+str(p.relative_to(root)) if p!=root else '/';c=ctypes.c_char_p()
 if logical.startswith('/apex/') and p.is_dir():
  # Empty mountpoints are hidden by original read-only payload roots.
  return
 if logical=='/archtv':
  # Covered by the immutable Linux payload root; never mint its trusted label
  # on the writable scaffold underneath.
  return
 if logical.startswith('/sys/') or logical=='/sys':
  # Private scaffolding only; real selinuxfs mounted over its leaf below.
  assert lib.lsetfilecon_raw(str(p).encode(),b'u:object_r:sysfs:s0')==0
  return
 ret=lib.selabel_lookup_raw(handle,ctypes.byref(c),logical.encode(),p.lstat().st_mode)
 assert ret==0,(logical,ctypes.get_errno())
 ret=lib.lsetfilecon_raw(str(p).encode(),c);assert ret==0,(logical,c.value,ctypes.get_errno())
 lib.freecon(c)
label(root)
for base,dirs,files in os.walk(root,followlinks=False):
 if Path(base)==root/'system':dirs[:]=[];continue
 dirs[:]=[n for n in dirs if Path(base)/n!=root/'system']
 for n in dirs+files:label(Path(base)/n)
for p in sorted((r/'dist/aosp16/factory-inputs-3').glob('*.payload.img')):
 target=root/'apex'/p.name.removesuffix('.payload.img');assert target.is_dir()
 kind=subprocess.check_output(['blkid','-p','-s','TYPE','-o','value',str(p)],text=True).strip()
 mount('-o','loop,ro,noload' if kind=='ext4' else 'loop,ro',p,target)
mount('-o','loop,ro,noload',r/'dist/aosp16/mc1-functional-candidate-5/payload-2.ext4',root/'archtv')
mount('-t','proc','proc',root/'proc')
# Only a new experiment subtree is exposed to the original libprocessgroup.
# Remount affects this private mount namespace, not the host mount flags.
mount('-o','remount,rw','/sys/fs/cgroup')
cgbase=Path('/sys/fs/cgroup/system.slice/codex-remote.service/archtv-mc1');cgbase.mkdir(exist_ok=True)
cg=cgbase/out.name;cg.mkdir()
(cg/'system').mkdir();os.chmod(cg/'system',0o775);os.chown(cg/'system',1000,1000)
# Place the whole cohort before transitioning: cgroup_procs_write_permission
# checks the source/destination common ancestor, not just the destination file.
# This trusted Linux factory crosses the host boundary; Android init then only
# migrates descendants inside its dedicated, originally labelled subtree.
(cg/'cgroup.procs').write_text(str(os.getpid()))
kernel=ctypes.CDLL(None,use_errno=True)
assert kernel.unshare(0x02000000)==0,ctypes.get_errno() # CLONE_NEWCGROUP after placement.
print('MC1_FACTORY_PLACED_IN_PRIVATE_CGROUP '+str(cg),flush=True)
(root/'sys/fs/cgroup').mkdir();mount('--bind',cg,root/'sys/fs/cgroup')
selinux=root/'sys/fs/selinux';mount('-t','selinuxfs','selinuxfs',selinux)
assert not(os.statvfs(selinux).f_flag&os.ST_RDONLY)
for n in ['load','enforce','disable','checkreqprot','commit_pending_bools']:
 p=selinux/n
 if p.exists():mount('--bind',p,p);mount('-o','remount,bind,ro',p)
binder=out/'binder';binder.mkdir();mount('-t','binder','binder',binder)
fd=os.open(binder/'binder-control',os.O_RDWR|os.O_CLOEXEC);request=bytearray(struct.pack('256sII',b'archtv-mc1-binder',0,0))
fcntl.ioctl(fd,0xc1086201,request,True);os.close(fd);os.chmod(binder/'archtv-mc1-binder',0o666)
(root/'dev/binder').touch();mount('--bind',binder/'archtv-mc1-binder',root/'dev/binder')
stdin_fd=os.open(root/'dev/null',os.O_RDONLY|os.O_CLOEXEC)
print('MC1_PREPARED original_GSI_and_36_APEX_RO NNP1 private_binder actual_context='+Path('/proc/self/attr/current').read_text().rstrip('\0'),flush=True)
if 'ARCHTV_MC1_READY_FD' in os.environ:
 ready=int(os.environ.pop('ARCHTV_MC1_READY_FD'));release=int(os.environ.pop('ARCHTV_MC1_RELEASE_FD'))
 os.write(ready,b'R');os.close(ready)
 assert os.read(release,1)==b'G';os.close(release)
libc=ctypes.CDLL(None,use_errno=True);assert libc.prctl(38,1,0,0,0)==0
os.chroot(root);os.chdir('/')
print('MC1_LINUX_FACTORY_STATUS '+json.dumps([s for s in Path('/proc/self/status').read_text().splitlines() if s.startswith(('Uid:','Gid:','CapEff:','CapPrm:','NoNewPrivs:'))]),flush=True)
env={'PATH':'/system/bin:/archtv/bin','ANDROID_ROOT':'/system','ANDROID_DATA':'/data'}
if Path('/sys/fs/selinux/enforce').read_text().strip()=='1':
 # The factory must enter through Rust; direct helper execution is forbidden
 # by policy. Refusal from helper's own identity guard would not prove MAC.
 try:
  forbidden=subprocess.run(['/archtv/bin/linux-exec-context','--permissive-integration'],stdin=stdin_fd,capture_output=True,text=True,env=env,timeout=2)
 except PermissionError as error:
  assert error.errno==13
  print('MC1_MAC_NEGATIVE_DIRECT_HELPER_EXEC_DENIED errno=13',flush=True)
 else:raise AssertionError('direct helper bypass was not kernel-denied: '+str(forbidden.returncode))
args=['/archtv/bin/native-supervisor','--diagnostic','--observe-ms','150','--','/archtv/bin/linux-exec-context','--permissive-integration']
lib.getpidcon_raw.argtypes=[ctypes.c_int,ctypes.POINTER(ctypes.c_char_p)]
p=subprocess.Popen(args,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True,stdin=stdin_fd,env=env,start_new_session=True)
errors=[];identities=[]
def collect():
 for line in p.stderr:
  errors.append(line)
  match=re.search(r'MC1_MANAGER_STARTED pid=(\d+)',line)
  if match:
   pid=int(match[1]);seen=[];seen_errors=[];deadline=time.monotonic()+1
   # Service::Start reports fork/credentials before the child's exec commits.
   # Observe the real post-exec SID; never substitute the intended context.
   while True:
    c=ctypes.c_char_p();ret=lib.getpidcon_raw(pid,ctypes.byref(c))
    actual=c.value.decode() if ret==0 else None
    if ret<0 and ctypes.get_errno() not in seen_errors:seen_errors.append(ctypes.get_errno())
    if ret==0:lib.freecon(c)
    if not seen or seen[-1]!=actual:seen.append(actual)
    if actual=='u:r:servicemanager:s0' or (ret<0 and ctypes.get_errno() in (2,3)) or time.monotonic()>=deadline:break
    time.sleep(.005)
   entry={'pid_namespace_pid':pid,'getpidcon_raw_return':ret,'actual_context':actual,'contexts_observed_in_order':seen,'errno_observed':seen_errors}
   try:
    status=Path('/proc/'+str(pid)+'/status').read_text()
    entry['status']=[l for l in status.splitlines() if l.startswith(('Uid:','Gid:','Groups:','CapEff:','CapPrm:','CapBnd:','NoNewPrivs:'))]
   except OSError as e:entry['status_error']=str(e)
   identities.append(entry)
thread=threading.Thread(target=collect);thread.start()
stdout=p.stdout.read();p.wait(timeout=24);thread.join(timeout=2);os.close(stdin_fd)
print('MC1_RESULT '+json.dumps({'exit':p.returncode,'stdout':stdout,'stderr':''.join(errors),'external_Linux_identity_observation':identities}),flush=True)
if p.returncode!=0:sys.exit(1)
assert identities and identities[0]['actual_context']=='u:r:servicemanager:s0'
text=Path('/data/local/tmp/archtv-mc1/service-list.txt').read_text()
assert 'manager:' in text and 'android.os.IServiceManager' in text
print('MC1_ORIGINAL_CLIENT_OUTPUT '+json.dumps(text),flush=True)
labels={n:os.getxattr(n,'security.selinux').decode().rstrip('\0') for n in ['/dev/binder','/archtv/lib/ld-linux-x86-64.so.2','/archtv/lib/libgcc_s.so.1']}
print('MC1_ACTUAL_LABELS '+json.dumps(labels),flush=True)
try:os.lstat('/dev/socket/property_service')
except FileNotFoundError:print('MC1_PROPERTY_SOCKET_ABSENT_OBSERVED',flush=True)
else:raise AssertionError('property socket remains after close')
assert labels['/dev/binder']=='u:object_r:binder_device:s0'
assert labels['/archtv/lib/ld-linux-x86-64.so.2']=='linux.system_u:linux.object_r:linux.ld_so_t:s0'
print('MC1_FUNCTIONAL_PREFIX_EXTERNALLY_VERIFIED NOT_APK_READINESS',flush=True)
