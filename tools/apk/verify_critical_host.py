#!/usr/bin/env python3
"""Verify the typed host-to-CriticalNative calling convention in ART."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
for name in ('sources', 'androidfw-sources', 'framework', 'art', 'tools', 'output'):
    parser.add_argument('--'+name, type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
source_cache, cache = args.sources.resolve(), args.androidfw_sources.resolve()
helper = next(c for c in json.loads((root/'runtime/aosp/hwui-sources.json').read_text())['components'] if c['name']=='nativehelper')
jni = source_cache/'nativehelper/include_jni/jni.h'
if sha(jni) != helper['files']['include_jni/jni.h']['sha256']:
    raise SystemExit('Original JNI header modified')
libcxx = next(c for c in json.loads((root/'runtime/aosp/androidfw-sources.json').read_text())['components'] if c['name']=='libcxx')
for name, expected in libcxx['files'].items():
    if sha(cache/'libcxx'/name) != expected['sha256']:
        raise SystemExit('Original libc++ headers modified')
fproof = json.loads((args.framework/'provenance.json').read_text())
reference = Path.home()/'.cache/archtv/aosp-compile-tools/android-all-13.jar'
if sha(reference) != fproof['compile_reference']['sha256']:
    raise SystemExit('Compile reference modified')
tools, art = args.tools.resolve(), args.art.resolve()
for item in json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())['artifacts']:
    if item['file'] in ('r8.jar','android.jar') and sha(tools/item['file']) != item['sha256']:
        raise SystemExit('DEX tool modified')
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
for name in ('classes','dex','art-data'):
    (out/name).mkdir(mode=0o700)
fixture = root/'fixtures/aosp-critical-host'
header = root/'runtime/aosp/native/critical-host-adapter.h'
cpp = ['clang++','-std=c++17','-nostdinc++','-isystem',str(cache/'libcxx'),
       '-I'+str(jni.parent),'-I'+str(header.parent)]
commands = [
    [*cpp,'-shared','-fPIC','-O1','-nostdlib++','-Wl,--no-undefined',str(fixture/'native-probe.cpp'),'-o',str(out/'libcritical_probe.so')],
    ['/usr/lib/jvm/java-17-openjdk/bin/javac','--release','8','-classpath',str(reference),'-d',str(out/'classes'),str(fixture/'CriticalHostProbe.java')],
    ['/usr/lib/jvm/java-17-openjdk/bin/jar','cf',str(out/'probe.jar'),'-C',str(out/'classes'),'.'],
    ['/usr/lib/jvm/java-17-openjdk/bin/java','-cp',str(tools/'r8.jar'),'com.android.tools.r8.D8','--release','--min-api','28','--lib',str(tools/'android.jar'),'--output',str(out/'dex'),str(out/'probe.jar')],
]
(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
for i,command in enumerate(commands):
    with (out/(str(i)+'.build.log')).open('w') as log:
        subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
bad = out/'object-argument.cpp'
bad.write_text('#include "critical-host-adapter.h"\nstatic jint invalid(JNIEnv*,jclass,jobject){return 0;}\nauto entry = &archtv::aosp::CriticalHostAdapter<&invalid>::call;\n')
negative = subprocess.run([*cpp,'-fsyntax-only',str(bad)],capture_output=True,text=True,timeout=30)
(out/'object-argument.stderr').write_text(negative.stderr)
if negative.returncode==0 or 'CriticalNative arguments must be primitive' not in negative.stderr:
    raise SystemExit('Object argument was not rejected')
environment = {k:v for k,v in os.environ.items() if not k.startswith('ANDROID_') and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','CLASSPATH')}
environment.update(ANDROID_DATA=str(out/'art-data'),ANDROID_LOG_TAGS='*:w')
command = [str(art/'bin/art'),'--64','--no-compile','--','-Xint','-Xcheck:jni','-cp',str(out/'dex/classes.dex'),
           'org.archtv.aospprobe.CriticalHostProbe',str(out/'libcritical_probe.so')]
run = subprocess.run(command,capture_output=True,text=True,env=environment,timeout=30)
(out/'art.stdout').write_text(run.stdout)
(out/'art.stderr').write_text(run.stderr)
passed = run.returncode==0 and 'ART_CRITICAL_HOST_ABI_OK signatures=8 calls=2298' in run.stdout
sources = [header,fixture/'native-probe.cpp',fixture/'CriticalHostProbe.java']
(out/'result.json').write_text(json.dumps({'critical_host_abi_pass':passed,'exit_code':run.returncode,'command':command,
    'object_argument_compile_rejected':True,'sources_sha256':{str(p.relative_to(root)):sha(p) for p in sources},
    'verifier_sha256':sha(Path(__file__)),'original_jni_header_sha256':sha(jni),'compile_reference_sha256':sha(reference),
    'probe_dex_sha256':sha(out/'dex/classes.dex'),'library_sha256':sha(out/'libcritical_probe.so'),
    'scope':'Eight fixture-defined native signatures adapted to ART CriticalNative, primitive-only guard. No original RenderNode JNI execution, graphics or rendering claim.'},indent=2)+'\n')
print(json.dumps({'critical_host_abi_pass':passed}))
if not passed:
    raise SystemExit(1)
