from pathlib import Path
import json,subprocess,shutil
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-service-effect-audit';out=r/'dist/aosp16/service-effect-audit-build-1';out.mkdir()
old=json.loads((r/'reports/android16-service-profile/build.json').read_text())
compile=old['compile']['argv'][:old['compile']['argv'].index('-c')]+['-I'+str(r/'runtime/aosp/native'),'-c',str(r/'runtime/aosp/native/audit-service-profiles.cpp'),'-o',str(out/'audit.o')]
link=[str(out/'audit.o') if x.endswith('/service-profile-build-3/verifier.o') else str(out/'audit-service-profiles') if x.endswith('/service-profile-build-3/verify-service-profile') else x for x in old['link']['argv']]
record=[]
for cmd in [compile,link]:
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=120);record.append({'argv':cmd,'exit':p.returncode,'stderr':p.stderr});(d/'build.json').write_text(json.dumps(record,indent=2)+'\n');print(p.returncode,p.stderr[:1800],flush=True);assert p.returncode==0
exe=r/'dist/aosp16/service-effect-audit-canonical-1';exe.mkdir();(exe/'data').mkdir();(exe/'app').mkdir();shutil.copytree(r/'dist/aosp16/service-profile-canonical-1/vendor',exe/'vendor');shutil.copy2(out/'audit-service-profiles',exe/'data/audit-service-profiles')
s=(r/'reports/android16-service-profile/launcher-canonical.py').read_text().replace('service-profile-canonical-1','service-effect-audit-canonical-1').replace('verify-service-profile','audit-service-profiles');(exe/'launcher.py').write_text(s);shutil.copy2(exe/'launcher.py',d/'launcher-canonical.py')
