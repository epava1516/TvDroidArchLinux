#!/usr/bin/env python3
"""Link the original effect provider against actual GSI/Bionic libraries."""
from pathlib import Path
import hashlib
import json
import os
import subprocess
import sys

repo = Path(__file__).resolve().parents[2]
out = (repo / sys.argv[1]).resolve()
out.mkdir()
root = repo / 'dist/aosp16/factory-inputs-3/root'
libs = root / 'system/lib64'
production_dynamics = '--production-dynamics' in sys.argv[2:]
archives = [repo / 'dist/aosp16/audio-support-build-4/audio_effect_service.a',
            repo / 'dist/aosp16/audio-support-build-2/libeffectconfig.a']
production_inputs = {}
if production_dynamics:
    build_path = repo / 'dist/aosp16/audio-production-dynamics-build-1/build.json'
    build = json.loads(build_path.read_text())
    assert build['terminal'] and all(c['exit'] == 0 for c in build['commands'])
    archive = build['archives']['libdynamicsprocessingaidl']
    archives = [Path(archive['path'])]
    assert hashlib.file_digest(archives[0].open('rb'), 'sha256').hexdigest() == archive['sha256']
    production_inputs = {str(build_path): hashlib.file_digest(build_path.open('rb'), 'sha256').hexdigest(),
                         **build['production_effect_inputs']}
    for unit in build['sources']:
        production_inputs[unit['path']] = unit['sha256']
        production_inputs[unit['object']] = unit['object_sha256']
    for path, digest in production_inputs.items():
        assert hashlib.file_digest(Path(path).open('rb'), 'sha256').hexdigest() == digest, path
names = ['android.media.audio.common.types-V4-ndk.so',
         'android.media.audio.eraser.types-V1-ndk.so',
         'android.hardware.audio.common-V4-ndk.so',
         'android.hardware.audio.effect-V3-ndk.so',
         'android.hardware.common-V2-ndk.so', 'android.hardware.common.fmq-V1-ndk.so',
         'libaudio_aidl_conversion_common_ndk.so', 'libaudioaidlcommon.so',
         'libaudioutils.so', 'libbase.so', 'libbinder_ndk.so', 'libcutils.so',
         'libfmq.so', 'liblog.so', 'libmedia_helper.so', 'libtinyxml2.so',
         'libutils.so', 'libapexsupport.so', 'libc++.so', 'libc.so', 'libm.so', 'libdl.so']


def original_library(name):
    path = libs / name
    # Absolute GSI links refer to its private root, never the Linux host root.
    for _ in range(20):
        if not path.is_symlink():
            assert path.is_file(), path
            assert path.is_relative_to(root), path
            return path
        target = path.readlink()
        path = root / str(target).lstrip('/') if target.is_absolute() else path.parent / target
        path = Path(os.path.normpath(path))
    raise ValueError('Original library symlink loop: ' + name)


shared = [original_library(name) for name in names]
toolchain = Path('/home/tv/.cache/archtv/aosp16-qpr2/native-toolchain-1/bin')
binary = out / ('libdynamicsprocessingaidl.so' if production_dynamics else
                'android.hardware.audio.effect.service-aidl.example')
cmd = [str(toolchain / 'ld.lld'), '--error-limit=0', '--no-undefined',
       '--no-allow-shlib-undefined', *(['-shared', '--as-needed', '-soname', binary.name]
          if production_dynamics else ['-pie', '--dynamic-linker=/system/bin/linker64']),
       '-z', 'relro', '-z', 'now', '--gc-sections', '--rpath-link=' + str(libs)]
cmd += ['--rpath-link=' + str(p) for p in (root / 'apex').glob('*/lib64')]
crt_begin = repo / ('dist/aosp16/libcutils-memfd-linux-2/crtbegin_so.o' if production_dynamics else
                    'dist/aosp16/crt-native-1/crtbegin_dynamic.o')
crt_end = repo / ('dist/aosp16/libcutils-memfd-linux-2/crtend_so.o' if production_dynamics else
                  'dist/aosp16/crt-native-1/crtend_android.o')
cmd += ['--rpath-link=' + str(root / 'apex/com.android.runtime/lib64/bionic'),
        str(crt_begin), '--whole-archive']
cmd += list(map(str, archives)) + ['--no-whole-archive'] + list(map(str, shared))
cmd += ['/home/tv/.cache/archtv/graphics-candidates-1/compiler-builtins/libclang_rt.builtins-x86_64-android.a',
        str(crt_end), '-o', str(binary)]
result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
(out / 'link.log').write_text(result.stdout + result.stderr)
record = {'scope': 'Original effect provider source binary linkage; no runtime/effects acceptance',
          'argv': cmd, 'exit': result.returncode,
          'inputs': {**production_inputs, **{str(p): hashlib.file_digest(p.open('rb'), 'sha256').hexdigest()
                     for p in archives + shared + [crt_begin, crt_end]}},
          'adaptation': 'Real apexsupport declarations included for outside-APEX Bionic build; no asserted APEX identity'}
if production_dynamics:
    record.update(scope='Complete original production DynamicsProcessing shared library; not runtime/DSP/audio acceptance',
                  adaptation='Original AIDL/context/common worker/ranges and real DPBase/DPFrequency engine; original Eigen MPL2 flag, Bionic/shared-library boundary. No source stubs or copy-through substitute.')
if result.returncode == 0:
    record['binary_sha256'] = hashlib.file_digest(binary.open('rb'), 'sha256').hexdigest()
(out / 'link.json').write_text(json.dumps(record, indent=2) + '\n')
print('original effect provider link', result.returncode, result.stderr[-3500:])
raise SystemExit(result.returncode)
