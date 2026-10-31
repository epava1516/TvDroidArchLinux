from pathlib import Path
import subprocess,json,hashlib,sys
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16'/('wayland-output-3' if len(sys.argv)<2 else sys.argv[1]);out.mkdir();old=r/'dist/aosp16/wayland-client-1';cache=Path('/home/tv/.cache/archtv/graphics-candidates-1');rec={'scope':'Reusable single-window Wayland SHM transport compiled against original Bionic client. Frame callback is NOT sync_file, physical present or APK compatibility.','commands':[]}
def run(cmd):
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=90);rec['commands'].append({'argv':cmd,'exit':p.returncode,'stderr':p.stderr});(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n');print(Path(cmd[0]).name,p.returncode,p.stderr[:2500],flush=True)
 if p.returncode:raise SystemExit(p.returncode)
for mode,name in [('client-header','xdg-shell-client-protocol.h'),('private-code','xdg-shell-protocol.c')]:run([str(old/'wayland-scanner'),'-s',mode,str(cache/'wayland-protocols/xdg-shell.xml'),str(out/name)])
prior=json.loads((old/'build.json').read_text());flags=next(c['argv'] for c in prior['commands'] if Path(c['argv'][0]).name=='clang-21');flags=flags[:flags.index('-c')];run(flags+['-I'+str(out),'-c',str(out/'xdg-shell-protocol.c'),'-o',str(out/'xdg.o')])
flags=json.loads((r/'reports/android16-hwc3-frontend/build.json').read_text())['results'][0]['argv'];flags=flags[:flags.index('-MMD')];flags+=['-D_GNU_SOURCE','-I'+str(cache/'wayland/src'),'-I'+str(old/'generated'),'-I'+str(out)];src=r/'runtime/aosp/native/linux-wayland-output.cpp';run(flags+['-c',str(src),'-o',str(out/'output.o')]);rec['source_sha256']=hashlib.sha256(src.read_bytes()).hexdigest();rec['terminal']=True;(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n')
