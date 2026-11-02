from pathlib import Path
import json,subprocess,shutil
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/property-actions-build-4';out.mkdir(exist_ok=True);overlay=r/'dist/aosp16/property-actions-source-3';old=json.loads((r/'reports/android16-propertyinit-entry/link.json').read_text())['attempts'];flags=old[0]['argv'][:old[0]['argv'].index('-c')];flags[1:1]=['-I'+str(overlay)];rec={'scope':'Original init action/event loop integration boundary, explicit lazy interface control, not SecondStageMain or APK compatibility','commands':[]}
for f in json.loads((overlay/'application.json').read_text())['files']:
 assert __import__('hashlib').sha256((overlay/f['name']).read_bytes()).hexdigest()==f['sha256'], f['name']
for name,source in [('init.cpp',overlay/'init.cpp'),('property_service.cpp',overlay/'property_service.cpp'),('probe',r/'reports/android16-property-actions/probe.cpp')]:
 cmd=flags+['-c',str(source),'-o',str(out/(name+'.o'))];x=subprocess.run(cmd,capture_output=True,text=True,timeout=150);rec['commands'].append({'argv':cmd,'exit':x.returncode,'stderr':x.stderr});(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n');print(name,x.returncode,x.stderr[:2500],flush=True);assert x.returncode==0
archive=out/'libinit-actions.a';shutil.copy2(r/'dist/aosp16/property-shutdown-build-3/libinit-shutdown.a',archive);subprocess.run(['/usr/bin/ar','r',str(archive),str(out/'init.cpp.o'),str(out/'property_service.cpp.o')],check=True)
# Final link belongs to the complete cohort: control handling retains original
# service/APEX/LMKD references absent from the older property-only probe link.
(out/'archive.json').write_text(json.dumps({'scope':'Compilation only; full cohort strict link and execution required','archive':str(archive),'sha256':__import__('hashlib').sha256(archive.read_bytes()).hexdigest()},indent=2)+'\n')
