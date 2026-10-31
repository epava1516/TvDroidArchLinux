from pathlib import Path
import json,subprocess,shutil
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/libui-link-2';d=out/'link-libs';(d/'libui.so').symlink_to(out/'libui.so');old=json.loads((r/'dist/aosp16/libui-implementation-build-4/state.json').read_text())['results'][0]['argv'];cmd=old[:old.index('-MMD')]+['-c',str(r/'reports/android16-libui-link/ui-runtime-probe.cpp'),'-o',str(out/'ui-runtime-probe.o')];x=subprocess.run(cmd,capture_output=True,text=True,timeout=90);rec={'compile':{'argv':cmd,'exit':x.returncode,'stderr':x.stderr}};print('compile',x.returncode,x.stderr[:2000],flush=True);assert x.returncode==0
old=json.loads((r/'reports/android16-libui-source-closure/codecs-link.json').read_text())['probe_link']['argv'];cmd=[]
for a in old:
 if a.startswith('-l:android.hardware.'):continue
 if a.endswith('/parcel-roundtrip.o'):a=str(out/'ui-runtime-probe.o')
 elif a.endswith('/parcel-roundtrip'):a=str(out/'ui-runtime-probe')
 elif a.startswith('--rpath-link='):a='--rpath-link='+str(d)
 elif a.startswith('-L'):a='-L'+str(d)
 cmd.append(a)
cmd[cmd.index('-lbinder'):cmd.index('-lbinder')]=['-lui'];x=subprocess.run(cmd,capture_output=True,text=True,timeout=60);rec['link']={'argv':cmd,'exit':x.returncode,'stderr':x.stderr};(out/'probe-build.json').write_text(json.dumps(rec,indent=2)+'\n');print('link',x.returncode,x.stderr[:2000],flush=True);assert x.returncode==0
exe=r/'dist/aosp16/libui-native-execution-1';exe.mkdir();(exe/'data').mkdir();(exe/'app').mkdir()
for n in ['libui.so','ui-runtime-probe']:shutil.copy2(out/n,exe/'data'/n)
s=(r/'reports/android16-libui-source-closure/native-launcher.py').read_text().replace('graphics-codecs-native-execution-1','libui-native-execution-1').replace('parcel-roundtrip','ui-runtime-probe');(exe/'launcher.py').write_text(s);(out/'native-launcher.py').write_text(s);print('PREPARED',flush=True)
