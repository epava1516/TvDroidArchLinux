#!/usr/bin/env python3
"""Link and exercise original Skia raster drawing; no ART or Wayland claim."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--skia-build', type=Path, required=True)
parser.add_argument('--sources', type=Path, required=True)
parser.add_argument('--androidfw-build', type=Path, required=True)
parser.add_argument('--androidfw-sources', type=Path, required=True)
parser.add_argument('--art', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
build, sources = args.skia_build.resolve(), args.sources.resolve()
native, cache = args.androidfw_build.resolve(), args.androidfw_sources.resolve()
proof = json.loads((build/'result.json').read_text())
if not proof['build_pass']:
    raise SystemExit('Skia build did not pass')
archives = []
for name, expected in proof['archives'].items():
    path = build/name
    if sha(path) != expected:
        raise SystemExit('Skia archive modified: '+name)
    archives.append(path)
original_native = json.loads((native/'provenance.json').read_text())
for name, expected in original_native['archives'].items():
    path = native/name
    if sha(path) != expected:
        raise SystemExit('Native resource archive modified: '+name)
    archives.append(path)
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
source = root/'runtime/aosp/native/skia-raster-probe.cpp'
libcxx = args.art.resolve()/'lib64/libc++.so'
if sha(libcxx) != original_native['libcxx_runtime_sha256']:
    raise SystemExit('ART libc++ differs from native archive build')
command = ['clang++', '-std=c++17', '-nostdinc++', '-isystem', str(cache/'libcxx'),
           '-I'+str(sources/'skia'), '-I'+str(sources/'skia/linux'),
           '-I'+str(sources/'skia/include/config'), '-I'+str(cache/'log/include'),
           '-nostdlib++', '-L'+str(libcxx.parent), '-Wl,-rpath,'+str(libcxx.parent),
           str(source), '-o', str(out/'skia-raster-probe'), '-Wl,--start-group',
           *map(str, archives), '-Wl,--end-group', '-lc++', '-lz', '-ldl', '-lpthread',
           '-lpng', '-ljpeg', '-lwebp', '-lwebpmux', '-lwebpdemux', '-lexpat',
           '-lfreetype', '-lharfbuzz', '-lharfbuzz-subset', '-licuuc', '-licui18n', '-licudata']
(out/'link-command.json').write_text(json.dumps(command, indent=2)+'\n')
with (out/'link.log').open('w') as stream:
    subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, check=True, timeout=120)
run = subprocess.run([str(out/'skia-raster-probe'), str(out/'raster.ppm')],
                     capture_output=True, text=True, timeout=30)
(out/'raster.stdout').write_text(run.stdout)
(out/'raster.stderr').write_text(run.stderr)
expected = 'ORIGINAL_SKIA_RASTER_OK pixels=3072 clip=1 translate=1 rgba_readback=1'
if run.returncode != 0 or expected not in run.stdout:
    raise SystemExit('Original Skia raster probe failed')
(out/'result.json').write_text(json.dumps({
    'original_skia_raster_pass': True, 'art_pass': False, 'wayland_pass': False,
    'scope': 'CPU raster clear/rect/clip/translate and exact 3072-pixel RGBA readback',
    'source_sha256': sha(source), 'verifier_sha256': sha(Path(__file__)),
    'build_provenance_sha256': sha(build/'result.json'),
    'native_provenance_sha256': sha(native/'provenance.json'),
    'libcxx_sha256': sha(libcxx), 'executable_sha256': sha(out/'skia-raster-probe'),
    'raster_sha256': sha(out/'raster.ppm'),
}, indent=2)+'\n')
print(expected)
