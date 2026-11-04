#!/usr/bin/env python3
"""Build complete original LC3/experimental Opus dependencies for the audio HAL.

Original generic x86_64 Android.bp source lists and feature defines. No codec,
Bluetooth, service or hardware functionality is accepted by compilation.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

repo = Path(__file__).resolve().parents[2]
core = repo / sys.argv[1]
out = repo / sys.argv[2]
out.mkdir()
study = Path('/home/tv/.cache/archtv/aosp16-qpr2/audio-original-study-1')
base = json.loads((core / 'build.json').read_text())
first = next(c['argv'] for c in base['commands'] if Path(c['log']).name.startswith('compile-'))
flags = first[:first.index('-MMD')]
flags = [f for f in flags if not f.startswith('-std=') and f not in
         ['-fno-rtti', '-frtti', '-fvisibility-inlines-hidden', '-nostdinc++']]
flags += ['-x', 'c', '-std=gnu11']
ar = 'ar'  # Standard archive container only; does not link Linux libraries.
record = {'scope': 'Complete original codec source build only; no execution acceptance',
          'commands': [], 'sources': [], 'archives': {},
          'diagnostic_adaptation': 'Retain original Opus unused-but-set-variable diagnostic as warning; no source/runtime change. Exact Soong sanitizer/CFI equivalence not established.'}

def run(args, name):
    args = list(map(str, args))
    x = subprocess.run(args, capture_output=True, timeout=120)
    log = out / (name + '.log')
    log.write_bytes(x.stdout + x.stderr)
    record['commands'].append({'argv': args, 'exit': x.returncode, 'log': str(log)})
    (out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
    print(name, x.returncode, flush=True)
    if x.returncode:
        print(x.stderr.decode(errors='replace')[-1600:])
        raise SystemExit(x.returncode)

for group in ['liblc3', 'opus-experimental']:
    root = study / group
    bp = root / 'Android.bp'
    text = bp.read_text()
    record.setdefault('android_bp_sha256', {})[str(bp)] = hashlib.sha256(bp.read_bytes()).hexdigest()
    if group == 'liblc3':
        units = sorted((root / 'src').glob('*.c'))
        extra = ['-O3', '-Wmissing-braces', '-Wno-#warnings', '-Wno-implicit-fallthrough',
                 '-Wno-self-assign', '-Wuninitialized', '-ffast-math']
        includes = ['include']
    else:
        section = text[text.index('name: "libopus-experimental"'):]
        srcs = re.search(r'srcs:\s*\[(.*?)\]', section, re.S).group(1)
        units = [root / name for name in re.findall(r'"([^"]+\.c)"', srcs)]
        extra = ['-O2', '-DDISABLE_DEBUG_FLOAT=1', '-DFLOAT_APPROX=1', '-DHAVE_LRINT',
                 '-DHAVE_LRINTF', '-DENABLE_HARDENING', '-DENABLE_RES24', '-DENABLE_QEXT',
                 '-DVAR_ARRAYS', '-DOPUS_BUILD', '-fno-math-errno', '-Wall', '-Werror',
                 '-Wno-error=unused-but-set-variable']
        includes = ['include', 'src', 'silk', 'celt', 'silk/float', 'silk/fixed']
    objects = []
    for i, src in enumerate(units):
        obj = out / (group + '-' + str(i) + '.o')
        run(flags + extra + ['-I' + str(root / p) for p in includes] +
            ['-MMD', '-MF', obj.with_suffix('.d'), '-c', src, '-o', obj], group + '-' + str(i))
        record['sources'].append({'path': str(src), 'sha256': hashlib.sha256(src.read_bytes()).hexdigest(),
                                  'object': str(obj), 'object_sha256': hashlib.sha256(obj.read_bytes()).hexdigest()})
        objects.append(obj)
    archive = out / (group + '.a')
    run([ar, 'rcs', archive, *objects], group + '-archive')
    record['archives'][group] = {'path': str(archive), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest()}
    (out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
