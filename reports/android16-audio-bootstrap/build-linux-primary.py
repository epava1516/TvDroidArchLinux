#!/usr/bin/env python3
"""Compile the reviewed Linux ALSA adaptation against original core contracts.

Preserves pristine cached AOSP sources and all unchanged factory/module units.
This does not link, execute or establish audio output availability.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

repo = Path(__file__).resolve().parents[2]
core = (repo / sys.argv[1]).resolve()
out = (repo / sys.argv[2]).resolve()
out.mkdir()
patches = [repo / 'runtime/aosp/android16-qpr2/patches/audio-primary-linux-alsa.patch']
write_diagnostic = '--write-diagnostic' in sys.argv[3:]
if write_diagnostic:
    patches.append(repo / 'runtime/aosp/android16-qpr2/patches/audio-alsa-write-observation.patch')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
study = Path('/home/tv/.cache/archtv/aosp16-qpr2/audio-original-study-1/hardware-audio')
record = {'scope': 'Compilation only; no link, service or output acceptance',
          'write_diagnostic': write_diagnostic, 'patches': {}, 'commands': [], 'objects': []}
files = []
for patch in patches:
    meta = json.loads(patch.with_suffix('.json').read_text())
    assert sha(patch) == meta['patch_sha256']
    record['patches'][str(patch)] = sha(patch)
    record['patches'][str(patch.with_suffix('.json'))] = sha(patch.with_suffix('.json'))
    for f in meta['files']:
        assert all(f['path'] != previous['path'] for previous in files)
        src = study / f['path']
        assert sha(src) == f['original_sha256']
        dest = out / 'source' / f['path']
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        files.append(f)
    subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch)],
                   cwd=out / 'source', check=True, capture_output=True)
base = json.loads((core / 'build.json').read_text())
for f in files:
    src = out / 'source' / f['path']
    assert sha(src) == f['adapted_sha256']
    original = str(study / f['path'])
    command = next(c['argv'] for c in base['commands'] if original in c['argv'])
    obj = out / (src.stem + '.o')
    argv = command[:command.index('-MMD')] + ['-MMD', '-MF', str(obj.with_suffix('.d')),
                                            '-c', str(src), '-o', str(obj)]
    result = subprocess.run(argv, capture_output=True, timeout=120)
    log = out / (src.stem + '.log')
    log.write_bytes(result.stdout + result.stderr)
    record['commands'].append({'argv': argv, 'exit': result.returncode, 'log': str(log)})
    if not result.returncode:
        record['objects'].append({'original': original, 'source_sha256': sha(src),
                                  'object': str(obj), 'sha256': sha(obj)})
    (out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
    print(src.name, result.returncode, flush=True)
    if result.returncode:
        print(result.stderr.decode(errors='replace')[-2000:])
        raise SystemExit(result.returncode)
