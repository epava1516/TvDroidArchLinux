#!/usr/bin/env python3
"""Relink the original complete vendor libcutils with the explicit memfd backport.

Retains the recorded vendor compiler flags, objects and LLNDK link boundary.
Static exports and linking do not establish runtime or security compatibility.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

repo = Path(__file__).resolve().parents[2]
out = (repo / sys.argv[1]).resolve()
out.mkdir()
records = repo / 'reports/android16-vendor-libutils'
meta_path = repo / 'runtime/aosp/android16-qpr2/patches/libcutils-memfd-original-label.json'
meta = json.loads(meta_path.read_text())
patch = meta_path.with_suffix('.patch')
compile_row = next(r for r in json.loads((records / 'dependencies-compile.json').read_text())['results']
                   if r['source'].endswith('/ashmem-dev.cpp'))
link_row = next(r for r in json.loads((records / 'link.json').read_text())['results'] if r['module'] == 'libcutils')
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
record = {'scope': __doc__, 'inputs': {}, 'commands': [], 'terminal': False}

def run(argv, **kwargs):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=180, **kwargs)
    record['commands'].append({'argv': argv, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    (out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
    if result.returncode:
        raise SystemExit(result.stderr or result.stdout)
    return result.stdout

source = Path(compile_row['source'])
assert sha(source) == meta['source_sha256'] == compile_row['source_sha256']
assert sha(patch) == meta['patch_sha256']
shutil.copytree(source.parent, out / 'libcutils')
for item in (out / 'libcutils').rglob('*'):
    if item.is_file():
        record['inputs'][str(item)] = sha(item)
run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch)], cwd=out)
adapted = out / 'libcutils/ashmem-dev.cpp'
assert sha(adapted) == meta['adapted_sha256']
record['inputs'][str(adapted)] = sha(adapted)
argv = compile_row['argv'].copy()
assert '-D__ANDROID_VNDK__' in argv and '-D__ANDROID_VENDOR__' in argv
for option, value in [('-c', adapted), ('-o', out / 'ashmem-dev.o'), ('-MF', out / 'ashmem-dev.d')]:
    argv[argv.index(option) + 1] = str(value)
for item in [source, patch, meta_path, records / 'dependencies-compile.json', records / 'link.json']:
    record['inputs'][str(item)] = sha(item)
run(argv)
argv = link_row['argv'].copy()
assert argv.count(compile_row['object']) == 1
for item in argv:
    if Path(item).is_file():
        record['inputs'][item] = sha(item)
argv[argv.index(compile_row['object'])] = str(out / 'ashmem-dev.o')
original = Path(argv[argv.index('-o') + 1])
target = out / 'libcutils.so'
argv[argv.index('-o') + 1] = str(target)
run(argv)

def exports(binary):
    result = set()
    for line in run(['readelf', '--dyn-syms', '--wide', str(binary)]).splitlines():
        fields = line.split()
        if len(fields) >= 8 and fields[4] in ('GLOBAL', 'WEAK') and fields[6] != 'UND':
            result.add(tuple(fields[3:6]) + (fields[7],))
    return result

old, new = exports(original), exports(target)
record['export_comparison'] = {'missing': sorted(old-new), 'added': sorted(new-old),
                               'original_count': len(old), 'candidate_count': len(new),
                               'limitation': 'Symbol identity/binding/type/visibility only, not full ABI or runtime proof'}
assert not old-new, record['export_comparison']
record.update(terminal=True, library=str(target), sha256=sha(target), original_change=meta)
(out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'library': str(target), 'sha256': sha(target), 'exports': record['export_comparison']}))
