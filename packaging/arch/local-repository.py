#!/usr/bin/env python3
"""Create a fresh local pacman repository containing only the three TV packages."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('packages', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
source = args.packages.resolve()
output = args.output.resolve()
expected = {'archtv-compositor', 'archtv-shell', 'archtv-session'}
selected = {}
for path in sorted(source.glob('*.pkg.tar.zst')):
    name, version = subprocess.check_output(['pacman', '-Qp', str(path)], text=True).split()
    if name in expected:
        if name in selected:
            raise SystemExit(f'Multiple versions of {name}; use a single build directory.')
        selected[name] = (path, version)
if set(selected) != expected:
    raise SystemExit('Expected compositor, shell and session packages.')
if len({version for _, version in selected.values()}) != 1:
    raise SystemExit('Package versions must agree.')
commit = (source / 'source-commit.txt').read_text().strip()
if not re.fullmatch(r'[0-9a-f]{40}', commit):
    raise SystemExit('Missing valid source commit.')
output.mkdir(parents=True, exist_ok=False)
records = []
for name, (path, version) in sorted(selected.items()):
    destination = output / path.name
    shutil.copyfile(path, destination)
    records.append({'name': name, 'version': version, 'file': path.name,
                    'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()})
subprocess.run(['repo-add', '--nocolor', 'archtv.db.tar.gz',
                *(record['file'] for record in records)], cwd=output, check=True)
manifest = {'source_commit': commit, 'scope': 'Unsigned local laboratory repository; not a public release.',
            'packages': records}
(output / 'manifest.json').write_text(json.dumps(manifest, indent=2) + '\n')
files = sorted(path for path in output.iterdir() if path.is_file() and not path.is_symlink())
(output / 'SHA256SUMS').write_text(''.join(
    f'{hashlib.sha256(path.read_bytes()).hexdigest()}  {path.name}\n' for path in files))
subprocess.run(['sha256sum', '--check', 'SHA256SUMS'], cwd=output, check=True)
print(output)
