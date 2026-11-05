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
synchronous_pcm = '--synchronous-pcm' in sys.argv[3:]
pcm_observation = '--pcm-observation' in sys.argv[3:]
assert not pcm_observation or synchronous_pcm
assert not (write_diagnostic and synchronous_pcm), 'Choose one StreamAlsa candidate'
if synchronous_pcm:
    patches.append(repo / 'runtime/aosp/android16-qpr2/patches/audio-alsa-synchronous-pcm.patch')
if write_diagnostic:
    patches.append(repo / 'runtime/aosp/android16-qpr2/patches/audio-alsa-write-observation.patch')
if pcm_observation:
    patches.append(repo / 'runtime/aosp/android16-qpr2/patches/audio-alsa-pcm-observation.patch')
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
study = Path('/home/tv/.cache/archtv/aosp16-qpr2/audio-original-study-1/hardware-audio')
record = {'scope': 'Compilation only; no link, service or output acceptance',
          'write_diagnostic': write_diagnostic, 'synchronous_pcm': synchronous_pcm,
          'pcm_observation': pcm_observation, 'patches': {}, 'commands': [], 'objects': []}
if pcm_observation:
    header = repo / 'runtime/aosp/native/linux-pcm-observation.h'
    record['observation_header'] = {'path': str(header), 'sha256': sha(header)}
files = []
for patch in patches:
    meta = json.loads(patch.with_suffix('.json').read_text())
    assert sha(patch) == meta['patch_sha256']
    record['patches'][str(patch)] = sha(patch)
    record['patches'][str(patch.with_suffix('.json'))] = sha(patch.with_suffix('.json'))
    for f in meta['files']:
        previous = next((v for v in files if v['path'] == f['path']), None)
        if previous is not None:
            dest = out / 'source' / f['path']
            assert sha(dest) == f['original_sha256'] == previous['adapted_sha256']
            previous['adapted_sha256'] = f['adapted_sha256']
            continue
        src = study / f['path']
        assert sha(src) == f['original_sha256']
        dest = out / 'source' / f['path']
        dest.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dest)
        files.append(f)
    subprocess.run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch)],
                   cwd=out / 'source', check=True, capture_output=True)
base = json.loads((core / 'build.json').read_text())
reuse_dir = repo / 'dist/aosp16/audio-linux-primary-build-1' if '--reuse-primary' in sys.argv[3:] else None
assert not reuse_dir or write_diagnostic or synchronous_pcm
reuse = json.loads((reuse_dir / 'build.json').read_text()) if reuse_dir else None
for f in files:
    src = out / 'source' / f['path']
    assert sha(src) == f['adapted_sha256']
    original = str(study / f['path'])
    command = next(c['argv'] for c in base['commands'] if original in c['argv'])
    reusable = next((u for u in reuse['objects'] if u['original'] == original), None) if reuse else None
    if reusable and f['path'] != 'aidl/default/alsa/StreamAlsa.cpp':
        unit = reusable
        prior_source = reuse_dir / 'source' / f['path']
        assert sha(prior_source) == unit['source_sha256'] == sha(src)
        assert sha(Path(unit['object'])) == unit['sha256']
        old_command = next(c for c in reuse['commands'] if str(prior_source) in c['argv'])
        assert old_command['exit'] == 0
        assert old_command['argv'][:old_command['argv'].index('-MMD')] == command[:command.index('-MMD')]
        record['commands'].append({**old_command, 'reused_verified_object': True,
                                   'source_record': str(reuse_dir / 'build.json'),
                                   'source_record_sha256': sha(reuse_dir / 'build.json')})
        record['objects'].append({**unit, 'reused_verified_object': True})
        (out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
        print(src.name, 'reused_verified_object', flush=True)
        continue
    obj = out / (src.stem + '.o')
    argv = command[:command.index('-MMD')] + ([
        '-I' + str(repo / 'runtime/aosp/native')] if pcm_observation else []) + ['-MMD', '-MF', str(obj.with_suffix('.d')),
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
