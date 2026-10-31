from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-mc1-exec-handoff';policy=r/'dist/aosp16/exec-context-policy-2/policy.bin';tool=r/'dist/aosp16/policy-access-host-1/source/sepol_check_access';transition=r/'dist/aosp16/policy-launch-transitions-1/sepol_compute_transition'
actor='linux.system_u:archtv_launcher_r:archtv_launcher:s0';creator='linux.system_u:linux.system_r:linux.init_t:s0';helper='linux.system_u:linux.object_r:archtv_exec_context_exec:s0';directory='linux.system_u:linux.object_r:archtv_bundle_dir:s0';app='u:r:untrusted_app:s0:c512,c768';init='u:r:init:s0';rows=[]
def run(name,binary,args,expected):
 argv=[str(binary),str(policy)]+args;p=subprocess.run(argv,capture_output=True,text=True,timeout=20);rows.append({'case':name,'argv':argv,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'expected_exit':expected});print(name,p.returncode,flush=True)
run('helper_exec_preserves_Rust_actor',transition,[actor,helper,'process'],0)
for perm in ['read','getattr','open','map','execute','execute_no_trans']:run('actor_helper_'+perm,tool,[actor,helper,'file',perm],0)
for name,src in [('creator',creator),('coordinator',init),('app',app)]:run(name+'_cannot_enter_helper',tool,[src,helper,'file','execute'],7)
for name,src in [('creator',creator),('actor',actor),('coordinator',init)]:run(name+'_payload_traversal',tool,[src,directory,'dir','search'],0)
run('app_payload_traversal_denied',tool,[app,directory,'dir','search'],7)
for name,src in [('creator',creator),('actor',actor)]:run(name+'_Android_root_traversal',tool,[src,'u:object_r:rootfs:s0','dir','search'],0)
for perm in ['create','write','append','setattr','relabelto','relabelfrom']:run('actor_helper_no_'+perm,tool,[actor,helper,'file',perm],7)
for typ in ['lib_t','ld_so_t']:
 for perm in ['read','open','map','execute']:run('actor_'+typ+'_'+perm,tool,[actor,'linux.system_u:linux.object_r:linux.'+typ+':s0','file',perm],0)
for perm in ['read','open']:run('actor_real_selinuxfs_'+perm,tool,[actor,'linux.system_u:linux.object_r:linux.security_t:s0','file',perm],None)
run('actor_selinuxfs_check_context_stays_denied',tool,[actor,'linux.system_u:linux.object_r:linux.security_t:s0','security','check_context'],7)
report={'scope':'Original offline computations/access only, not loaded policy/contexts/syscalls. File read/open observations with no expected value expose remaining admission requirements.','policy_sha256':hashlib.sha256(policy.read_bytes()).hexdigest(),'results':rows};(d/'queries.json').write_text(json.dumps(report,indent=2)+'\n')
for row in rows:
 if row['expected_exit'] is not None:assert row['exit']==row['expected_exit'],row
assert rows[0]['stdout'].strip()==actor
assert all(row['exit'] in [0,7] for row in rows)
print('SELECTED_OFFLINE_CHECKS_OK; no MAC/runtime acceptance')
