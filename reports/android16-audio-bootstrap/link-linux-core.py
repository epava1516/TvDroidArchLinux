#!/usr/bin/env python3
"""Link the complete original audio core factory with reviewed Linux ALSA units.

Reuses verified prior original build objects and whole original Bluetooth groups.
A linked executable does not establish service, audio or APK compatibility.
"""
from pathlib import Path
import hashlib
import json
import subprocess
import sys

repo = Path(__file__).resolve().parents[2]
out = repo / sys.argv[1]
out.mkdir()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
old = json.loads((repo / 'dist/aosp16/audio-core-link-1/link.json').read_text())
for path, digest in old['inputs'].items():
    assert sha(path) == digest, path
core = json.loads((repo / 'dist/aosp16/audio-original-build-12/build.json').read_text())
for source in core['sources']:
    assert sha(source['path']) == source['sha256'], source['path']
write_diagnostic = '--write-diagnostic' in sys.argv[2:]
adapted_dir = repo / ('dist/aosp16/audio-linux-primary-build-2' if write_diagnostic else 'dist/aosp16/audio-linux-primary-build-1')
adapted = json.loads((adapted_dir / 'build.json').read_text())
assert len(adapted['objects']) == (3 if write_diagnostic else 2)
assert all(c['exit'] == 0 for c in adapted['commands'])
if write_diagnostic:
    assert adapted['write_diagnostic']
    assert any(u['original'].endswith('/alsa/StreamAlsa.cpp') for u in adapted['objects'])
    for path, expected in adapted['patches'].items():
        assert sha(path) == expected, path
replace = {}
for unit in adapted['objects']:
    assert sha(unit['object']) == unit['sha256']
    relative = Path(unit['original']).relative_to('/home/tv/.cache/archtv/aosp16-qpr2/audio-original-study-1/hardware-audio')
    assert sha(adapted_dir / 'source' / relative) == unit['source_sha256']
    previous = next(s['object'] for s in core['sources'] if s['path'] == unit['original'])
    replace[previous] = unit['object']
support = json.loads((repo / 'dist/aosp16/audio-support-build-11/build.json').read_text())
assert support['commands'][-1]['exit'] == 1  # Preserved final missing include diagnostic.
last = support['commands'][-1]['argv']
assert last[last.index('-c') + 1].endswith('com_android_btaudio_hal_flags.cc')
flagobj = out / 'btaudiohal-flags.o'
cmd = last[:last.index('-MMD')] + [
    '-I/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/aconfig-source/source/build/make/tools/aconfig/aconfig_storage_read_api/include',
    '-c', last[last.index('-c') + 1], '-o', str(flagobj)]
result = subprocess.run(cmd, capture_output=True, timeout=120)
(out / 'flags.log').write_bytes(result.stdout + result.stderr)
record = {'scope': 'Original core executable linkage only; no runtime or output acceptance',
          'commands': [{'argv': cmd, 'exit': result.returncode}], 'inputs': dict(old['inputs'])}
(out / 'link.json').write_text(json.dumps(record, indent=2) + '\n')
if result.returncode:
    print(result.stderr.decode(errors='replace')[-2500:])
    raise SystemExit(result.returncode)
archives = []
for name in ['libbluetooth_audio_session_aidl', 'android_hardware_bluetooth_audio_impl',
             'bluetooth_hidl', 'bluetooth_xml']:
    unit = support['archives'][name]
    assert sha(unit['path']) == unit['sha256']
    archives.append(unit['path'])
codecs = json.loads((repo / 'dist/aosp16/audio-codecs-build-3/build.json').read_text())
for unit in codecs['archives'].values():
    assert sha(unit['path']) == unit['sha256']
    archives.append(unit['path'])
rust = json.loads((repo / 'dist/aosp16/audio-offload-rust-library-2/build.json').read_text())
assert rust['exit'] == 0
assert sha(rust['archive']['path']) == rust['archive']['sha256']
archives.append(rust['archive']['path'])
flat = json.loads((repo / 'dist/aosp16/audio-support-build-12/build.json').read_text())['archives']['libflatbuffers_cpp']
assert sha(flat['path']) == flat['sha256']
archives.append(flat['path'])
# Preserve original shared-library boundaries: static flattening gives two
# different original DSOs the same exported isOpusHiResCodec symbol.
libs = repo / 'dist/aosp16/factory-inputs-3/root/system/lib64'
extra = [libs / n for n in ['libhidlbase.so', 'libbinder.so', 'libtinyxml2.so',
                            'server_configurable_flags.so', 'libaconfig_storage_read_api_cc.so']]
