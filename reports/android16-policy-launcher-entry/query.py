from pathlib import Path
import json,subprocess,sys,hashlib
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-policy-launcher-entry';kind=sys.argv[1];policy=Path(sys.argv[2]);dest=d/(kind+'-queries.json');transition=r/'dist/aosp16/policy-launch-transitions-1/sepol_compute_transition';access=r/'dist/aosp16/policy-access-host-1/source/sepol_check_access';validate=r/'dist/aosp16/policy-access-host-1/source/sepol_validate_transition';base=r/'dist/aosp16/linux-policy-builder-compile-1/policy.bin';rows=[]
role='linux.system_r' if kind=='automatic' else 'archtv_launcher_r';actor='linux.system_u:'+role+':archtv_launcher:s0';android='u:r:init:s0';linuxinit='linux.system_u:linux.system_r:linux.init_t:s0';linuxkernel='linux.system_u:linux.system_r:linux.kernel_t:s0';app='u:r:untrusted_app:s0:c512,c768';sec='linux.system_u:linux.object_r:linux.security_t:s0'
def run(name,tool,path,args):
 cmd=[str(tool),str(path)]+args;p=subprocess.run(cmd,capture_output=True,text=True,timeout=15);rows.append({'case':name,'argv':cmd,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});dest.write_text(json.dumps({'scope':'Offline computation and AV/validation queries only; no setexeccon/exec/kernel load/enforcement','policy_sha256':hashlib.sha256(policy.read_bytes()).hexdigest(),'results':rows},indent=2)+'\n');print(kind,name,p.returncode,p.stdout.strip()[:160],flush=True)
run('automatic_entry_context',transition,policy,[actor,'u:object_r:init_exec:s0','process'])
if kind=='automatic':run('followup_original_service_context',transition,policy,['linux.system_u:linux.system_r:init:s0','u:object_r:servicemanager_exec:s0','process'])
else:
 for name,target in [('manager','servicemanager'),('hwmanager','hwservicemanager')]:run('original_'+name+'_context',transition,policy,[android,'u:object_r:'+target+'_exec:s0','process'])
 run('explicit_transition_validation',validate,policy,[actor,android,'process',actor])
checks=[('actor_setexec',actor,actor,'process','setexec'),('actor_init_transition',actor,android,'process','transition'),('actor_init_dyntransition',actor,android,'process','dyntransition'),('actor_manager_bypass',actor,'u:r:servicemanager:s0','process','transition'),('actor_exec_read',actor,'u:object_r:init_exec:s0','file','read'),('init_entrypoint',android,'u:object_r:init_exec:s0','file','entrypoint'),('init_channel_fd',android,actor,'fd','use'),('init_channel_read',android,actor,'unix_stream_socket','read'),('app_channel_fd',app,actor,'fd','use'),('app_to_init',app,android,'process','transition'),('linux_init_to_android_init',linuxinit,android,'process','transition'),('linux_kernel_to_android_init',linuxkernel,android,'process','transition'),('init_compute_create',android,sec,'security','compute_create'),('init_compute_av',android,sec,'security','compute_av'),('init_check_context',android,sec,'security','check_context'),('init_load_policy',android,sec,'security','load_policy'),('init_setenforce',android,sec,'security','setenforce'),('app_security_write',app,sec,'file','write')]
for name,src,tgt,cls,perm in checks:run(name,access,policy,[src,tgt,cls,perm])
if kind!='automatic':
 run('actor_cannot_drop_MCS_categories',access,policy,['linux.system_u:archtv_launcher_r:archtv_launcher:s0:c512,c768',android,'process','transition'])
 run('actor_cannot_write_coordinator_exec',access,policy,[actor,'u:object_r:init_exec:s0','file','write'])
 run('actor_wrong_role_is_invalid_context',transition,policy,['linux.system_u:linux.system_r:archtv_launcher:s0','u:object_r:init_exec:s0','process'])
 # Check unrelated existing Linux subjects against the old and new policy: role edge must not widen them.
 for name,typ in [('unconfined','unconfined_t'),('sshd','sshd_t'),('init','init_t'),('kernel','kernel_t')]:
  src='linux.system_u:linux.system_r:linux.'+typ+':s0'
  for suffix,path in [('base',base),('after',policy)]:run('unrelated_'+name+'_'+suffix,access,path,[src,android,'process','transition'])
