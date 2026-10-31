from pathlib import Path
import subprocess,json,shutil
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-postboot-mac-readiness';out=r/'dist/aosp16/postboot-mac-readiness-build-3';out.mkdir()
old=json.loads((r/'reports/android16-service-start-gate/build.json').read_text());compile=old[0]['argv'];compile=compile[:compile.index('-c')]+['-c',str(d/'native-inspect.cpp'),'-o',str(out/'inspect.o')]
link=[str(out/'inspect.o') if x.endswith('/service-start-gate-build-1/probe.o') else str(out/'native-inspect') if x.endswith('/service-start-gate-build-1/service-start-gate') else x for x in old[1]['argv']]
record=[]
for cmd in [compile,link]:
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=120);record.append({'argv':cmd,'exit':p.returncode,'stderr':p.stderr});(d/'build.json').write_text(json.dumps(record,indent=2)+'\n');print(p.returncode,p.stderr[:1400],flush=True);assert p.returncode==0
out=r/'dist/aosp16/postboot-mac-inspection-1';out.mkdir();(out/'data').mkdir();(out/'app').mkdir();shutil.copy2(r/'dist/aosp16/postboot-mac-readiness-build-3/native-inspect',out/'app/native-inspect')
s=(r/'reports/android16-selinux-permissive-boot/binder-sid-launcher.py').read_text().replace('selinux-permissive-binder-sid-1','postboot-mac-inspection-1');i=s.index("os.execve('/probe/driver-probe'");s=s[:i]+"os.execve('/probe/native-inspect',['/probe/native-inspect'],{'ANDROID_ROOT':'/system','ANDROID_DATA':'/data'})\n";(out/'launcher.py').write_text(s);shutil.copy2(out/'launcher.py',d/'native-launcher.py')
