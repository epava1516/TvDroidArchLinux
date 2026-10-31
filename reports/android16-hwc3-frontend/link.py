from pathlib import Path
import json,subprocess,hashlib,re
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/hwc3-frontend-2';cache=Path('/home/tv/.cache/archtv/graphics-candidates-1');state=json.loads((out/'build.json').read_text());assert state.get('terminal') and all(x['exit']==0 for x in state['results'])
rec={'scope':'Strict link of whole original frontend and real providers; expected missing real backend must remain an error. No unresolved-symbol suppression, fake backend, executable/service/graphics acceptance.','providers':[]}
flags=state['results'][0]['argv'];flags=flags[:flags.index('-MMD')];source=cache/'hardware-interfaces/common/support/NativeHandle.cpp';obj=out/'NativeHandle.o';cmd=flags+['-c',str(source),'-o',str(obj)];x=subprocess.run(cmd,capture_output=True,text=True,timeout=90);rec['NativeHandle']={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'argv':cmd,'exit':x.returncode,'stderr':x.stderr};assert x.returncode==0,x.stderr
libdir=out/'link-libs';libdir.mkdir(exist_ok=True);gsi=r/'dist/aosp16/factory-inputs-3/root';special={'libui.so':r/'dist/aosp16/libui-link-2/libui.so','android.hardware.graphics.composer@2.1-resources.so':r/'dist/aosp16/composer-link-1/android.hardware.graphics.composer@2.1-resources.so'}
direct=['android.hardware.graphics.composer3-V4-ndk.so','android.hardware.graphics.common-V7-ndk.so','android.hardware.common-V2-ndk.so','android.hardware.drm.common-V1-ndk.so','android.hardware.graphics.composer@2.1-resources.so','libbase.so','libbinder_ndk.so','libcutils.so','libhidlbase.so','liblog.so','libsync.so','libui.so','libutils.so','libc++.so','libc.so','libm.so','libdl.so'];queue=list(direct);seen=set()
while queue:
 name=queue.pop(0)
 if name in seen:continue
 seen.add(name);p=special.get(name,gsi/('apex/com.android.runtime/lib64/bionic' if name in ['libc.so','libm.so','libdl.so','libdl_android.so'] else 'system/lib64')/name);assert p.is_file(),p
 dynamic=subprocess.check_output(['readelf','-d',str(p)],text=True);needed=re.findall(r'\(NEEDED\).*?\[([^]]+)\]',dynamic);queue+=needed
 if not (libdir/name).exists():(libdir/name).symlink_to(p)
 else:assert (libdir/name).resolve()==p.resolve()
 rec['providers'].append({'name':name,'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'needed':needed})
ld='/home/tv/.cache/archtv/aosp16-qpr2/native-toolchain-1/bin/ld.lld';cmd=[ld,'--error-limit=0','--no-undefined','--no-allow-shlib-undefined','-pie','--dynamic-linker=/system/bin/linker64','-z','relro','-z','now','--rpath-link='+str(libdir),str(r/'dist/aosp16/crt-native-1/crtbegin_dynamic.o')]+[str(out/(Path(x['source']).stem+'.o')) for x in state['results']]+[str(obj),'-L'+str(libdir)]+['-l:'+n for n in direct]+[str(cache/'compiler-builtins/libclang_rt.builtins-x86_64-android.a'),str(r/'dist/aosp16/crt-native-1/crtend_android.o'),'-o',str(out/'hwc3-wayland')]
x=subprocess.run(cmd,capture_output=True,text=True,timeout=90);rec['link']={'argv':cmd,'exit':x.returncode,'stdout':x.stdout,'stderr':x.stderr};(out/'link.json').write_text(json.dumps(rec,indent=2)+'\n');print('STRICT LINK',x.returncode,x.stderr[:12000],flush=True)

raise SystemExit(x.returncode)
