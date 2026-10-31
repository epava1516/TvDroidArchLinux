from pathlib import Path
import json,subprocess,shutil
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/property-actions-build-1';out.mkdir();overlay=r/'dist/aosp16/property-actions-source-1';old=json.loads((r/'reports/android16-propertyinit-entry/link.json').read_text())['attempts'];flags=old[0]['argv'][:old[0]['argv'].index('-c')];flags[1:1]=['-I'+str(overlay)];rec={'scope':'Original init action/event loop integration boundary, not SecondStageMain, control backend or APK compatibility','commands':[]}
for name,source in [('init.cpp',overlay/'init.cpp'),('property_service.cpp',overlay/'property_service.cpp'),('probe',r/'reports/android16-property-actions/probe.cpp')]:
 cmd=flags+['-c',str(source),'-o',str(out/(name+'.o'))];x=subprocess.run(cmd,capture_output=True,text=True,timeout=150);rec['commands'].append({'argv':cmd,'exit':x.returncode,'stderr':x.stderr});(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n');print(name,x.returncode,x.stderr[:2500],flush=True);assert x.returncode==0
archive=out/'libinit-actions.a';shutil.copy2(r/'dist/aosp16/property-shutdown-build-3/libinit-shutdown.a',archive);subprocess.run(['/usr/bin/ar','r',str(archive),str(out/'init.cpp.o'),str(out/'property_service.cpp.o')],check=True)
cmd=[]
for a in old[1]['argv']:
 if a.startswith('--Map='):continue
 if a.endswith('/propertyinit-link-2/entry.o'):a=str(out/'probe.o')
 elif a.endswith('/propertyinit-link-2/entry'):a=str(out/'property-actions-probe')
 elif a.endswith('/libinit-native-archive-1/libinit-native-prototype.a'):a=str(archive)
 cmd.append(a)
cmd[1:1]=['--no-undefined','--no-allow-shlib-undefined'];x=subprocess.run(cmd,capture_output=True,text=True,timeout=120);rec['commands'].append({'argv':cmd,'exit':x.returncode,'stderr':x.stderr});(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n');print('link',x.returncode,x.stderr[:4500],flush=True);assert x.returncode==0
exe=r/'dist/aosp16/property-actions-execution-1';exe.mkdir();(exe/'data').mkdir();shutil.copytree(r/'dist/aosp16/propertyinit-execution-2/vendor',exe/'vendor');shutil.copy2(out/'property-actions-probe',exe/'data/property-actions-probe');s=(r/'reports/android16-property-shutdown/native-launcher.py').read_text().replace('property-shutdown-execution-4','property-actions-execution-1').replace('property-shutdown-probe','property-actions-probe');(exe/'launcher.py').write_text(s);(out/'native-launcher.py').write_text(s)
