#!/usr/bin/env python3
"""Link all seven verified original odsign units; not service or cache acceptance."""
from pathlib import Path
import argparse, hashlib, json, subprocess
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('source_build', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[2]
source = (repo / args.source_build).resolve()
out = (repo / args.output).resolve()
assert source.is_relative_to(repo / 'dist/aosp16') and out.is_relative_to(repo / 'dist/aosp16')
out.mkdir()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
build = json.loads((source / 'build.json').read_text())
assert len(build['sources']) == 7 and all(c['exit'] == 0 for c in build['commands'])
for name, expected in build.get('generated_header_sha256', {}).items():
    assert sha(source / name) == expected, name
objects = []
for item in build['sources']:
    assert sha(item['path']) == item['sha256']
    assert sha(item['object']) == item['object_sha256']
    objects.append(Path(item['object']))
record = {'scope': 'Whole source-linked original odsign with explicit SOFTWARE selection; no execution, signing, image loading or APK acceptance',
          'source_build': str(source / 'build.json'), 'source_build_sha256': sha(source / 'build.json'),
          'all_seven_source_objects_verified': True, 'commands': [], 'source_profile': build['patch'],
          'source_corrections': build.get('source_corrections', []),
          'source_build_state': build.get('status', 'legacy_missing_prelink_status'),
          'note': 'Reusing only all7 hash-recorded completed compilation artifacts, no failed compiler output. Linking and execution are separate.'}
libs = repo / 'dist/aosp16/factory-inputs-3/root/system/lib64'
support = repo / 'dist/aosp16/hwc3-frontend-2/link-libs'
stats_root = repo / 'dist/aosp16/statsd-inputs-1'
stats = stats_root / 'com.android.os.statsd/lib64'
provenance = json.loads((stats_root / 'provenance.json').read_text())
module = next(m for m in json.loads((repo / 'reports/android16-apex-bootstrap/complete-inputs.json').read_text())['modules'] if m['name'] == 'com.android.os.statsd')
assert sha(stats_root / 'com.android.os.statsd.apex') == module['archive_sha256']
record['stats_apex'] = {'original_module': module, 'extraction_provenance_sha256': sha(stats_root / 'provenance.json')}
for name in ['libstatspull.so', 'libstatssocket.so']:
    path = stats / name
    assert sha(path) == provenance['files'][str(path.relative_to(stats_root))]['sha256']
needed = ['android.system.keystore2-V1-cpp.so', 'android.hardware.security.keymint-V1-cpp.so',
          'libbase.so', 'libbinder.so', 'libcrypto.so', 'libcrypto_utils.so', 'libfsverity.so',
          'liblogwrap.so', 'libprotobuf-cpp-lite.so', 'libstatspull.so', 'libstatssocket.so',
          'libutils.so', 'liblog.so', 'libc++.so', 'libc.so', 'libm.so', 'libdl.so']
paths = []
for name in needed:
    path = stats / name if name in ['libstatspull.so', 'libstatssocket.so'] else libs / name
    if not path.is_file():
        path = support / name
    assert path.is_file(), name
    paths.append(path)
crt = repo / 'dist/aosp16/crt-native-1'
start, end = crt / 'crtbegin_dynamic.o', crt / 'crtend_android.o'
builtins = Path('/home/tv/.cache/archtv/graphics-candidates-1/compiler-builtins/libclang_rt.builtins-x86_64-android.a')
record['inputs'] = {str(p): sha(p) for p in [*paths, start, end, builtins]}
record['link_script_sha256'] = sha(Path(__file__))
record['linker_sha256'] = sha(Path('/home/tv/.cache/archtv/aosp16-qpr2/native-toolchain-1/bin/ld.lld'))
binary = out / 'archtv-odsign-software'
argv = list(map(str, [Path('/home/tv/.cache/archtv/aosp16-qpr2/native-toolchain-1/bin/ld.lld'),
    '--no-undefined', '--no-allow-shlib-undefined', '-pie', '--dynamic-linker=/system/bin/linker64',
    '-z', 'relro', '-z', 'now', '--rpath-link=' + str(libs), '--rpath-link=' + str(support),
    '--rpath-link=' + str(stats), start, *objects, *paths, builtins, end, '-o', binary]))
result = subprocess.run(argv, capture_output=True, text=True, timeout=120)
record['commands'].append({'argv': argv, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
record['status'] = 'linked_not_executed' if result.returncode == 0 else 'failed'
if result.returncode == 0:
    record.update(binary=str(binary), binary_sha256=sha(binary))
(out / 'link.json').write_text(json.dumps(record, indent=2) + '\n')
print('original odsign whole-source link', result.returncode, result.stderr[:2000], flush=True)
result.check_returncode()
