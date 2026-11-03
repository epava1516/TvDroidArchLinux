#!/usr/bin/env python3
"""Build pinned original libxml2 Android static variant for bootstrap, not an API shim."""
from pathlib import Path
import concurrent.futures, hashlib, json, re, shutil, subprocess, sys
repo=Path(__file__).resolve().parents[2]
root=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/libxml2-target/source/external/libxml2')
out=(repo/sys.argv[1]).resolve();out.mkdir()
cache=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs')
clang=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-toolchain-1/bin/clang-21')
ar=Path(shutil.which('llvm-ar'));assert ar.is_file()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
bp=(root/'Android.bp').read_text();section=bp[bp.index('name: "libxml2-defaults"'):];section=section[:section.index('stl:')]
files=re.findall(r'"([^"\n]+\.c)"',section);assert len(files)>25 and len(files)==len(set(files))
# Exact original Android static profile: original xmlversion.h disables ICU
# for __ANDROID__ && STATIC_LIBXML; no source/header patch or stub is used.
argv=[str(clang),'--target=x86_64-linux-android36','-std=gnu11','-nostdinc','-O2','-g0','-fPIC','-ffunction-sections','-fdata-sections','-DSTATIC_LIBXML=1','-fvisibility=hidden','-DANDROID','-I'+str(root),'-I'+str(root/'include')]
for folder in [cache/'clang21-builtins/source/prebuilts/clang/host/linux-x86/clang-r563880c/lib/clang/21/include',cache/'bionic-libc/source/include',cache/'bionic-libc/source/kernel/uapi/asm-x86',cache/'bionic-libc/source/kernel/uapi',cache/'bionic-libc/source/kernel/android/uapi']:
 assert folder.is_dir();argv+=['-isystem',str(folder)]
inputs={str(p.relative_to(root)):sha(p) for p in sorted(root.rglob('*')) if p.is_file() and (p.suffix in ['.h','.c'] or p.name=='Android.bp')}
record={'scope':'Original complete libxml2 source/static Android build, compilation only; strict cohort link and actual bootstrap execution required','source':str(root),'source_sha256':inputs,'provenance':json.loads((cache/'libxml2-target/provenance.json').read_text()),'compiler':str(clang),'compiler_sha256':sha(clang),'archiver':str(ar),'archiver_sha256':sha(ar),'profile':'Original Android.bp static flags STATIC_LIBXML=1, hidden; original header disables ICU','commands':[]}
(out/'input.json').write_text(json.dumps(record,indent=2)+'\n')
def compile_one(name):
 args=argv+['-c',str(root/name),'-o',str(out/(name+'.o'))];p=subprocess.run(args,text=True,capture_output=True)
 (out/(name+'.stderr.log')).write_text(p.stderr)
 return {'source':name,'argv':args,'exit':p.returncode,'stderr':str(out/(name+'.stderr.log'))}
with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:record['commands']=list(pool.map(compile_one,files))
(out/'build.json').write_text(json.dumps(record,indent=2)+'\n');assert all(c['exit']==0 for c in record['commands']),'Original XML compile failed; inspect per-source stderr'
archive=out/'libxml2-bootstrap.a';args=[str(ar),'rcs',str(archive),*[str(out/(n+'.o')) for n in files]];p=subprocess.run(args,text=True,capture_output=True);assert p.returncode==0,p.stderr
record.update(archive=str(archive),archive_sha256=sha(archive),archive_argv=args,terminal=True)
(out/'artifact.json').write_text(json.dumps(record,indent=2)+'\n');print(str(archive))
