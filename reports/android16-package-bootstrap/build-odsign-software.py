#!/usr/bin/env python3
"""Build whole pinned odsign with an explicit SOFTWARE profile, no runtime acceptance."""
from pathlib import Path
import argparse, hashlib, json, re, shutil, subprocess, tarfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', type=Path)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[2]
out = (repo / args.output).resolve()
assert out.is_relative_to(repo / 'dist/aosp16')
out.mkdir()
cache = Path('/home/tv/.cache/archtv/aosp16-qpr2')
study = cache / 'audio-original-study-1'
inputs = cache / 'native-build-inputs'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
record = {'scope': 'Whole original odsign source build, explicit SOFTWARE profile; no signing, ART load, MAC or APK acceptance',
          'commands': [], 'sources': [], 'provenance': {}}
def save():
    (out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
def run(argv):
    argv = list(map(str, argv))
    result = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    record['commands'].append({'argv': argv, 'exit': result.returncode,
                               'stdout': result.stdout, 'stderr': result.stderr})
    if result.returncode:
        record['status'] = 'failed'
    save()
    print(Path(argv[0]).name, result.returncode, result.stderr[:1400], flush=True)
    result.check_returncode()
for name in ['original-odsign', 'original-odrefresh', 'original-fsverity-utils', 'original-art-atoms', 'original-logwrapper']:
    acquisition = study / (name + '.acquisition.json')
    item = json.loads(acquisition.read_text())
    assert sha(study / (name + '.tar.gz')) == item['sha256']
    # Bind extracted sources to the actual pinned archive, not only a cache marker.
    with tarfile.open(study / (name + '.tar.gz')) as archive:
        for member in archive.getmembers():
            if member.isfile():
                assert (study / name / member.name).read_bytes() == archive.extractfile(member).read(), member.name
    record['provenance'][name] = item
source = out / 'source'
shutil.copytree(study / 'original-odsign', source)
patch = repo / 'runtime/aosp/android16-qpr2/patches/odsign-explicit-software.patch'
meta = json.loads(patch.with_suffix('.json').read_text())
assert sha(patch) == meta['patch_sha256']
for item in meta['files']:
    assert sha(source / item['path']) == item['original_sha256']
run(['patch', '--batch', '--fuzz=0', '-p1', '-d', source, '-i', patch])
for item in meta['files']:
    assert sha(source / item['path']) == item['adapted_sha256']
record['patch'] = meta
correction = repo / 'runtime/aosp/android16-qpr2/patches/odsign-x509-initialization.patch'
correction_meta = json.loads(correction.with_suffix('.json').read_text())
assert sha(correction) == correction_meta['patch_sha256']
for item in correction_meta['files']:
    assert sha(source / item['path']) == item['original_sha256']
run(['patch', '--batch', '--fuzz=0', '-p1', '-d', source, '-i', correction])
for item in correction_meta['files']:
    assert sha(source / item['path']) == item['adapted_sha256']
record['source_corrections'] = [correction_meta]
apis = [inputs / 'keystore2-aidl-original/source/system/hardware/interfaces/keystore2/aidl/aidl_api/android.system.keystore2/1',
        inputs / 'security-hal-original/source/hardware/interfaces/security/keymint/aidl/aidl_api/android.hardware.security.keymint/1',
        inputs / 'security-hal-original/source/hardware/interfaces/security/secureclock/aidl/aidl_api/android.hardware.security.secureclock/1']
for api in apis:
    run([repo / 'dist/aosp16/aidl-host-build-4/aidl', '--lang=cpp', '--structured',
         '--stability=vintf', '--version=1', '--hash=' + (api / '.hash').read_text().splitlines()[-1],
         '--omit_invocation', '--out=' + str(out / 'aidl/src'), '--header_out=' + str(out / 'aidl/include')]
        + ['-I' + str(p) for p in apis] + sorted(api.rglob('*.aidl')))
# Only enum constants used by original StatsReporter: generated from the complete
# pinned Status enum, with no replacement metrics functions or invented results.
atoms = study / 'original-art-atoms/odrefresh_extension_atoms.proto'
text = re.sub(r'//[^\n]*', '', atoms.read_text())
body = re.search(r'message\s+OdsignReported\s*\{\s*enum\s+Status\s*\{([^}]+)\}', text).group(1)
values = re.findall(r'\b(STATUS_[A-Z_]+)\s*=\s*(\d+)\s*;', body)
assert len(values) == 8 and len(set(n for n, _ in values)) == 8
headers = out / 'generated'
headers.mkdir()
(headers / 'statslog_odsign.h').write_text('#pragma once\nnamespace art::metrics::statsd {\n' + ''.join(
    'inline constexpr int ODSIGN_REPORTED__STATUS__' + n + ' = ' + value + ';\n' for n, value in values) + '}\n')
record['metrics_constants'] = {'source': str(atoms), 'sha256': sha(atoms), 'values': values,
                              'scope': 'Enum-only generation for original file-based StatsReporter; not a replacement stats service'}
proto = source / 'proto/odsign_info.proto'
run([repo / 'dist/aosp16/protoc-host-2/protoc', '-I' + str(proto.parent),
     '--cpp_out=lite:' + str(headers), proto])
flags = json.loads((repo / 'reports/android16-hwc3-frontend/build.json').read_text())['results'][0]['argv']
flags = flags[:flags.index('-MMD')]
flags += ['-DARCHTV_ODSIGN_SOFTWARE_PROFILE=1'] + ['-I' + str(p) for p in [
    source, source / 'include', headers, out / 'aidl/include',
    study / 'original-logwrapper/include',
    study / 'original-odrefresh/include', study / 'original-fsverity-utils/include',
    inputs / 'keymint-boringssl-headers/source/external/boringssl/src/include',
    inputs / 'protobuf/source/external/protobuf/src', inputs / 'abseil/source/external/abseil-cpp']]
units = [source / n for n in ['KeystoreKey.cpp', 'KeystoreHmacKey.cpp', 'odsign_main.cpp',
                             'StatsReporter.cpp', 'CertUtils.cpp', 'VerityUtils.cpp']]
units += [headers / 'odsign_info.pb.cc']
objects = []
for number, path in enumerate(units):
    obj = out / (str(number) + '.o')
    run(flags + ['-c', path, '-o', obj])
    objects.append(obj)
    record['sources'].append({'path': str(path), 'sha256': sha(path), 'object': str(obj), 'object_sha256': sha(obj)})
    save()
record.update(status='compiled_not_linked_or_executed',
              generated_header_sha256={str(p.relative_to(out)): sha(p)
                  for directory in [out / 'aidl/include', headers]
                  for p in directory.rglob('*.h')},
              builder_sha256=sha(Path(__file__)))
save()
