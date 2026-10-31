from pathlib import Path
import subprocess,json,hashlib,re,importlib.util,sys
r=Path('/home/tv/repositorio-principal');source=r/'dist/aosp16/minigbm-native-4';o=r/'dist/aosp16'/sys.argv[1];o.mkdir();state=json.loads((source/'build.json').read_text());assert state.get('terminal');assert len(state['sources'])==23
for row in state['sources']:assert hashlib.sha256(Path(row['object']).read_bytes()).hexdigest()==row['object_sha256']
libdir=o/'link-libs';libdir.mkdir();root=r/'dist/aosp16/factory-inputs-3/root';spec=importlib.util.spec_from_file_location('audit',r/'tools/aosp/audit_boot_inputs.py');audit=importlib.util.module_from_spec(spec);spec.loader.exec_module(audit)
direct=['libbase.so','libbinder_ndk.so','libcutils.so','libdmabufheap.so','libdrm.so','libgralloctypes.so','libhidlbase.so','liblog.so','libnativewindow.so','libsync.so','libutils.so','android.hardware.graphics.allocator-V2-ndk.so','android.hardware.graphics.mapper@4.0.so','android.hardware.common-V2-ndk.so','android.hardware.graphics.common-V7-ndk.so','libc++.so','libc.so','libm.so','libdl.so'];queue=list(direct);seen=set();providers=[]
while queue:
 name=queue.pop(0)
 if name in seen:continue
 seen.add(name);logical=('/apex/com.android.runtime/lib64/bionic/' if name in ['libc.so','libm.so','libdl.so','libdl_android.so'] else '/system/lib64/')+name;source=audit.inside(root,logical)
 if name=='libui.so':source=r/'dist/aosp16/libui-link-2/libui.so'
 assert source.is_file(),str(source)
 needed=re.findall(r'\(NEEDED\).*?\[([^]]+)\]',subprocess.check_output(['readelf','-d',str(source)],text=True));queue+=needed;(libdir/name).symlink_to(source);providers.append({'name':name,'path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'needed':needed})
ld='/home/tv/.cache/archtv/aosp16-qpr2/native-toolchain-1/bin/ld.lld';crt=r/'dist/aosp16/hwc2on1-build-1';rec={'scope':'Whole minigbm modules strict linkage against real Bionic providers, platform-profile only; not vendor namespace, runtime allocation, HWC or APK acceptance','providers':providers,'links':[]};groups={}
for row in state['sources']:groups.setdefault(row['module'],[]).append(row['object'])
for name,objects,deps in [('libminigbm_gralloc.so',groups['core']+groups['common'],direct),('libminigbm_gralloc4_utils.so',groups['utils'],direct+['libminigbm_gralloc.so']),('mapper.minigbm.so',groups['mapper']+groups['utils'],direct+['libminigbm_gralloc.so']),('android.hardware.graphics.allocator-service.minigbm',groups['allocator']+[str(r/'dist/aosp16/hwc3-frontend-2/NativeHandle.o')],direct+['libminigbm_gralloc.so','libminigbm_gralloc4_utils.so'])]:
 shared=name.endswith('.so');begin=str(crt/'crtbegin_so.c.o') if shared else str(r/'dist/aosp16/crt-native-1/crtbegin_dynamic.o');end=str(crt/'crtend_so.S.o') if shared else str(r/'dist/aosp16/crt-native-1/crtend_android.o');cmd=[ld,'--as-needed','--no-undefined','--no-allow-shlib-undefined','--error-limit=0','-z','relro','-z','now','--rpath-link='+str(libdir)]+(['-shared','--soname='+name] if shared else ['-pie','--dynamic-linker=/system/bin/linker64'])+[begin]+objects+['-L'+str(libdir)]+['-l:'+n for n in deps]+[str(Path('/home/tv/.cache/archtv/graphics-candidates-1/compiler-builtins/libclang_rt.builtins-x86_64-android.a')),end,'-o',str(o/name)]
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=90);rec['links'].append({'name':name,'argv':cmd,'exit':p.returncode,'stderr':p.stderr});(o/'link.json').write_text(json.dumps(rec,indent=2)+'\n');print('LINK',name,p.returncode,p.stderr[:3500],flush=True)
 if p.returncode:raise SystemExit(p.returncode)
 (libdir/name).symlink_to(o/name)
rec['terminal']=True;rec['artifacts']=[{'path':str(o/row['name']),'sha256':hashlib.sha256((o/row['name']).read_bytes()).hexdigest()} for row in rec['links']];(o/'link.json').write_text(json.dumps(rec,indent=2)+'\n')
