#!/usr/bin/env python3
"""Rebuild the seat adapter against the preserved, verified original HWC frontend."""
from pathlib import Path
import sys,json,subprocess,hashlib
r=Path(__file__).resolve().parents[2];old=r/'dist/aosp16/hwc3-wayland-1';out=(r/sys.argv[1]).resolve();out.mkdir()
record={'scope':'Original HWC frontend with Linux seat gateway; build only, not input or MAC acceptance','commands':[],'inputs':{}}
def digest(p):return hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
def run(argv):
 p=subprocess.run(argv,capture_output=True,text=True,timeout=150);record['commands'].append({'argv':argv,'exit':p.returncode,'stderr':p.stderr});(out/'build.json').write_text(json.dumps(record,indent=2)+'\n');print(Path(argv[0]).name,p.returncode,p.stderr[:2000],flush=True);
 if p.returncode:raise SystemExit(p.returncode)
link=json.loads((old/'link.json').read_text());assert digest(Path(link['argv'][-1]))==link['executable_sha256']
native=Path('/home/tv/.cache/archtv/aosp16-qpr2/frameworks-native-gui-source-1')
for name in ['IInputConstants','MotionEventFlag','PointerCaptureMode','PointerIconType']:
 source=native/('libs/input/android/os/'+name+'.aidl');record['inputs'][str(source)]=digest(source)
 run([str(r/'dist/aosp16/aidl-host-build-4/aidl'),'--lang=cpp','--out='+str(out/'aidl-src'),'--header_out='+str(out/'include'),'-I'+str(native/'libs/input'),str(source)])
protocol=r/'runtime/aosp/protocols/archtv-launcher-v1.xml'
record['inputs'][str(protocol)]=digest(protocol)
scanner=r/'dist/aosp16/wayland-client-1/wayland-scanner'
for mode,name in [('client-header','archtv-launcher-client-protocol.h'),('private-code','archtv-launcher-protocol.c')]:
 run([str(scanner),'-s',mode,str(protocol),str(out/name)])
base=json.loads((r/'dist/aosp16/wayland-client-1/build.json').read_text())
cflags=next(c['argv'] for c in base['commands'] if Path(c['argv'][0]).name=='clang-21')
cflags=cflags[:cflags.index('-c')]
run(cflags+['-I'+str(out),'-c',str(out/'archtv-launcher-protocol.c'),'-o',str(out/'archtv-launcher-protocol.o')])
state=json.loads((old/'build.json').read_text())
for name in ['linux-wayland-output.cpp','linux-wayland-frame-composer.cpp']:
 source=r/'runtime/aosp/native'/name
 cmd=list(next(c['argv'] for c in state['commands'] if '-c' in c['argv'] and 'linux-wayland-frame-composer.cpp' in c['argv'][c['argv'].index('-c')+1]))
 cmd[cmd.index('-c')+1]=str(source)
 cmd[1:1]=['-I'+str(out),'-I'+str(out/'include'),'-I'+str(native/'libs/binder/include'),'-I/home/tv/.cache/archtv/aosp16-qpr2/wayland-input-original']
 for flag,suffix in [('-o','.o'),('-MF','.d')]:cmd[cmd.index(flag)+1]=str(out/(source.stem+suffix))
 record['inputs'][str(source)]=digest(source)
 run(cmd)
for name in ['linux-launcher-control.h','linux-wayland-input.h','linux-wayland-task-protocol.h','linux-wayland-output.h','linux-wayland-frame-composer.h']:
 p=r/'runtime/aosp/native'/name;record['inputs'][str(p)]=digest(p)
cmd=list(link['argv'])
for name in ['linux-wayland-output','linux-wayland-frame-composer']:
 oldobj=str(old/(name+'.o'));assert cmd.count(oldobj)==1
 cmd[cmd.index(oldobj)]=str(out/(name+'.o'))
cmd[-1]=str(out/'android.hardware.graphics.composer3-service.archtv-input')
cmd.insert(-2,str(out/'archtv-launcher-protocol.o'))
lib=r/'dist/aosp16/factory-inputs-3/root/system/lib64/libinput.so';cmd.insert(-2,str(lib))
record['inputs'][str(lib)]=digest(lib)
for a in cmd:
 if a.endswith('.o') or (a.endswith('.a') and Path(a).exists()):record['inputs'][a]=digest(Path(a))
run(cmd);record['executable']=cmd[-1];record['executable_sha256']=digest(Path(cmd[-1]));record['terminal']=True;(out/'build.json').write_text(json.dumps(record,indent=2)+'\n')
