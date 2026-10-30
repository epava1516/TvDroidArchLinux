#!/usr/bin/env python3
"""Check original resource Java classes on host ART with the Linux JNI adapter."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import zipfile

parser = argparse.ArgumentParser()
for name in ('art', 'java-build', 'native-build', 'output'):
    parser.add_argument('--'+name, type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
java_build = args.java_build.resolve()
native_build = args.native_build.resolve()
dex = java_build/'dex/classes.dex'
library = native_build/'libarchtv_resources_linux.so'
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
java_proof = json.loads((java_build/'provenance.json').read_text())
native_proof = json.loads((native_build/'provenance.json').read_text())
assert sha(dex) == java_proof['dex_sha256']
assert sha(library) == native_proof['jni_library_sha256']
for name in ('AssetManager', 'ApkAssets', 'StringBlock'):
    assert 'android/content/res/'+name+'.class' in java_proof['runtime_classes']
assert not any(name.startswith(('java/', 'org/robolectric/')) for name in java_proof['runtime_classes'])
apk = root/'fixtures/apk/counter/golden/counter.apk'
assert sha(apk) == 'f07c9b92ab3353237276081c22e11ce06168b8c9f71a99ea32968b2ce0f00e28'
with zipfile.ZipFile(apk) as archive:
    content = {name: archive.read(name) for name in archive.namelist()}
assert content['resources.arsc'].count(b'Contador:') == 1
cases = [('original-1', apk, [], None), ('original-2', apk, [], None)]
for label, table, text, error in [
    ('variant', content['resources.arsc'].replace(b'Contador:', b'Registro:'), ['Registro:'], None),
    ('truncated', content['resources.arsc'][:20], [], b'java.io.IOException')]:
    path = out/(label+'-unsigned.apk')
    with zipfile.ZipFile(path, 'w') as archive:
        for name, data in content.items():
            archive.writestr(name, table if name == 'resources.arsc' else data)
    with zipfile.ZipFile(path) as archive:
        assert archive.read('classes.dex') == content['classes.dex']
    cases.append((label, path, text, error))
cases.append(('missing-apk', out/'absent.apk', [], b'java.io.IOException'))
env = {key: value for key, value in os.environ.items()
       if not key.startswith('ANDROID_') and key not in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'CLASSPATH')}
env['ANDROID_LOG_TAGS'] = '*:w'
results = []
for label, path, extra, error in cases:
    data = out/(label+'-art-data')
    data.mkdir(mode=0o700)
    env['ANDROID_DATA'] = str(data)
    command = [str(args.art.resolve()/'bin/art'), '--64', '--no-compile', '--', '-Xint', '-Xcheck:jni',
               '-cp', str(dex), 'org.archtv.aospprobe.ResourcesProbe', str(library), str(path), *extra]
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                          cwd=out, start_new_session=True) as process:
        try:
            stdout, stderr = process.communicate(timeout=30)
        except BaseException:
            try: os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            process.communicate()
            raise
    (out/(label+'.stdout')).write_bytes(stdout)
    (out/(label+'.stderr')).write_bytes(stderr)
    passed = (process.returncode == 0 and stdout.strip() == b'AOSP_RESOURCES_JNI_OK') if error is None else (
        process.returncode > 0 and error in stderr and b'AOSP_RESOURCES_JNI_OK' not in stdout)
    results.append({'case': label, 'exit_code': process.returncode, 'pass': passed, 'command': command})
    if not passed:
        raise SystemExit('Resource JNI case failed: '+label+'; see '+str(out))
(out/'result.json').write_text(json.dumps({'pass': True, 'cases': results, 'dex_sha256': sha(dex),
    'library_sha256': sha(library), 'apk_sha256': sha(apk),
    'scope': 'Original ApkAssets.loadFromPath, AssetManager identifier/value/text resolution, ActivityInfo configuration conversion and StringBlock cache via real ART JNI. Internal sentinel constructor bypasses system resource initialization only in probe. No Resources.getString, public constructor, Activity/View integration, styled text or general APK support claim.'}, indent=2)+'\n')
print(out/'result.json')
