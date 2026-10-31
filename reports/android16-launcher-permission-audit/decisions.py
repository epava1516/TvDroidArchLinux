from pathlib import Path
import json,subprocess,hashlib
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-launcher-permission-audit';policy=r/'dist/aosp16/policy-launcher-explicit-2/policy.bin';tool=r/'dist/aosp16/policy-access-host-1/source/sepol_check_access';actor='linux.system_u:archtv_launcher_r:archtv_launcher:s0';app='u:r:untrusted_app:s0:c512,c768';context=lambda t:'linux.system_u:linux.object_r:linux.'+t+':s0';cases=[]
for name,cls,perm in [('namespace_admin','capability','sys_admin'),('setuid','capability','setuid'),('setgid','capability','setgid'),('ptrace_cap','capability','sys_ptrace'),('net_admin','capability','net_admin'),('mac_admin','capability2','mac_admin'),('lockdown_integrity','lockdown','integrity'),('lockdown_confidentiality','lockdown','confidentiality')]:cases.append(('actor_'+name,actor,actor,cls,perm))
cases += [('actor_textrel_execmod',actor,context('textrel_shlib_t'),'file','execmod'),('actor_ldcache_read',actor,context('ld_so_cache_t'),'file','read'),('actor_urandom_read',actor,context('urandom_device_t'),'chr_file','read'),('actor_shadow_read',actor,context('shadow_t'),'file','read'),('actor_security_write',actor,context('security_t'),'file','write'),('app_actor_ptrace',app,actor,'process','ptrace'),('app_actor_socket_write',app,actor,'unix_stream_socket','write')]
for t in ['init_t','kernel_t','sshd_t','unconfined_t']:
 src='linux.system_u:linux.system_r:linux.'+t+':s0'
 cases.append(('host_'+t+'_enter_actor',src,actor,'process','transition'))
 cases.append(('host_'+t+'_ptrace_actor',src,actor,'process','ptrace'))
 cases.append(('actor_ptrace_host_'+t,actor,src,'process','ptrace'))
rows=[]
for name,src,target,cls,perm in cases:
 cmd=[str(tool),str(policy),src,target,cls,perm];p=subprocess.run(cmd,capture_output=True,text=True,timeout=10);rows.append({'case':name,'argv':cmd,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});print(name,p.returncode,flush=True)
(d/'decisions.json').write_text(json.dumps({'scope':'Original libsepol single-permission decisions using original current default booleans, concrete contexts; NOT live kernel/DAC/capability/Yama/other LSM/namespace result. Errors distinct from denials.','policy_sha256':hashlib.sha256(policy.read_bytes()).hexdigest(),'tool_sha256':hashlib.sha256(tool.read_bytes()).hexdigest(),'results':rows},indent=2)+'\n')
