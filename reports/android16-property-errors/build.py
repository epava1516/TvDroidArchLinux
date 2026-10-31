from pathlib import Path
import json,subprocess,shutil,hashlib
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/property-errors-build-1';out.mkdir();overlay=r/'dist/aosp16/property-errors-source-1';old=json.loads((r/'reports/android16-propertyinit-entry/link.json').read_text())['attempts'];rec={'scope':'Adapted original persistence/error callers build, not server runtime acceptance','commands':[]};flags=old[0]['argv'][:old[0]['argv'].index('-c')];flags[1:1]=['-I'+str(overlay)]
for name in ['persistent_properties.cpp','property_service.cpp']:
 cmd=flags+['-c',str(overlay/name),'-o',str(out/(name+'.o'))];x=subprocess.run(cmd,capture_output=True,text=True,timeout=150);rec['commands'].append({'argv':cmd,'exit':x.returncode,'stderr':x.stderr});(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n');print(name,x.returncode,x.stderr[:2500],flush=True);assert x.returncode==0
archive=out/'libinit-adapted.a';shutil.copy2(r/'dist/aosp16/libinit-native-archive-1/libinit-native-prototype.a',archive);cmd=['/usr/bin/ar','r',str(archive),str(out/'persistent_properties.cpp.o'),str(out/'property_service.cpp.o')];subprocess.run(cmd,check=True)
cmd=flags+['-c',str(r/'reports/android16-property-errors/probe.cpp'),'-o',str(out/'probe.o')];x=subprocess.run(cmd,capture_output=True,text=True,timeout=90);rec['commands'].append({'argv':cmd,'exit':x.returncode,'stderr':x.stderr});print('probe',x.returncode,x.stderr[:1800],flush=True);assert x.returncode==0
cmd=[]
for a in old[1]['argv']:
 if a.startswith('--Map='):continue
 if a.endswith('/propertyinit-link-2/entry.o'):a=str(out/'probe.o')
 elif a.endswith('/propertyinit-link-2/entry'):a=str(out/'persistence-probe')
 elif a.endswith('/libinit-native-archive-1/libinit-native-prototype.a'):a=str(archive)
 cmd.append(a)
cmd[1:1]=['--no-undefined','--no-allow-shlib-undefined','--Map='+str(out/'probe.map')];x=subprocess.run(cmd,capture_output=True,text=True,timeout=120);rec['commands'].append({'argv':cmd,'exit':x.returncode,'stderr':x.stderr});print('link',x.returncode,x.stderr[:2500],flush=True);assert x.returncode==0
# Retain complete server entry in a second link-only artifact to verify caller compilation/link.
cmd=[str(out/'server-link-only') if a==str(out/'persistence-probe') else a for a in cmd];cmd[1:1]=['--undefined=_ZN7android4init20StartPropertyServiceEPi'];cmd=[a for a in cmd if not a.startswith('--Map=')];x=subprocess.run(cmd,capture_output=True,text=True,timeout=120);rec['commands'].append({'argv':cmd,'exit':x.returncode,'stderr':x.stderr});print('server root link',x.returncode,x.stderr[:1800],flush=True);assert x.returncode==0
(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n');exe=r/'dist/aosp16/property-errors-execution-1';exe.mkdir();(exe/'data').mkdir();(exe/'app').mkdir();shutil.copy2(out/'persistence-probe',exe/'data/persistence-probe');s=(r/'reports/android16-persistence-native/native-launcher.py').read_text().replace('persistence-native-execution-1','property-errors-execution-1');(exe/'launcher.py').write_text(s);(out/'native-launcher.py').write_text(s)
