#!/usr/bin/env python3
"""Probe original Resources initialization and preserve the exact runtime boundary."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess

parser = argparse.ArgumentParser()
for name in ('art', 'java-build', 'linux-library', 'resources-library', 'output'):
    parser.add_argument('--'+name, type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
dex = args.java_build.resolve()/'dex/classes.dex'
proof = json.loads((args.java_build/'provenance.json').read_text())
assert hashlib.sha256(dex.read_bytes()).hexdigest() == proof['dex_sha256']
assert not any(name.startswith('java/') for name in proof['runtime_classes'])
apk = root/'fixtures/apk/counter/golden/counter.apk'
assert hashlib.sha256(apk.read_bytes()).hexdigest() == 'f07c9b92ab3353237276081c22e11ce06168b8c9f71a99ea32968b2ce0f00e28'
env = {key: value for key, value in os.environ.items()
       if not key.startswith(('ANDROID_', 'ARCHTV_ANDROID_PROPERTY_')) and key not in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'CLASSPATH')}
env['ANDROID_LOG_TAGS'] = '*:w'
# Declared laboratory target: AOSP 13 API shape, x86_64 ART; not a compatibility claim.
host_properties = {'ro.build.version.sdk':'33', 'ro.build.version.codename':'REL',
                   'ro.build.version.all_codenames':'REL', 'ro.build.version.release':'13',
                   'ro.product.cpu.abilist':'x86_64', 'ro.product.cpu.abilist64':'x86_64',
                   'archtv.public.unicode':'Televisión 📺', 'archtv.public.true':'yes',
                   'archtv.public.false':'off', 'archtv.public.invalid':'TRUE'}
for key, value in host_properties.items():
    env['ARCHTV_ANDROID_PROPERTY_'+key] = value
results = {}
for label, extra, marker in [('reference', [], b'ART_REFERENCE_OK'), ('public-resources',
    [str(args.resources_library.resolve()), str(args.linux_library.resolve()), str(apk)], b'AOSP_PUBLIC_RESOURCES_OK')]:
    data = out/(label+'-art-data')
    data.mkdir(mode=0o700)
    env['ANDROID_DATA'] = str(data)
    command = [str(args.art.resolve()/'bin/art'), '--64', '--no-compile', '--', '-Xint', '-Xcheck:jni',
        '-cp', str(dex), 'org.archtv.aospprobe.PublicResourcesProbe', *extra]
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env,
                          cwd=out, start_new_session=True) as process:
        try: stdout, stderr = process.communicate(timeout=30)
        except BaseException:
            try: os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError: pass
            process.communicate()
            raise
    (out/(label+'.stdout')).write_bytes(stdout)
    (out/(label+'.stderr')).write_bytes(stderr)
    results[label] = {'pass': process.returncode == 0 and stdout.strip() == marker,
                      'exit_code': process.returncode, 'command': command}
results['host_properties'] = host_properties
results['source_count'] = len(proof['original_sources_sha256'])
results['prebuilt_bindings'] = proof['prebuilt_bindings']
results['scope'] = 'Original public Resources constructor/getIdentifier/getString with internal host AssetManager setup. No full system-resource initialization or broad API/Activity/View compatibility claim.'
results['sha256'] = {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
                    for path in (dex, args.linux_library, args.resources_library, apk)}
(out/'result.json').write_text(json.dumps(results, indent=2)+'\n')
print(out/'result.json')
if not all(results[name]['pass'] for name in ('reference', 'public-resources')): raise SystemExit(1)
