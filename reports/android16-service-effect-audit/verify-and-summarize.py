from pathlib import Path
import json
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-service-effect-audit'
load=lambda name:json.loads((d/(name+'.json')).read_text())
m=load('canonical-final-manifest');assert m['execution']=='none' and m['admission_status']=='not_evaluated';assert len(m['services'])==4 and len(m['sections'])==5 and m['actions']==1;assert all(x['pid']==0 for x in m['services'])
q=load('quoted-import-manifest');assert len(q['services'])==2 and q['actions']==1
lines=[line['tokens'] for s in q['sections'] for line in s['lines']]
assert ['onrestart','setprop','persist.audit.text','value with spaces'] in lines
assert ['setprop','persist.audit.expansion','${audit.source:-fallback value}'] in lines
assert ['reboot_on_failure','reboot'] in lines
assert any(s['filename']=='/data/profiles/imported.rc' for s in q['sections'])
o=load('override-manifest');assert len(o['services'])==1 and len(o['sections'])==2
assert o['services'][0]['uid']==2000 and o['services'][0]['args'][0]=='/system/bin/getprop'
assert o['sections'][0]['lines'][-1]['tokens']==['onrestart','setprop','audit.old','value']
assert o['sections'][1]['lines'][-1]['tokens']==['onrestart','setprop','audit.new','value']
b=load('bad-option-mcp');assert b['exit']['code']==2;assert not any(l.startswith('PROFILE_AUDIT ') for l in b['observations']);assert not (d/'bad-option-manifest.json').exists()
for name in ['canonical-final','quoted-import','override']:assert load(name+'-mcp')['exit']['code']==0
names={s['name'] for s in m['services']};references=[];effects=[]
for s in m['sections']:
 for line in s['lines']:
  a=line['tokens'];base={'file':s['filename'],'line':line['line'],'tokens':a}
  if s['kind']=='service' and a[0]=='onrestart':
   effects.append(base)
   if a[1]=='restart':references.append({**base,'target':a[-1],'declared_in_current_cohort':a[-1] in names,'only_if_running':'--only-if-running' in a,'status':'runtime_semantics_not_tested'})
   if a[1]=='class_restart':references.append({**base,'class':a[-1],'members_in_current_cohort':[v['name'] for v in m['services'] if a[-1] in v['classes']],'only_enabled':'--only-enabled' in a,'status':'cohort_scope_not_approved'})
  elif a[0] in ['critical','shutdown','file','task_profiles','capabilities','interface'] or s['kind']=='on':effects.append(base)
result={'scope':'Declared original profile effects only; no policy admission or runtime handler execution','canonical_services':sorted(names),'direct_restart_references':references,'original_effect_declarations':effects,'unresolved_direct_targets':sorted({x['target'] for x in references if 'target' in x and not x['declared_in_current_cohort']}),'required_linux_decisions':['Scope original class restart to explicitly managed cohort; preserve flags/enable state and dependencies, no arbitrary host service control','Define critical and reboot_on_failure behavior as explicit Linux-supervisor failure policy; do not silently clear flags or reboot host','Validate Android UID/GID/cgroups/device FDs/task profiles/capabilities and original SELinux transitions before Start','Preserve property action triggers and onrestart order/arguments. Tokens are unexpanded declarations, not completed side effects','Bind policy to approved immutable profile hashes and original parser results; import and override declarations need effective-profile/provenance handling','No CheckAllCommands with runtime builtin map; it invokes handlers'],'regressions':['original canonical four-service and one-action declarations','original tokenizer preserves spaces/property template tokens','original ImportParser observed across imported profile','override declaration history separate from original final service UID/args','invalid option causes exit2 and no manifest even when partial original ServiceList exists'],'limits':['Audit not complete resolved policy; raw options not substituted for original private/default state','Import targets not restricted by audit; production must constrain/hash them before admission','No native service/process/APK launched by audit; PID0 metadata alone not complete process-tree proof','Programmatic actions and mutable source files outside approved immutable profile set not admitted','GMS/DRM/ARM remain separate unresolved axes']}
(d/'effect-summary.json').write_text(json.dumps(result,indent=2)+'\n');print('Verified five native captures and declaration regressions; unresolved targets:',result['unresolved_direct_targets'])
