from pathlib import Path
import json,subprocess,re,collections,hashlib
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/policy-proc-adapter-1';assert json.load(open(out/'results.json'))['exit_code']==0;report=r/'reports/android16-policy-proc-adapter'
subprocess.run(['python',str(report/'compare-access.py'),str(out/'combined.bin'),str(report/'after.json')],check=True)
old=json.load(open(report/'before.json'))['results'];new=json.load(open(report/'after.json'))['results'];assert [x['case'] for x in old]==[x['case'] for x in new]
checks=[]
for before,after in zip(old,new):
 expected=0 if after['case'].startswith('proc_directory_') and not after['case'].endswith('_denied') else 7
 checks.append({'case':after['case'],'before':before['exit_code'],'after':after['exit_code'],'expected':expected,'matches':after['exit_code']==expected})
valid=[]
for c in json.load(open(r/'reports/android16-policy-type-universe/access-comparison.json'))['results']:
 if c.get('previous_exit_code') not in (0,7):continue
 cmd=c['argv'][:];cmd[1]=str(out/'combined.bin');p=subprocess.run(cmd,capture_output=True,text=True,timeout=10);valid.append({'case':c['case'],'argv':cmd,'expected':c['exit_code'],'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
cmd=[str(r/'dist/aosp16/checkpolicy-host-2/source/checkpolicy'),'-M','-b','-C','-o',str(out/'export.cil'),str(out/'combined.bin')];p=subprocess.run(cmd,capture_output=True,text=True,timeout=30);assert p.returncode==0,p.stderr
before=(r/'dist/aosp16/policy-type-universe-sparse-linux-1/export.cil').read_text();after=(out/'export.cil').read_text();b=collections.Counter(before.splitlines());a=collections.Counter(after.splitlines());added=list((a-b).elements());removed=list((b-a).elements());diff={'scope':'Complete original binary-to-CIL statement multiset difference, order-independent; still not a live syscall/API guarantee','added':added,'removed':removed,'non_allow_changes':[x for x in added+removed if not x.startswith('(allow ')]}
def attributes(text):
 attrs={x:set() for x in re.findall(r'^\(typeattribute (\S+)\)$',text,re.M)};sets=re.findall(r'^\(typeattributeset (\S+) \(([^()]*)\)\)$',text,re.M);assert len(sets)==len(re.findall(r'^\(typeattributeset ',text,re.M))
 for key,value in sets:attrs[key].update(value.split())
 return attrs
record={'scope':'Offline original tools:17 control decisions,9 original valid queries, full binary-export statement delta and attribute memberships. Not live MAC/services/APK acceptance','policy_sha256':hashlib.sha256((out/'combined.bin').read_bytes()).hexdigest(),'checks':checks,'all_controls_match':all(x['matches'] for x in checks),'original_valid_cases':valid,'all_original_valid_preserved':len(valid)==9 and all(x['exit_code']==x['expected'] for x in valid),'export_argv':cmd,'attribute_memberships_identical':attributes(before)==attributes(after),'statement_delta':diff};(report/'comparison.json').write_text(json.dumps(record,indent=2)+'\n');print('Controls',record['all_controls_match'],'Originalvalid',record['all_original_valid_preserved'],'Attrs',record['attribute_memberships_identical'],'Added',len(added),'Removed',len(removed),'Nonallow',len(diff['non_allow_changes']))
