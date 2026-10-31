from pathlib import Path
import json,subprocess,hashlib,time
r=Path('/home/tv/repositorio-principal');o=r/'dist/aosp16/hwc3-wayland-1';setup=json.loads((o/'continuation.json').read_text());rec=setup['record'];flags=setup['flags']
for source in [o/'source/Device.cpp']+[r/'runtime/aosp/native'/n for n in ['linux-wayland-output.cpp','linux-wayland-frame-composer.cpp','linux-wayland-display-finder.cpp']]:
 if any(row['path']==str(source) for row in rec['sources']):continue
 obj=o/(source.stem+'.o');cmd=flags+['-MMD','-MF',str(o/(source.stem+'.d')),'-c',str(source),'-o',str(obj)];p=subprocess.run(cmd,capture_output=True,text=True,timeout=150);rec['commands'].append({'argv':cmd,'exit':p.returncode,'stderr':p.stderr});(o/'build.json').write_text(json.dumps(rec,indent=2)+'\n');print(source.name,p.returncode,p.stderr[:2000],flush=True)
 if p.returncode:raise SystemExit(p.returncode)
 rec['sources'].append({'path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'object_sha256':hashlib.sha256(obj.read_bytes()).hexdigest()})
rec['terminal']=True;(o/'build.json').write_text(json.dumps(rec,indent=2)+'\n')
