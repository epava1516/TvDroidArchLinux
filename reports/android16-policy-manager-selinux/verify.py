from pathlib import Path
import json,subprocess,re,collections,hashlib
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/policy-manager-selinux-1';report=r/'reports/android16-policy-manager-selinux';assert json.load(open(out/'results.json'))['exit_code']==0
subprocess.run(['python',str(report/'cases.py'),str(out/'combined.bin'),str(report/'after.json')],check=True);after=json.load(open(report/'after.json'))['results'];special=all(x['exit_code']==x['after_adapter_expected'] for x in after);previous=[]
for row in json.load(open(r/'reports/android16-policy-proc-adapter/after.json'))['results']:
 cmd=row['argv'][:];cmd[1]=str(out/'combined.bin');p=subprocess.run(cmd,capture_output=True,text=True,timeout=10);expected=0 if row['case'].startswith('manager_linux_') else row['exit_code'];previous.append({'case':row['case'],'argv':cmd,'previous_exit_code':row['exit_code'],'expected':expected,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
valid=[]
for row in json.load(open(r/'reports/android16-policy-type-universe/access-comparison.json'))['results']:
 if row.get('previous_exit_code') not in (0,7):continue
 cmd=row['argv'][:];cmd[1]=str(out/'combined.bin');p=subprocess.run(cmd,capture_output=True,text=True,timeout=10);valid.append({'case':row['case'],'argv':cmd,'expected':row['exit_code'],'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
cmd=[str(r/'dist/aosp16/checkpolicy-host-2/source/checkpolicy'),'-M','-b','-C','-o',str(out/'export.cil'),str(out/'combined.bin')];p=subprocess.run(cmd,capture_output=True,text=True,timeout=30);assert p.returncode==0,p.stderr;before=(r/'dist/aosp16/policy-proc-adapter-1/export.cil').read_text();text=(out/'export.cil').read_text();a=collections.Counter(text.splitlines());b=collections.Counter(before.splitlines());added=list((a-b).elements());removed=list((b-a).elements());expected={'dir':{'getattr','search'},'file':{'read','getattr','map','open','write'},'security':{'compute_av'}};actual={}
for line in added:
 m=re.fullmatch(r'\(allow servicemanager linux.security_t \((\S+) \(([^()]*)\)\)\)',line)
 if m:actual[m[1]]=set(m[2].split())
def attrs(t):
 result={x:set() for x in re.findall(r'^\(typeattribute (\S+)\)$',t,re.M)};sets=re.findall(r'^\(typeattributeset (\S+) \(([^()]*)\)\)$',t,re.M);assert len(sets)==len(re.findall(r'^\(typeattributeset ',t,re.M))
 for key,value in sets:result[key].update(value.split())
 return result
record={'scope':'Original offline compiler/libsepol decisions and complete binary-to-CIL statement delta; no kernel endpoint calls/status mapping/original manager execution/APK acceptance','policy_sha256':hashlib.sha256((out/'combined.bin').read_bytes()).hexdigest(),'special_cases':len(after),'all_special_cases_match':special,'proc_regressions':previous,'all_proc_regressions_match':all(x['exit_code']==x['expected'] for x in previous),'original_valid_cases':valid,'all_original_valid_preserved':len(valid)==9 and all(x['exit_code']==x['expected'] for x in valid),'export_argv':cmd,'attribute_memberships_identical':attrs(before)==attrs(text),'statement_delta':{'added':added,'removed':removed,'exactly_three_expected_rules':len(added)==3 and not removed and actual==expected}};(report/'comparison.json').write_text(json.dumps(record,indent=2)+'\n');print('Special',special,'Proc',record['all_proc_regressions_match'],'Original',record['all_original_valid_preserved'],'Attrs',record['attribute_memberships_identical'],'Delta',record['statement_delta']['exactly_three_expected_rules'])
