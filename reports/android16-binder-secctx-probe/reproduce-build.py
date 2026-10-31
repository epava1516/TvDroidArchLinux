from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/tv/repositorio-principal');p=r/'reports/android16-binder-secctx-probe';out=r/'dist/aosp16/binder-secctx-build-1';out.mkdir(exist_ok=True)
old=json.loads((r/'reports/android16-binder-kernel-contract/native-build.json').read_text())['results'][1]['argv'];cmd=old[:old.index('-c')]+['-c',str(p/'driver-probe.cpp'),'-o',str(out/'probe.o')];x=subprocess.run(cmd,capture_output=True,text=True);rec={'compile':{'argv':cmd,'exit_code':x.returncode,'stderr':x.stderr}};print(x.returncode,x.stderr[:2000]);
if x.returncode==0:
 cmd=json.loads((r/'reports/android16-binder-kernel-contract/native-link.json').read_text())['argv'];cmd=[str(out/'probe.o') if x.endswith('/binderDriverInterfaceTest.o') else str(out/'driver-probe') if x.endswith('/binderDriverInterfaceTest') else x for x in cmd if not x.endswith('/gtest-all.o')];x=subprocess.run(cmd,capture_output=True,text=True);rec['link']={'argv':cmd,'exit_code':x.returncode,'stderr':x.stderr};print(x.returncode,x.stderr[:2000])
(p/'build.json').write_text(json.dumps(rec,indent=2)+'\n')
