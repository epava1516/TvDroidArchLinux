#!/usr/bin/env python3
"""Check host ART semantics and expose the missing Android API boundary."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time

parser = argparse.ArgumentParser()
parser.add_argument('--runtime', type=Path, required=True)
parser.add_argument('--dex', type=Path, required=True)
parser.add_argument('--apk', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
runtime, dex, apk, out = [path.resolve() for path in
                          (args.runtime, args.dex, args.apk, args.output)]
out.mkdir(parents=True, exist_ok=False)
data = out/'runtime-data'
data.mkdir(mode=0o700)
environment = {key: value for key, value in os.environ.items()
               if not key.startswith('ANDROID_') and key not in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'CLASSPATH')}
environment['ANDROID_DATA'] = str(data)
environment['ANDROID_LOG_TAGS'] = '*:w'
main = 'org.archtv.runtimeprobe.RuntimeProbe'
base = [str(runtime/'bin/art'), '--64', '--no-compile', '--', '-Xint']
results = {}
for name, suffix in [('semantics', ['-cp', str(dex), main]),
                     ('apk-class-load', ['-verbose:class', '-cp', str(dex)+':'+str(apk), main, 'org.archtv.probe.MainActivity'])]:
    command = base+suffix
    started = time.monotonic()
    result = subprocess.run(command, env=environment, cwd=out, capture_output=True, timeout=90)
    (out/(name+'.stdout')).write_bytes(result.stdout)
    (out/(name+'.stderr')).write_bytes(result.stderr)
    results[name] = {'command': command, 'exit_code': result.returncode,
                     'elapsed_seconds': time.monotonic()-started}
results['engine_semantics_pass'] = (results['semantics']['exit_code'] == 0
    and b'DEX_SEMANTICS_OK total=9' in (out/'semantics.stdout').read_bytes())
results['apk_api_boundary_observed'] = (results['apk-class-load']['exit_code'] != 0
    and b'android/app/Activity' in (out/'apk-class-load.stderr').read_bytes())
results['apk_functional_pass'] = False
results['sha256'] = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in (dex, apk)}
results['scope'] = 'ART host engine probe and expected missing Android superclass. No Activity lifecycle, UI, persistence, isolation or stable APK compatibility proved.'
(out/'result.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps({key: results[key] for key in
                  ('engine_semantics_pass', 'apk_api_boundary_observed', 'apk_functional_pass')}))
if not results['engine_semantics_pass'] or not results['apk_api_boundary_observed']:
    raise SystemExit(1)
