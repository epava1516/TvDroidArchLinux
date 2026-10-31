from pathlib import Path
import json,hashlib,subprocess
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-policy-launcher-entry';base=r/'runtime/aosp/android16-qpr2/policy/build-profile.json';profile=json.loads(base.read_text());record={'scope':'Offline alternatives, no deployment approval or actual exec/host security changes','base_profile_sha256':hashlib.sha256(base.read_bytes()).hexdigest(),'commands':[]}
for case in ['automatic','explicit']:
 p=dict(profile);p['modules']=profile['modules']+['runtime/aosp/android16-qpr2/policy/experiments/launcher-'+case+'.cil'];(d/('profile-'+case+'.json')).write_text(json.dumps(p,indent=2)+'\n')
 cmd=['python',str(r/'tools/aosp/build_linux_policy.py'),'--profile',str(d/('profile-'+case+'.json')),'--output',str(r/('dist/aosp16/policy-launcher-'+case+'-1')),'--compile'];v=subprocess.run(cmd,capture_output=True,text=True,timeout=260);record['commands'].append({'case':case,'argv':cmd,'exit':v.returncode,'stdout':v.stdout,'stderr':v.stderr});(d/'build.json').write_text(json.dumps(record,indent=2)+'\n');print(case,v.returncode,v.stdout,v.stderr[:1000],flush=True)
