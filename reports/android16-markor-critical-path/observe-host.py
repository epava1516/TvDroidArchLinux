from pathlib import Path
import json,subprocess,os,sys,struct,mmap,hashlib,datetime,ctypes
r=Path('/home/tv/repositorio-principal');out=r/('dist/aosp16/markor-priority-host-observation-2' if len(sys.argv)>1 else 'dist/aosp16/markor-priority-host-observation-1');out.mkdir();mount=out/'sys/fs/selinux';mount.mkdir(parents=True)
subprocess.run(['/usr/bin/mount','--make-rprivate','/'],check=True)
subprocess.run(['/usr/bin/mount','-t','selinuxfs','-o','ro','selinuxfs',str(mount)],check=True)
def read(path):
 try:return {'state':'observed','value':path.read_text().strip()}
 except OSError as e:return {'state':'unknown','errno':e.errno}
result={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'Read-only private mount of current kernel selinuxfs; no load/enforce/relabel operation','kernel':os.uname().release,'active_lsm':read(Path('/sys/kernel/security/lsm')),'enforce':read(mount/'enforce'),'policyvers':read(mount/'policyvers'),'current_context':read(Path('/proc/self/attr/current')),'class_directory_exists':(mount/'class').exists()}
sys.path.insert(0,str(r/'tools/aosp'))
import check_host_security
result['status']=check_host_security.read_status(out)
result['private_mounts']=subprocess.check_output(['/usr/bin/findmnt','-J','-t','selinuxfs'],text=True)
print(json.dumps(result,indent=2))
