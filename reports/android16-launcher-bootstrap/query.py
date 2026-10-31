from pathlib import Path
import json,subprocess,hashlib
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-launcher-bootstrap';policy=r/'dist/aosp16/launcher-bootstrap-4/policy.bin';tools=r/'dist/aosp16/policy-access-host-1/source';transition=r/'dist/aosp16/policy-launch-transitions-1/sepol_compute_transition';rows=[]
creator='linux.system_u:linux.system_r:linux.init_t:s0';actor='linux.system_u:archtv_launcher_r:archtv_launcher:s0';image='linux.system_u:linux.object_r:archtv_launcher_exec:s0';init='u:r:init:s0'
def run(name,tool,args):
 cmd=[str(tool),str(policy)]+args;p=subprocess.run(cmd,capture_output=True,text=True,timeout=15);rows.append({'case':name,'argv':cmd,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});print(name,p.returncode,p.stdout.strip()[:140],flush=True);(d/'queries.json').write_text(json.dumps({'scope':'Offline original context/AV computations, not runtime exec/FD use; first load subject not observed. Errors distinct from denials.','policy_sha256':hashlib.sha256(policy.read_bytes()).hexdigest(),'results':rows},indent=2)+'\n');return p
run('creator_entry_context',transition,[creator,image,'process'])
run('actor_no_automatic_android_context',transition,[actor,'u:object_r:init_exec:s0','process'])
run('original_manager_context',transition,[init,'u:object_r:servicemanager_exec:s0','process'])
run('original_hwmanager_context',transition,[init,'u:object_r:hwservicemanager_exec:s0','process'])
socket=run('actor_created_socket_context',transition,[actor,actor,'unix_stream_socket']).stdout.strip()
cases=[('creator_to_actor',creator,actor,'process','transition'),('creator_exec_file',creator,image,'file','execute'),('actor_entrypoint',actor,image,'file','entrypoint'),('actor_exec_map',actor,image,'file','map'),('actor_no_exec_write',actor,image,'file','write'),('actor_to_android',actor,init,'process','transition'),('actor_kill_owned_coordinator',actor,init,'process','sigkill'),('actor_no_kill_host',actor,creator,'process','sigkill'),('actor_no_kill_manager',actor,'u:r:servicemanager:s0','process','sigkill'),('actor_control_create',actor,socket,'unix_stream_socket','create'),('android_control_read',init,socket,'unix_stream_socket','read'),('android_control_write',init,socket,'unix_stream_socket','write'),('android_control_fd',init,actor,'fd','use'),('actor_no_namespace_admin',actor,actor,'capability','sys_admin')]
for name,src,tgt in [('creator',creator,actor),('actor',actor,init)]:
 for perm in ['nnp_transition','nosuid_transition']:cases.append((name+'_'+perm,src,tgt,'process2',perm))
for t in ['kernel_t','sshd_t','unconfined_t']:
 src='linux.system_u:linux.system_r:linux.'+t+':s0';cases.extend([('other_'+t+'_no_enter',src,actor,'process','transition'),('other_'+t+'_no_exec',src,image,'file','execute'),('other_'+t+'_no_nnp',src,actor,'process2','nnp_transition')])
app='u:r:untrusted_app:s0:c512,c768';cases.extend([('app_no_exec',app,image,'file','execute'),('app_no_enter',app,actor,'process','transition'),('app_no_channel',app,socket,'unix_stream_socket','write'),('actor_no_bypass_manager',actor,'u:r:servicemanager:s0','process','transition'),('coordinator_no_policy_load',init,'linux.system_u:linux.object_r:linux.security_t:s0','security','load_policy')])
for target in ['servicemanager','hwservicemanager','vndservicemanager']:
 for perm in ['nnp_transition','nosuid_transition']:cases.append(('pending_service_'+target+'_'+perm,init,'u:r:'+target+':s0','process2',perm))
for perm in ['create','write','append','setattr','relabelto','relabelfrom']:cases.append(('creator_no_mint_'+perm,creator,image,'file',perm))
for name,src,tgt,cls,perm in cases:run(name,tools/'sepol_check_access',[src,tgt,cls,perm])
for name,src,tgt in [('creator',creator,actor),('actor',actor,init)]:run(name+'_context_validation',tools/'sepol_validate_transition',[src,tgt,'process',src])
