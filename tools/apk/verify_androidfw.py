#!/usr/bin/env python3
"""Exercise original AOSP resource lookup against owned APKs, including failures."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--build', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
build = args.build.resolve()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
probe = build/'archtv-resource-probe'
provenance = json.loads((build/'provenance.json').read_text())
assert hashlib.sha256(probe.read_bytes()).hexdigest() == provenance['probe_sha256']
apk = root/'fixtures/apk/counter/golden/counter.apk'
assert hashlib.sha256(apk.read_bytes()).hexdigest() == 'f07c9b92ab3353237276081c22e11ce06168b8c9f71a99ea32968b2ce0f00e28'
results = []

def run(label, path, names, expected=None):
    command = [str(probe), str(path), *['org.archtv.probe:string/'+name for name in names]]
    result = subprocess.run(command, capture_output=True, timeout=15)
    (out/(label+'.stdout')).write_bytes(result.stdout)
    (out/(label+'.stderr')).write_bytes(result.stderr)
    if expected is None:
        assert result.returncode > 0, (label, result.returncode)
    else:
        assert result.returncode == 0, (label, result.stderr)
        lines = result.stdout.decode('ascii').splitlines()
        values = [bytes.fromhex(line.split('\t')[1]).decode('utf-8') for line in lines]
        assert values == expected, (label, values)
        assert all(int(line.split('\t')[0], 16) >> 24 == 0x7f for line in lines)
    results.append({'case': label, 'returncode': result.returncode, 'pass': True})

run('original', apk, ['app_name', 'counter', 'increment'], ['Arch TV · APK probe', 'Contador:', 'Incrementar'])
with zipfile.ZipFile(apk) as archive:
    content = {name: archive.read(name) for name in archive.namelist()}
assert content['resources.arsc'].count(b'Contador:') == 1
for label, table in [('variant', content['resources.arsc'].replace(b'Contador:', b'Registro:')),
                     ('truncated', content['resources.arsc'][:20])]:
    path = out/(label+'-unsigned.apk')
    with zipfile.ZipFile(path, 'w') as archive:
        for name, data in content.items():
            archive.writestr(name, table if name == 'resources.arsc' else data)
    with zipfile.ZipFile(path) as archive:
        assert archive.read('classes.dex') == content['classes.dex']
    run(label, path, ['counter'], ['Registro:'] if label == 'variant' else None)
run('missing-name', apk, ['nonexistent'])
run('missing-apk', out/'absent.apk', ['counter'])
(out/'result.json').write_text(json.dumps({'pass': True, 'cases': results,
    'apk_sha256': hashlib.sha256(apk.read_bytes()).hexdigest(),
    'probe_sha256': provenance['probe_sha256'],
    'scope': 'Original AOSP native AssetManager/ResTable string lookup. No Java Resources/JNI integration or general APK compatibility claim.'}, indent=2)+'\n')
print(out/'result.json')
