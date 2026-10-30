#!/usr/bin/env python3
"""Exercise the original HWUI interpolator factory and C++ objects in ART."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
for name in ('sources', 'androidfw-sources', 'androidfw-build', 'framework', 'art', 'tools', 'output'):
    parser.add_argument('--'+name, type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
sources, cache = args.sources.resolve(), args.androidfw_sources.resolve()
manifests = {}
for name, directory in [('hwui', sources), ('androidfw', cache)]:
    path = root/'runtime/aosp'/(name+'-sources.json')
    manifests[name] = sha(path)
    for component in json.loads(path.read_text())['components']:
        for filename, expected in component['files'].items():
            p = directory/component['name']/filename
            if not p.is_file() or sha(p) != expected['sha256']:
                raise SystemExit('Original source mismatch: '+str(p))
framework, native, art, tools = [p.resolve() for p in (args.framework, args.androidfw_build, args.art, args.tools)]
fproof = json.loads((framework/'provenance.json').read_text())
if sha(framework/'framework.jar') != fproof['framework_jar_sha256'] or sha(framework/'dex/classes.dex') != fproof['dex_sha256']:
    raise SystemExit('Original framework build modified')
recipe = json.loads((root/'runtime/aosp/androidfw-build.json').read_text())
native_proof = json.loads((native/'provenance.json').read_text())
archives = []
for name, expected in native_proof['archives'].items():
    p = native/name
    if sha(p) != expected:
        raise SystemExit('Native archive modified: '+name)
    archives.append(p)
libcxx = art/'lib64/libc++.so'
if sha(libcxx) != native_proof['libcxx_runtime_sha256']:
    raise SystemExit('ART libc++ mismatch')
for item in json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())['artifacts']:
    if item['file'] in ('r8.jar', 'android.jar') and sha(tools/item['file']) != item['sha256']:
        raise SystemExit('DEX tool mismatch')
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
for name in ('classes', 'dex', 'art-data'):
    (out/name).mkdir(mode=0o700)
own_sources = [root/'runtime/aosp/native/interpolators-jni.cpp',
               root/'fixtures/aosp-native-interpolators/native-probe.cpp',
               root/'fixtures/aosp-native-interpolators/NativeInterpolatorsProbe.java']
include = [cache/p for p in recipe['includes']]
include += [sources/p for p in ['hwui', 'hwui/jni', 'nativehelper/include', 'nativehelper/include_jni',
                               'nativehelper/include_platform', 'nativehelper/header_only_include']]
commands = [
    ['clang++', '-shared', '-std=gnu++20', '-fPIC', '-O1', '-g0', '-fvisibility=hidden',
     '-ffunction-sections', '-fdata-sections', '-nostdinc++', '-isystem', str(cache/'libcxx'),
     *['-I'+str(p) for p in include], *map(str, own_sources[:2]), str(sources/'hwui/Interpolator.cpp'),
     '-Wl,--gc-sections', '-Wl,--no-undefined', '-nostdlib++', '-L'+str(libcxx.parent),
     '-Wl,-rpath,'+str(libcxx.parent), '-Wl,--start-group', *map(str, archives), '-Wl,--end-group',
     '-lc++', '-lz', '-ldl', '-lpthread', '-lm', '-o', str(out/'libinterpolator_probe.so')],
    ['/usr/lib/jvm/java-17-openjdk/bin/javac', '--release', '8', '-classpath', str(framework/'framework.jar'),
     '-d', str(out/'classes'), str(own_sources[2])],
    ['/usr/lib/jvm/java-17-openjdk/bin/jar', 'cf', str(out/'probe.jar'), '-C', str(out/'classes'), '.'],
    ['/usr/lib/jvm/java-17-openjdk/bin/java', '-cp', str(tools/'r8.jar'), 'com.android.tools.r8.D8',
     '--release', '--min-api', '28', '--lib', str(tools/'android.jar'), '--output', str(out/'dex'), str(out/'probe.jar')],
]
(out/'commands.json').write_text(json.dumps(commands, indent=2)+'\n')
for i, command in enumerate(commands):
    with (out/(str(i)+'.build.log')).open('w') as log:
        subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
with zipfile.ZipFile(out/'probe.jar') as jar:
    if any(p.startswith('android/') for p in jar.namelist()):
        raise SystemExit('Probe must not provide Android API implementations')
environment = {k: v for k, v in os.environ.items()
               if not k.startswith('ANDROID_') and k not in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'CLASSPATH')}
environment.update(ANDROID_DATA=str(out/'art-data'), ANDROID_LOG_TAGS='*:w')
command = [str(art/'bin/art'), '--64', '--no-compile', '--', '-Xint', '-Xcheck:jni', '-cp',
           str(framework/'dex/classes.dex')+':'+str(out/'dex/classes.dex'),
           'org.archtv.aospprobe.NativeInterpolatorsProbe', str(out/'libinterpolator_probe.so')]
run = subprocess.run(command, capture_output=True, text=True, env=environment, timeout=30)
(out/'art.stdout').write_text(run.stdout)
(out/'art.stderr').write_text(run.stderr)
expected = 'AOSP_NATIVE_INTERPOLATORS_OK factories=11 objects=222 samples=3102 java_parity=2'
passed = run.returncode == 0 and expected in run.stdout
(out/'result.json').write_text(json.dumps({
    'original_native_interpolators_pass': passed, 'exit_code': run.returncode, 'command': command,
    'scope': '11 original JNI factories, native C++ interpolation and controlled release; two original Java/native parity checks. No frame clock, RenderNode, CriticalNative or rendered animation claim.',
    'manifests': manifests, 'sources_sha256': {str(p.relative_to(root)): sha(p) for p in own_sources},
    'verifier_sha256': sha(Path(__file__)), 'framework_dex_sha256': fproof['dex_sha256'],
    'native_provenance_sha256': sha(native/'provenance.json'), 'libcxx_sha256': sha(libcxx),
    'library_sha256': sha(out/'libinterpolator_probe.so'), 'probe_dex_sha256': sha(out/'dex/classes.dex'),
}, indent=2)+'\n')
print(json.dumps({'original_native_interpolators_pass': passed}))
if not passed:
    raise SystemExit(1)