assert all(p.is_file() for p in extra)
platform = [Path(a) for a in old['argv'] if a.endswith('.so')] + extra
crt = repo / 'dist/aosp16/libcutils-memfd-linux-2'
assert (crt / 'crtbegin_so.o').is_file() and (crt / 'crtend_so.o').is_file()
search = [a for a in old['argv'] if a.startswith('--rpath-link=')]
outputs = []

def shared(name, objects, dependencies=(), whole=(), normal=()):
    target = out / name
    argv = [old['argv'][0], '-shared', '--error-limit=0', '--no-undefined',
            '--no-allow-shlib-undefined', '--as-needed', '-soname', name,
            '-z', 'relro', '-z', 'now', '--gc-sections',
            '--rpath-link=' + str(out), *search, str(crt / 'crtbegin_so.o'),
            *map(str, objects), '--whole-archive', *map(str, whole), '--no-whole-archive',
            '--start-group', *map(str, normal), '--end-group',
            *map(str, dependencies), *map(str, platform),
            '/home/tv/.cache/archtv/graphics-candidates-1/compiler-builtins/libclang_rt.builtins-x86_64-android.a',
            str(crt / 'crtend_so.o'), '-o', str(target)]
    result = subprocess.run(argv, capture_output=True, timeout=120)
    (out / (name + '.log')).write_bytes(result.stdout + result.stderr)
    record['commands'].append({'argv': argv, 'exit': result.returncode})
    (out / 'link.json').write_text(json.dumps(record, indent=2) + '\n')
    print(name, result.returncode, result.stderr.decode(errors='replace')[-3000:], flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)
    outputs.append(target)
    return target

hidl = []
for prefix, name in [('android/hidl/safe_union/1.0/', 'android.hidl.safe_union@1.0.so'),
                     ('android/hardware/audio/common/5.0/', 'android.hardware.audio.common@5.0.so'),
                     ('android/hardware/bluetooth/audio/2.0/', 'android.hardware.bluetooth.audio@2.0.so'),
                     ('android/hardware/bluetooth/audio/2.1/', 'android.hardware.bluetooth.audio@2.1.so')]:
    units = [u for u in support['sources'] if '/hidl/' + prefix in u['path']]
    assert units
    for u in units:
        assert sha(u['object']) == u['object_sha256']
        record['inputs'][u['object']] = u['object_sha256']
    hidl.append(shared(name, [u['object'] for u in units], hidl))
ndk = shared('android.hardware.bluetooth.audio-V5-ndk.so', [],
             whole=[repo / 'dist/aosp16/audio-support-build-5/libbluetooth_audio_v5_ndk.a'])
session = shared('libbluetooth_audio_session_aidl.so', [flagobj], [*hidl, ndk],
                 whole=[archives[0], archives[3]], normal=archives[4:])
impl = shared('android.hardware.bluetooth.audio-impl.so', [flagobj], [session, ndk],
              whole=[archives[1]])
cmd = [replace.get(a, a) for a in old['argv']]
cmd = [a for a in cmd if a != str(repo / 'dist/aosp16/audio-support-build-5/libbluetooth_audio_v5_ndk.a')]
idx = cmd.index('--no-whole-archive') + 1
cmd[idx:idx] = list(map(str, [ndk, session, impl])) + ['--rpath-link=' + str(out)]
binary = out / 'android.hardware.audio.service-aidl.example'
cmd[-1] = str(binary)
result = subprocess.run(cmd, capture_output=True, timeout=120)
(out / 'link.log').write_bytes(result.stdout + result.stderr)
record['commands'].append({'argv': cmd, 'exit': result.returncode})
for path in [*replace.values(), *archives, str(flagobj), *map(str, extra),
             *map(str, outputs), str(crt / 'crtbegin_so.o'), str(crt / 'crtend_so.o')]:
    record['inputs'][path] = sha(path)
record['inputs'][str(adapted_dir / 'build.json')] = sha(adapted_dir / 'build.json')
for unit in adapted['objects']:
    relative = Path(unit['original']).relative_to('/home/tv/.cache/archtv/aosp16-qpr2/audio-original-study-1/hardware-audio')
    source = adapted_dir / 'source' / relative
    record['inputs'][str(source)] = sha(source)
for path, expected in adapted.get('patches', {}).items():
    record['inputs'][path] = expected
record['write_diagnostic'] = write_diagnostic
if result.returncode == 0:
    record['binary_sha256'] = sha(binary)
(out / 'link.json').write_text(json.dumps(record, indent=2) + '\n')
print('original Linux ALSA core link', result.returncode, result.stderr.decode(errors='replace')[-6000:])
raise SystemExit(result.returncode)
