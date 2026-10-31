from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/policy-type-universe-linux-2';result=json.load(open(out/'results.json'));assert result['exit_code']==0,'Compiler must finish successfully before policy evaluation';rows=[]
for c in json.load(open(r/'reports/android16-policy-semantic-baselines/access-baselines.json'))['results']:
 src,tgt,cls,perm=c['argv'][-4:]
 def context(s):
  if c['policy']=='aosp':return s
  parts=s.split(':',3);return ':'.join(['linux.'+p for p in parts[:3]]+[parts[3]])
 cmd=[c['argv'][0],str(out/'combined.bin'),context(src),context(tgt),cls,perm];p=subprocess.run(cmd,capture_output=True,text=True,timeout=10);rows.append({'case':c['case'],'scope':'selected baseline, not full projection','argv':cmd,'previous_exit_code':c['exit_code'],'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
tool=str(r/'dist/aosp16/policy-access-host-1/source/sepol_check_access');app='u:r:untrusted_app:s0:c512,c768'
for name,target,cls,perm in [('app_original_proc_search','u:object_r:proc:s0','dir','search'),('app_linux_proc_search','linux.system_u:linux.object_r:linux.proc_t:s0','dir','search'),('app_original_meminfo_read','u:object_r:proc_meminfo:s0','file','read')]:
 cmd=[tool,str(out/'combined.bin'),app,target,cls,perm];p=subprocess.run(cmd,capture_output=True,text=True,timeout=10);rows.append({'case':name,'scope':'cross-label diagnostic, not actual syscall/APK','argv':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
(out/'access-comparison.json').write_text(json.dumps({'scope':'Original libsepol offline selected baseline/cross-label computations only, not full semantic preservation/live enforcement/APK acceptance','policy_sha256':hashlib.sha256((out/'combined.bin').read_bytes()).hexdigest(),'results':rows},indent=2)+'\n')
for row in rows:print(row['case'],row['exit_code'],row.get('previous_exit_code'),flush=True)
