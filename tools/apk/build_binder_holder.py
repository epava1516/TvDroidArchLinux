#!/usr/bin/env python3
"""Build the original Binder holder JNI on Linux, without Binder IPC initialization."""
import argparse,hashlib,json,subprocess
from pathlib import Path
p=argparse.ArgumentParser()
for n in ('sources','androidfw-sources','androidfw-build','hwui-sources','art','output'):p.add_argument('--'+n,type=Path,required=True)
a=p.parse_args();root=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
sources=a.sources.resolve();cache=a.androidfw_sources.resolve();native=a.androidfw_build.resolve();hwui=a.hwui_sources.resolve();art=a.art.resolve()
manifest_hashes={}
for manifest,directory in [('binder',sources),('androidfw',cache),('hwui',hwui)]:
 path=root/'runtime/aosp'/(manifest+'-sources.json');manifest_hashes[manifest]=sha(path)
 m=json.loads(path.read_text())
 for c in m['components']:
  for name,expected in c['files'].items():
   path=directory/c['name']/name
   assert path.is_file() and sha(path)==expected['sha256'],str(path)
proof=json.loads((native/'provenance.json').read_text());recipe=json.loads((root/'runtime/aosp/androidfw-build.json').read_text())
libcxx=art/'lib64/libc++.so';assert sha(libcxx)==proof['libcxx_runtime_sha256']
archives=[]
for name,digest in proof['archives'].items():
 path=native/name;assert sha(path)==digest;archives.append(path)
out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
own=root/'runtime/aosp/native/binder-holder-jni.cpp';obj=out/'binder-holder.o';lib=out/'libarchtv_binder_holder.so'
atomic=hwui/'skia/third_party/externals/bionic-headers/stdatomic.h'
bionic=next(c for c in json.loads((root/'runtime/aosp/skia-extra-sources.json').read_text())['components'] if c['name']=='bionic-headers')
assert sha(atomic)==bionic['files']['stdatomic.h']['sha256']
headers=out/'host-headers';headers.mkdir();(headers/'stdatomic.h').write_bytes(atomic.read_bytes())
inc=[headers]+[sources/x for x in ['binder/include','binderthreadstate/include','hwbinder/include','core-jni','core-jni/include']]+[hwui/x for x in ['nativehelper/include','nativehelper/include_jni','nativehelper/include_platform','nativehelper/header_only_include']]+[cache/x for x in recipe['includes']]
flags=['clang++','-std=gnu++20','-nostdinc++','-isystem',str(cache/'libcxx'),'-fPIC','-O1','-g0','-fno-rtti','-fvisibility=hidden','-ffunction-sections','-fdata-sections','-DSTATIC_ANDROIDFW_FOR_TOOLS','-DFMT_HEADER_ONLY','-DNDEBUG',*['-I'+str(x) for x in inc]]
version=out/'exports.map';version.write_text('{ global: Java_android_os_Binder_getNativeBBinderHolder; Java_android_os_Binder_getNativeFinalizer; local: *; };\n')
commands=[[*flags,'-c',str(own),'-o',str(obj)],['clang++','-shared','-nostdlib++','-Wl,--gc-sections','-Wl,--no-undefined','-Wl,--version-script='+str(version),'-L'+str(libcxx.parent),'-Wl,-rpath,'+str(libcxx.parent),str(obj),'-Wl,--start-group',*map(str,archives),'-Wl,--end-group','-lc++','-lz','-ldl','-lpthread','-lm','-o',str(lib)]]
result={'build_pass':False,'manifest_sha256':manifest_hashes,'builder_sha256':sha(Path(__file__)),'recipe_sha256':sha(root/'runtime/aosp/androidfw-build.json'),'commands':commands,'own_source_sha256':sha(own),'original_jni_sha256':sha(sources/'core-jni/android_util_Binder.cpp'),'original_stdatomic_sha256':sha(atomic),'archives':proof['archives'],'libcxx_sha256':sha(libcxx),'compiler':subprocess.check_output(['clang++','--version'],text=True)}
for i,cmd in enumerate(commands):
 with (out/('build-'+str(i)+'.log')).open('w') as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,timeout=120)
 if r.returncode:
  result['failed_step']=i;result['exit_code']=r.returncode;break
else:
 symbols=subprocess.check_output(['nm','-D','--defined-only',str(lib)],text=True)
 (out/'exports.txt').write_text(symbols)
 assert {line.split()[-1] for line in symbols.splitlines()}=={'Java_android_os_Binder_getNativeBBinderHolder','Java_android_os_Binder_getNativeFinalizer'}
 result.update(build_pass=True,library_sha256=sha(lib))
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if not result['build_pass']:raise SystemExit('Binder holder build failed; inspect '+str(out))
print(lib)
