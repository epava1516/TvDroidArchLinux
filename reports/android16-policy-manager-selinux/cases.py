from pathlib import Path
import subprocess,json,sys,hashlib
r=Path('/home/tv/repositorio-principal');policy=Path(sys.argv[1]);dest=Path(sys.argv[2]);tool=r/'dist/aosp16/policy-access-host-1/source/sepol_check_access';manager='u:r:servicemanager:s0';app='u:r:untrusted_app:s0:c512,c768';target='linux.system_u:linux.object_r:linux.security_t:s0';cases=[]
for cls,permissions in [('dir',['getattr','search']),('file',['read','getattr','map','open','write']),('security',['compute_av'])]:
 for perm in permissions:cases.append(('manager_'+cls+'_'+perm,manager,target,cls,perm,0))
for perm in ['compute_create','compute_member','check_context','load_policy','compute_relabel','compute_user','setenforce','setbool','setsecparam','setcheckreqprot','read_policy','validate_trans']:cases.append(('manager_security_'+perm+'_denied',manager,target,'security',perm,7))
for cls,perm in [('file','read'),('file','write'),('file','map'),('security','compute_av'),('security','load_policy'),('security','setenforce')]:cases.append(('app_'+cls+'_'+perm+'_denied',app,target,cls,perm,7))
cases += [('manager_shadow_read_denied',manager,'linux.system_u:linux.object_r:linux.shadow_t:s0','file','read',7),('app_activity_add_denied',app,'u:object_r:activity_service:s0','service_manager','add',7)]
rows=[]
for name,src,tgt,cls,perm,expected in cases:
 cmd=[str(tool),str(policy),src,tgt,cls,perm];p=subprocess.run(cmd,capture_output=True,text=True,timeout=10);rows.append({'case':name,'argv':cmd,'after_adapter_expected':expected,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr});print(name,p.returncode,flush=True)
dest.write_text(json.dumps({'scope':'Original libsepol offline single-permission decisions, not kernel syscalls/real status mapping or query/API execution. file.write alone is not administration; security class permissions checked separately.','policy_sha256':hashlib.sha256(policy.read_bytes()).hexdigest(),'results':rows},indent=2)+'\n')
