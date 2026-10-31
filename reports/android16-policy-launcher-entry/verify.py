from pathlib import Path
import json
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-policy-launcher-entry';auto=json.loads((d/'automatic-queries.json').read_text());explicit=json.loads((d/'explicit-queries.json').read_text());a={x['case']:x for x in auto['results']};e={x['case']:x for x in explicit['results']}
assert a['automatic_entry_context']['stdout'].strip()=='linux.system_u:linux.system_r:init:s0'
assert a['followup_original_service_context']['exit']==1
assert json.loads((d/'automatic-computed-transition-access.json').read_text())['exit']==0
assert json.loads((d/'automatic-followup-context-validity.json').read_text())['exit']==1
assert e['automatic_entry_context']['stdout'].strip()=='linux.system_u:archtv_launcher_r:archtv_launcher:s0'
for name,value in [('original_manager_context','u:r:servicemanager:s0'),('original_hwmanager_context','u:r:hwservicemanager:s0')]:assert e[name]['stdout'].strip()==value and e[name]['exit']==0
allowed={'explicit_transition_validation','actor_setexec','actor_init_transition','actor_exec_read','init_entrypoint','init_channel_fd','init_channel_read','init_compute_create','init_compute_av','init_check_context'}
for name,row in e.items():
 if name in ['automatic_entry_context','original_manager_context','original_hwmanager_context']:continue
 if name=='actor_wrong_role_is_invalid_context':assert row['exit']==1;continue
 assert row['exit']==(0 if name in allowed else 7),(name,row['exit'])
assert 'constraint' in e['actor_cannot_drop_MCS_categories']['stdout']
for name in ['unconfined','sshd','init','kernel']:assert e['unrelated_'+name+'_base']['exit']==e['unrelated_'+name+'_after']['exit']==7
for case in ['automatic-1','explicit-2']:
 c=json.loads((r/('dist/aosp16/policy-launcher-'+case)/'compiler.json').read_text());assert c['exit_code']==0 and c['neverallow_disabled'] is False
print('Automatic context dead-end and explicit bounded entry assertions verified; no actual process/domain/kernel policy test claimed')
