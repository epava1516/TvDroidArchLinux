from pathlib import Path
import json
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-launcher-bootstrap';rows=json.loads((d/'queries.json').read_text())['results'];by={x['case']:x for x in rows};expected={'creator_entry_context':'linux.system_u:archtv_launcher_r:archtv_launcher:s0','actor_no_automatic_android_context':'linux.system_u:archtv_launcher_r:archtv_launcher:s0','original_manager_context':'u:r:servicemanager:s0','original_hwmanager_context':'u:r:hwservicemanager:s0','actor_created_socket_context':'linux.system_u:object_r:archtv_launcher:s0'}
for name,value in expected.items():assert by[name]['exit']==0 and by[name]['stdout'].strip()==value
allowed={'creator_to_actor','creator_exec_file','actor_entrypoint','actor_exec_map','actor_to_android','actor_kill_owned_coordinator','actor_control_create','android_control_read','android_control_write','android_control_fd','creator_nnp_transition','creator_nosuid_transition','actor_nnp_transition','actor_nosuid_transition','creator_context_validation','actor_context_validation'}
for name,row in by.items():
 if name in expected:continue
 assert row['exit']==(0 if name in allowed else 7),(name,row['exit'])
assert len(rows)==51
index=json.loads((d/'final-export-index.json').read_text());assert index['typebounds']==[];assert '(policycap userspace_initial_context)' in index['policycaps'] and '(policycap nnp_nosuid_transition)' in index['policycaps']
assert sum(x['case'].startswith('pending_service_') for x in rows)==6
for i in [1,2,3,4]:
 j=json.loads((r/f'dist/aosp16/launcher-bootstrap-{i}/compiler.json').read_text());assert j['exit_code']==0 and j['neverallow_disabled'] is False
print('51 offline queries verified; 6 downstream service NNP/nosuid denials remain. No native/runtime acceptance.')
