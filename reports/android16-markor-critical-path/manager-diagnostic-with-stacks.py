from pathlib import Path
import os, subprocess, ctypes, fcntl, struct, json, sys, signal
r=Path('/home/tv/repositorio-principal')
out=r/'dist/aosp16/markor-manager-current-host-2'
out.mkdir();root=out/'runtime';root.mkdir()
for name in ['system','apex','linkerconfig','data','sys','dev','proc','vendor','odm']:(root/name).mkdir()
def mount(*args):subprocess.run(['/usr/bin/mount',*map(str,args)],check=True,stdout=subprocess.DEVNULL)
mount('--make-rprivate','/')
selinux=root/'sys/fs/selinux';selinux.mkdir(parents=True)
# Genuine filesystem visible to original libselinux autodetection. Not a policy load.
mount('-t','selinuxfs','selinuxfs',selinux)
protected=[]
for name in ['load','enforce','checkreqprot','disable','commit_pending_bools']:
 p=selinux/name
 if p.exists():
  mount('--bind',p,p);mount('-o','remount,bind,ro',p);protected.append(name)
sys.path.insert(0,str(r/'tools/aosp'));import check_host_security
before=check_host_security.read_status(root)
assert before['enforcing']==0 and before['policyload']==0
for name in ['system','apex']:
 mount('--bind',r/'dist/aosp16/factory-inputs-3/root'/name,root/name);mount('-o','remount,bind,ro',root/name)
for name in ['product','system_ext']:(root/name).symlink_to('/system/'+name)
(root/'etc').symlink_to('/system/etc')
mount('--bind',r/'dist/aosp16/linkerconfig-2/generated',root/'linkerconfig');mount('-o','remount,bind,ro',root/'linkerconfig')
mount('-t','proc','proc',root/'proc')
(root/'dev/__properties__').mkdir();mount('--bind',r/'dist/aosp16/propertyinit-execution-2/root/dev/__properties__',root/'dev/__properties__');mount('-o','remount,bind,ro',root/'dev/__properties__')
for name in ['null','urandom']:
 (root/'dev'/name).touch();mount('--bind','/dev/'+name,root/'dev'/name)
(root/'dev/socket').mkdir();(root/'dev/binderfs').mkdir()
mount('-t','binder','-o','max=1','binder',root/'dev/binderfs')
fd=os.open(root/'dev/binderfs/binder-control',os.O_RDWR|os.O_CLOEXEC);request=bytearray(struct.pack('256sII',b'binder',0,0))
try:fcntl.ioctl(fd,(3<<30)|(len(request)<<16)|(ord('b')<<8)|1,request,True)
finally:os.close(fd)
os.chmod(root/'dev/binderfs/binder',0o666);(root/'dev/binder').symlink_to('/dev/binderfs/binder')
# Open logs before chroot; only private test output is writable.
managerlog=open(out/'manager.log','w+');clientlog=open(out/'client.log','w+')
libc=ctypes.CDLL(None,use_errno=True)
def credentials(uid):
 os.setgroups([]);os.setgid(uid);os.setuid(uid)
 if libc.prctl(38,1,0,0,0)!=0:raise OSError(ctypes.get_errno(),'NNP')
 status={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path('/proc/self/status').read_text().splitlines()}
 assert status['NoNewPrivs']=='1' and int(status['CapEff'],16)==0 and int(status['CapPrm'],16)==0
 print('DIAGNOSTIC_IDENTITY '+json.dumps({k:status[k] for k in ['Uid','Gid','CapEff','CapPrm','NoNewPrivs']}),flush=True)
os.chroot(root);os.chdir('/')
env={'ANDROID_ROOT':'/system','ANDROID_DATA':'/data','PATH':'/system/bin'}
manager=None
try:
 manager=subprocess.Popen(['/system/bin/servicemanager','/dev/binder'],stdout=managerlog,stderr=subprocess.STDOUT,env=env,preexec_fn=lambda:credentials(1000))
 # service retries/context-manager wait are bounded by the parent; no readiness claim.
 client=subprocess.Popen(['/system/bin/service','list'],stdout=clientlog,stderr=subprocess.STDOUT,env=env,preexec_fn=lambda:credentials(10000))
 try:clientexit=client.wait(timeout=5)
 except subprocess.TimeoutExpired:
  for name,process in [('manager',manager),('client',client)]:
   snapshot={}
   for node in ['wchan','syscall','status']:
    try:snapshot[node]=Path('/proc/'+str(process.pid)+'/'+node).read_text()[:5000]
    except OSError as error:snapshot[node]={'errno':error.errno}
   try:snapshot['fds']={p.name:os.readlink(p) for p in Path('/proc/'+str(process.pid)+'/fd').iterdir()}
   except OSError as error:snapshot['fds']={'errno':error.errno}
   print('BLOCKED_PROCESS '+name+' '+json.dumps(snapshot),flush=True)
  client.kill();clientexit=client.wait()
 print('MANAGER_DIAGNOSTIC '+json.dumps({'client_exit':clientexit,'manager_exit_before_cleanup':manager.poll(),'protected_controls':protected,'status_before':before}),flush=True)
 for name,log in [('manager',managerlog),('client',clientlog)]:
  log.flush();log.seek(0);print('ORIGINAL_'+name.upper()+'_OUTPUT '+log.read(12000),flush=True)
finally:
 if manager is not None:
  if manager.poll() is None:manager.terminate()
  try:manager.wait(timeout=2)
  except subprocess.TimeoutExpired:manager.kill();manager.wait()
 # checker path now chroot-relative genuine filesystem, no writable policy operation.
 after=check_host_security.read_status(Path('/'))
 assert after['enforcing']==before['enforcing'] and after['policyload']==before['policyload']
 print('SECURITY_UNCHANGED '+json.dumps(after),flush=True)
