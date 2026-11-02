#!/usr/bin/env python3
"""Build the original complete IKeyMintDevice v4 software provider, not Keystore readiness."""
from pathlib import Path
import hashlib, json, subprocess, sys

r = Path(__file__).resolve().parents[2]
out = (r / sys.argv[1]).resolve()
out.mkdir()
inputs = Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs')
km = inputs / 'keymaster-original-v4/source/system/keymaster'
hw = inputs / 'security-hal-original/source/hardware/interfaces/security'
cache = Path('/home/tv/.cache/archtv/graphics-candidates-1')
record = {'scope': 'Source build only; no keys, service execution, Keystore, user or APK acceptance',
          'commands': [], 'sources': [], 'provenance': {}}
for name in ['keymaster-original-v4', 'security-hal-original', 'keymint-boringssl-headers', 'keymint-cppbor-original-headers']:
    p = inputs / name / 'provenance.json'
    d = json.loads(p.read_text())
    assert d['status'] == 'complete', name
    record['provenance'][name] = d

def run(argv):
    argv = list(map(str, argv))
    p = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    record['commands'].append(dict(argv=argv, exit=p.returncode, stdout=p.stdout, stderr=p.stderr))
    (out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
    print(Path(argv[0]).name, p.returncode, p.stderr[:1800], flush=True)
    if p.returncode:
        raise RuntimeError('Original provider build failed; see build.json')

apis = [hw / 'keymint/aidl/aidl_api/android.hardware.security.keymint/4',
        hw / 'secureclock/aidl/aidl_api/android.hardware.security.secureclock/1']
for api, version in zip(apis, [4, 1]):
    run([r / 'dist/aosp16/aidl-host-build-4/aidl', '--lang=ndk', '--structured',
         '--stability=vintf', '--version=' + str(version),
         '--hash=' + (api / '.hash').read_text().splitlines()[-1],
         '--min_sdk_version=29', '--omit_invocation',
         '--out=' + str(out / 'aidl/src'), '--header_out=' + str(out / 'aidl/include')]
        + ['-I' + str(p) for p in apis] + sorted(api.rglob('*.aidl')))
flags = json.loads((r / 'reports/android16-hwc3-frontend/build.json').read_text())['results'][0]['argv']
flags = flags[:flags.index('-MMD')]
flags += ['-I' + str(p) for p in [out / 'aidl/include', km / 'include', km / 'ng/include',
          inputs / 'keymint-boringssl-headers/source/external/boringssl/src/include',
          inputs / 'keymint-cppbor-original-headers/source/system/libcppbor/include/cppbor']]
# Reuse the original portable crypto/context libraries from the pinned factory;
# rebuild the entire IKeyMintDevice/operation/conversion implementation as v4.
units = [km / 'ng' / p for p in ['AndroidKeyMintDevice.cpp', 'AndroidKeyMintOperation.cpp', 'KeyMintUtils.cpp']]
units += [km / 'android_keymaster/keymaster_configuration.cpp',
          r / 'runtime/aosp/native/linux-keymint-service.cpp']
for i, p in enumerate(units):
    obj = out / (str(i) + '.o')
    run(flags + ['-c', p, '-o', obj])
    record['sources'].append(dict(path=str(p), sha256=hashlib.sha256(p.read_bytes()).hexdigest(), object=str(obj)))
libs = r / 'dist/aosp16/factory-inputs-3/root/system/lib64'
support = r / 'dist/aosp16/hwc3-frontend-2/link-libs'
needed = ['android.hardware.security.keymint-V4-ndk.so', 'android.hardware.security.secureclock-V1-ndk.so',
          'libkeymaster_portable.so', 'libkeymaster_messages.so', 'libpuresoftkeymasterdevice.so',
          'libbase.so', 'libbinder_ndk.so', 'libcrypto.so', 'libcutils.so', 'liblog.so',
          'libutils.so', 'libc++.so', 'libc.so', 'libm.so', 'libdl.so']
binary = out / 'archtv-keymint-software'
run([inputs.parent / 'native-toolchain-1/bin/ld.lld', '--no-undefined', '--no-allow-shlib-undefined',
     '-pie', '--dynamic-linker=/system/bin/linker64', '-z', 'relro', '-z', 'now',
     '--rpath-link=' + str(libs), '--rpath-link=' + str(support),
     r / 'dist/aosp16/crt-native-1/crtbegin_dynamic.o']
    + [x['object'] for x in record['sources']] + ['-L' + str(libs), '-L' + str(support)]
    + ['-l:' + n for n in needed]
    + [cache / 'compiler-builtins/libclang_rt.builtins-x86_64-android.a',
       r / 'dist/aosp16/crt-native-1/crtend_android.o', '-o', binary])
record['linked_libraries_sha256'] = {str((libs / n) if (libs / n).exists() else (support / n)): hashlib.sha256(((libs / n) if (libs / n).exists() else (support / n)).read_bytes()).hexdigest() for n in needed}
record['binary_sha256'] = hashlib.sha256(binary.read_bytes()).hexdigest()
provider_link = record['commands'][-1]['argv']
probe_source = r / 'fixtures/aosp-keymint-software/SoftwareCryptoProbe.cpp'
probe_hash = hashlib.sha256(probe_source.read_bytes()).hexdigest()
run(flags + ['-c', probe_source, '-o', out / 'probe.o'])
probe_compile = record['commands'][-1]
probe_binary = out / 'keymint-crypto-probe'
run([str(out / 'probe.o') if x == str(out / '4.o') else str(probe_binary) if x == str(binary) else x for x in provider_link])
assert hashlib.sha256(probe_source.read_bytes()).hexdigest() == probe_hash
probe_record = {'scope': 'Build only, not crypto/Keystore/user/APK acceptance',
                'probe_compile': probe_compile, 'probe_link': record['commands'][-1],
                'source_sha256': probe_hash,
                'binary_sha256': hashlib.sha256(probe_binary.read_bytes()).hexdigest()}
(out / 'probe-build.json').write_text(json.dumps(probe_record, indent=2) + '\n')
record['probe'] = probe_record
record['terminal'] = True
(out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
