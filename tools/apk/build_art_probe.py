#!/usr/bin/env python3
"""Build a DEX semantic probe; does not execute APKs or implement Android APIs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--tools', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--jdk', type=Path, default=Path('/usr/lib/jvm/java-17-openjdk'))
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
tools = args.tools.resolve()
manifest = json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())
for item in manifest['artifacts']:
    if item['file'] not in ('r8.jar', 'android.jar'):
        continue
    with (tools/item['file']).open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != item['sha256']:
            raise SystemExit('Tool checksum mismatch: '+item['file'])
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
(out/'classes').mkdir()
(out/'dex').mkdir()
source = root/'fixtures/art-host/RuntimeProbe.java'
commands = [
    [args.jdk/'bin/javac', '--release', '8', '-d', out/'classes', source],
    [args.jdk/'bin/jar', 'cf', out/'probe.jar', '-C', out/'classes', '.'],
    [args.jdk/'bin/java', '-cp', tools/'r8.jar', 'com.android.tools.r8.D8', '--release',
     '--min-api', '21', '--lib', tools/'android.jar', '--output', out/'dex', out/'probe.jar'],
]
for command in commands:
    subprocess.run([str(part) for part in command], check=True, timeout=120)
(out/'provenance.json').write_text(json.dumps({
    'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
    'dex_sha256': hashlib.sha256((out/'dex/classes.dex').read_bytes()).hexdigest(),
    'toolchain': manifest,
    'scope': 'DEX semantic and class resolution probe only; no Android API implementation.',
}, indent=2)+'\n')
print(out/'dex/classes.dex')
