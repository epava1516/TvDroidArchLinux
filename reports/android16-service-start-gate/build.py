from pathlib import Path
import json, subprocess, shutil
r=Path('/home/tv/repositorio-principal')
d=r/'reports/android16-service-start-gate'
out=r/'dist/aosp16/service-start-gate-build-1'
out.mkdir()
previous=json.loads((r/'reports/android16-child-reaper/build-attempt-2.json').read_text())
compile=next(x['argv'] for x in previous['commands'] if '-c' in x['argv'] and str(r/'reports/android16-child-reaper/probe.cpp') in x['argv'])
link=next(x['argv'] for x in previous['commands'] if str(r/'dist/aosp16/child-reaper-build-2/child-reaper-probe') in x['argv'])
compile=[str(d/'probe.cpp') if x==str(r/'reports/android16-child-reaper/probe.cpp') else str(out/'probe.o') if x.endswith('/child-reaper-build-2/probe.o') else x for x in compile]
link=[str(out/'probe.o') if x.endswith('/child-reaper-build-2/probe.o') else str(out/'service-start-gate') if x.endswith('/child-reaper-build-2/child-reaper-probe') else x for x in link]
record=[]
for cmd in (compile,link):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=120)
 record.append({'argv':cmd,'exit':p.returncode,'stderr':p.stderr})
 (d/'build.json').write_text(json.dumps(record,indent=2)+'\n')
 print(p.returncode,p.stderr[:1500],flush=True)
 assert p.returncode==0
exe=r/'dist/aosp16/service-start-gate-execution-1'
exe.mkdir();(exe/'data').mkdir();(exe/'app').mkdir()
shutil.copytree(r/'dist/aosp16/propertyinit-execution-2/vendor',exe/'vendor')
shutil.copy2(out/'service-start-gate',exe/'data/service-start-gate')
s=(r/'reports/android16-service-profile/launcher-canonical.py').read_text().replace('service-profile-canonical-1','service-start-gate-execution-1')
i=s.index("os.execve('/data/verify-service-profile'")
s=s[:i]+"os.execve('/data/service-start-gate',['/data/service-start-gate'],{'ANDROID_ROOT':'/system','ANDROID_DATA':'/data'})\n"
(exe/'launcher.py').write_text(s)
shutil.copy2(exe/'launcher.py',d/'launcher.py')
