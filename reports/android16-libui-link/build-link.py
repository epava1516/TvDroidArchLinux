from pathlib import Path
import json,subprocess,hashlib,importlib.util,re
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/libui-link-1';out.mkdir();d=out/'link-libs';d.mkdir();cache=Path('/home/tv/.cache/archtv/graphics-candidates-1');rows=json.loads((r/'reports/android16-libui-implementation/compiled-units.json').read_text())['results'];last=json.loads((r/'reports/android16-libui-implementation/compile-attempt-3.json').read_text())['results'][0]['argv'];flags=last[:last.index('-MMD')];objects=[x['argv'][x['argv'].index('-o')+1] for x in rows];rec={'scope':'Original complete libui source module strict link against original GSI providers; no runtime/Soong equivalence/APK acceptance','compile':[],'providers':[]}
for src in [cache/'hardware-interfaces/common/support/NativeHandle.cpp',Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/system-core/source/system/core/libgrallocusage/GrallocUsageConversion.cpp')]:
 obj=out/(src.stem+'.o');cmd=flags+['-c',str(src),'-o',str(obj)];x=subprocess.run(cmd,capture_output=True,text=True,timeout=120);rec['compile'].append({'argv':cmd,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'exit':x.returncode,'stderr':x.stderr});(out/'state.json').write_text(json.dumps(rec,indent=2)+'\n');print(src.name,x.returncode,x.stderr[:1400],flush=True);assert x.returncode==0;objects.append(str(obj))
sp=importlib.util.spec_from_file_location('audit',r/'tools/aosp/audit_boot_inputs.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);root=r/'dist/aosp16/factory-inputs-3/root';queue=['libui.so'];seen=set();direct=[]
while queue:
 name=queue.pop(0)
 if name in seen:continue
 seen.add(name);logical=('/apex/com.android.runtime/lib64/bionic/' if name in ['libc.so','libdl.so','libm.so'] else '/system/lib64/')+name;f=m.inside(root,logical)
 if not f.is_file():raise RuntimeError('Original provider missing '+logical)
 text=subprocess.check_output(['readelf','-d',str(f)],text=True);needed=re.findall(r'\(NEEDED\).*?\[([^]]+)\]',text);queue+=needed
 if name=='libui.so':direct=needed;continue
 (d/name).symlink_to(f);rec['providers'].append({'logical':logical,'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'needed':needed})
ld='/home/tv/.cache/archtv/aosp16-qpr2/native-toolchain-1/bin/ld.lld';crt=r/'dist/aosp16/hwc2on1-build-1';builtins='/home/tv/.cache/archtv/graphics-candidates-1/compiler-builtins/libclang_rt.builtins-x86_64-android.a';cmd=[ld,'-shared','--soname=libui.so','--no-undefined','--no-allow-shlib-undefined','-z','relro','-z','now','--rpath-link='+str(d),str(crt/'crtbegin_so.c.o')]+objects+['-L'+str(d)]+['-l:'+n for n in direct]+[builtins,str(crt/'crtend_so.S.o'),'-o',str(out/'libui.so')];x=subprocess.run(cmd,capture_output=True,text=True,timeout=90);rec['link']={'argv':cmd,'exit':x.returncode,'stderr':x.stderr};rec['terminal']=True;(out/'state.json').write_text(json.dumps(rec,indent=2)+'\n');print('STRICT_LINK',x.returncode,x.stderr[:7000],flush=True)
