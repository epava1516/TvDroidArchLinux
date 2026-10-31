from pathlib import Path
import json,subprocess,hashlib,time
r=Path('/home/tv/repositorio-principal');cache=Path('/home/tv/.cache/archtv/graphics-candidates-1');wl=cache/'wayland';ffi=cache/'libffi';out=r/'dist/aosp16/wayland-client-1';out.mkdir(exist_ok=True);gen=out/'generated';gen.mkdir();rec={'scope':'Whole original AOSP Wayland client + full Android.bp x86_64 libffi implementation; source scanner is host-only. Strict native linkage is not execution/graphics/APK acceptance.','commands':[]}
def run(cmd,seconds=90):
 t=time.monotonic();p=subprocess.run(cmd,capture_output=True,text=True,timeout=seconds);rec['commands'].append({'argv':list(map(str,cmd)),'exit':p.returncode,'seconds':time.monotonic()-t,'stdout':p.stdout,'stderr':p.stderr});(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n');print(Path(str(cmd[0])).name,p.returncode,p.stderr[:1300],flush=True)
 if p.returncode:raise SystemExit(p.returncode)
 return p
for base in [wl,ffi]:
 inventory=json.loads((base/'source-inventory.json').read_text())
 for row in inventory['files']:
  p=base/row['path'];data=p.readlink().as_posix().encode() if p.is_symlink() else p.read_bytes();assert hashlib.sha256(data).hexdigest()==row['sha256'],str(p)
run(['/usr/bin/cc','-D_GNU_SOURCE','-std=gnu11','-I'+str(wl),'-I'+str(wl/'src'),str(wl/'src/scanner.c'),str(wl/'src/wayland-util.c'),'-lexpat','-o',str(out/'wayland-scanner')])
for mode,name in [('client-header','wayland-client-protocol.h'),('private-code','wayland-protocol-private.c')]:run([str(out/'wayland-scanner'),'-s',mode,str(wl/'protocol/wayland.xml'),str(gen/name)])
p=subprocess.run(['/bin/bash',str(ffi/'gen_ffi_header.sh')],input=(ffi/'include/ffi.h.in').read_bytes(),capture_output=True,timeout=10);assert p.returncode==0,p.stderr;(gen/'ffi_gen.h').write_bytes(p.stdout)
rec['ffi_header']={'generator_sha256':hashlib.sha256((ffi/'gen_ffi_header.sh').read_bytes()).hexdigest(),'input_sha256':hashlib.sha256((ffi/'include/ffi.h.in').read_bytes()).hexdigest(),'output_sha256':hashlib.sha256(p.stdout).hexdigest()}
old=json.loads((r/'reports/android16-libui-link/native-compile.json').read_text())['results'][0]['argv'];system=[]
for i,arg in enumerate(old[:-1]):
 if arg=='-isystem' and ('bionic-libc' in old[i+1] or '/clang/21/include' in old[i+1]):system+=['-isystem',old[i+1]]
flags=[old[0],'--target=x86_64-linux-android36','-std=gnu11','-nostdinc','-fPIC','-O2','-g0','-D_GNU_SOURCE']+system+['-I'+str(p) for p in [gen,ffi/'linux-x86_64',ffi/'include',ffi/'src/x86',wl,wl/'src']]
ffisources=[ffi/'src'/p for p in ['closures.c','debug.c','java_raw_api.c','prep_cif.c','raw_api.c','types.c','x86/ffi64.c','x86/ffiw64.c','x86/unix64.S','x86/win64.S']];wlsources=[wl/'src'/p for p in ['connection.c','wayland-client.c','wayland-os.c','wayland-util.c']]+[gen/'wayland-protocol-private.c'];objects=[];rec['sources']=[]
for p in ffisources+wlsources:
 obj=out/(p.stem+'.o');cmd=[v for v in flags if not(v=='-std=gnu11' and p.suffix=='.S')]+(['-DHAVE_AS_X86_PCREL','-DHAVE_AS_ASCII_PSEUDO_OP'] if p.suffix=='.S' else [])+['-c',str(p),'-o',str(obj)];run(cmd);objects.append(obj);rec['sources'].append({'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'object_sha256':hashlib.sha256(obj.read_bytes()).hexdigest()})
run(['/usr/bin/llvm-ar','rcs',str(out/'libwayland-client-bionic.a')]+list(map(str,objects)))
lib=r/'dist/aosp16/factory-inputs-3/root/apex/com.android.runtime/lib64/bionic';ld='/home/tv/.cache/archtv/aosp16-qpr2/native-toolchain-1/bin/ld.lld';crt=r/'dist/aosp16/hwc2on1-build-1';run([ld,'--no-undefined','--no-allow-shlib-undefined','-shared','--soname=libwayland-client-bionic.so','-z','relro','-z','now',str(crt/'crtbegin_so.c.o')]+list(map(str,objects))+[str(lib/('lib'+n+'.so')) for n in ['c','m','dl']]+[str(cache/'compiler-builtins/libclang_rt.builtins-x86_64-android.a'),str(crt/'crtend_so.S.o'),'-o',str(out/'libwayland-client-bionic.so')])
rec['terminal']=True;rec['artifacts']=[{'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in [out/'wayland-scanner',out/'libwayland-client-bionic.a',out/'libwayland-client-bionic.so']];(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n')
