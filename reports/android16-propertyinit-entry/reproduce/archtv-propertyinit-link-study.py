from pathlib import Path
import json,subprocess,sys,hashlib
r=Path('/home/tv/repositorio-principal');sys.path.insert(0,str(r/'tools/aosp'));from audit_boot_inputs import inside
out=r/'dist/aosp16/propertyinit-link-1';out.mkdir();root=r/'dist/aosp16/factory-inputs-3/root';state=json.loads((r/'dist/aosp16/libinit-native-finalize-1/state.json').read_text());src=out/'entry.cpp';src.write_text('#include "property_service.h"\n#include <stdio.h>\nint main() { android::init::PropertyInit(); puts("PROPERTY_INIT_RETURNED"); return 0; }\n')
base=state['common_argv'];core=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/system-core/source/system/core/init');cmd=base+['-I'+str(core),'-c',str(src),'-o',str(out/'entry.o')];p=subprocess.run(cmd,capture_output=True,text=True);rows=[dict(argv=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)];assert p.returncode==0,p.stderr
shared=['libbase','libcutils','libdl','libext4_utils','libfs_mgr','libgsi','liblog','liblogwrap','liblp','libprocessgroup','libprocessgroup_setup','libselinux','libunwindstack','libutils','libvendorsupport','libc++','libc','libm']
libs=[];absent=[]
for name in shared:
 p=inside(root,'/system/lib64/'+name+'.so')
 if p.is_file():libs.append(str(p))
 else:absent.append(name)
archives=[r/'dist/aosp16/libinit-native-archive-1/libinit-native-prototype.a',r/'dist/aosp16/property-libs-native-1/libpropertyinfoparser.a',r/'dist/aosp16/property-libs-native-1/libpropertyinfoserializer.a',r/'dist/aosp16/genfslabelsversion-native-1/libgenfslabelsversion.a']+list((r/'dist/aosp16/aconfig-original-1').glob('*/*.a'))+[r/'dist/aosp16/snapshot-support-native-1/libsnapshot_messages.a']
cmd=['/home/tv/.cache/archtv/aosp16-qpr2/native-toolchain-1/bin/ld.lld','-pie','--dynamic-linker','/system/bin/linker64','--build-id=sha1','--no-undefined','--error-limit=0','--gc-sections','-z','relro','-z','now',str(r/'dist/aosp16/crt-native-1/crtbegin_dynamic.o'),str(out/'entry.o'),'--start-group']+[str(p) for p in archives]+['--end-group']+libs+[str(r/'dist/aosp16/crt-native-1/crtend_android.o'),'-o',str(out/'entry')];p=subprocess.run(cmd,capture_output=True,text=True);rows.append(dict(argv=cmd,exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr));(out/'results.json').write_text(json.dumps({'scope':'Link study, never executed; missing static modules not substituted with shared ABI guesses or stubs','missing_declared_shared':absent,'attempts':rows},indent=2)+'\n');print('link exit',p.returncode,'missing shared',absent);print(p.stderr[:16000])
