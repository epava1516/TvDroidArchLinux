from pathlib import Path
import json,subprocess,os,sys,struct,mmap,hashlib,datetime
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/selinux-permissive-observation-1';out.mkdir();mount=out/'selinuxfs';mount.mkdir()
subprocess.run(['/usr/bin/mount','--make-rprivate','/'],check=True)
subprocess.run(['/usr/bin/mount','-t','selinuxfs','-o','ro','selinuxfs',str(mount)],check=True)
def read(path):
 try:return {'state':'observed','value':path.read_text().strip()}
 except OSError as e:return {'state':'unknown','errno':e.errno}
result={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Read-only private mount of current kernel selinuxfs; no load/enforce/relabel operation','kernel':os.uname().release,'active_lsm':read(Path('/sys/kernel/security/lsm')),'enforce':read(mount/'enforce'),'policyvers':read(mount/'policyvers'),'current_context':read(Path('/proc/self/attr/current')),'class_directory_exists':(mount/'class').exists()}
try:
 with (mount/'status').open('rb') as f:
  with mmap.mmap(f.fileno(),mmap.PAGESIZE,flags=mmap.MAP_SHARED,prot=mmap.PROT_READ) as a:
   for _ in range(20):
    before=struct.unpack_from('=I',a,4)[0];v=struct.unpack_from('=5I',a);after=struct.unpack_from('=I',a,4)[0]
    if before==after==v[1] and not before&1:result['status']=dict(zip(['version','sequence','enforcing','policyload','deny_unknown'],v));break
   else:result['status']={'state':'inconsistent'}
except OSError as e:result['status']={'state':'unknown','errno':e.errno}
result['private_mounts']=subprocess.check_output(['/usr/bin/findmnt','-J','-t','selinuxfs'],text=True)
print(json.dumps(result,indent=2))
