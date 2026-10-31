from pathlib import Path
import json
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-launcher-permission-audit';j=json.loads((d/'actor-potential-allows.json').read_text());assert j['matching_rules']==54 and j['conditional_rules']==3 and j['target_type_count']==57
assert j['export']['all_AV_rules_parsed']==152494 and j['export']['all_extended_rules_parsed']==657
assert len(j['incoming_potential_rules'])==633 and j['extended_actor_rules']==[]
rows={x['case']:x for x in json.loads((d/'decisions.json').read_text())['results']}
allowed={'actor_lockdown_integrity','actor_lockdown_confidentiality','actor_textrel_execmod','actor_ldcache_read','host_init_t_ptrace_actor','host_kernel_t_ptrace_actor','host_unconfined_t_ptrace_actor'}
for name,row in rows.items():assert row['exit']==(0 if name in allowed else 7),(name,row['exit'])
booleans=json.loads((d/'boolean-defaults.json').read_text());assert booleans['allow_ptrace']==booleans['global_ssp']=='false'
assert j['class_permission_union'].get('capability',[])==[] and j['class_permission_union'].get('capability2',[])==[]
delta=json.loads((r/'dist/aosp16/launcher-permission-audit-1/statement-delta.json').read_text());assert len(delta['added'])==27 and len(delta['removed'])==2
other_added=[x for x in delta['added'] if x.startswith('(allow ') and 'archtv_launcher' not in x];assert len(other_added)==3 and all(x.startswith('(allow init linux.security_t ') for x in other_added)
assert not any(x.startswith('(allow ') for x in delta['removed'])
print('Static coverage, conditional/default distinction and 27 concrete libsepol decisions verified; not live authorization')
