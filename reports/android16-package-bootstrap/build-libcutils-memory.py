#!/usr/bin/env python3
"""Build the complete original Bionic libcutils with an explicit memory backport.

No library installation, policy loading, APK or isolation acceptance here.
"""
from pathlib import Path
import hashlib
import json
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
out = (ROOT / sys.argv[1]).resolve()
out.mkdir()
source = Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/system-core/source/system/core')
bionic = Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/bionic-libc/source')
patch = ROOT / 'runtime/aosp/android16-qpr2/patches/libcutils-memfd-original-label.patch'
metadata = json.loads(patch.with_suffix('.json').read_text())
record = {'scope': 'Complete original libcutils, experimental AOSP memfd-label backport; build only', 'commands': [], 'inputs': {}}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def run(argv, **kwargs):
    result = subprocess.run(argv, capture_output=True, text=True, timeout=180, **kwargs)
    record['commands'].append({'argv': argv, 'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr})
    (out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
    if result.returncode:
        raise SystemExit(result.stderr or result.stdout)


assert digest(source / 'libcutils/ashmem-dev.cpp') == metadata['source_sha256']
assert digest(patch) == metadata['patch_sha256']
shutil.copytree(source / 'libcutils', out / 'libcutils')
run(['patch', '--batch', '--fuzz=0', '-p1', '-i', str(patch)], cwd=out)
assert digest(out / 'libcutils/ashmem-dev.cpp') == metadata['adapted_sha256']

# Preserve the already recorded original Bionic/Clang target configuration.
commands = json.loads((ROOT / 'dist/aosp16/hwc3-wayland-1/build.json').read_text())['commands']
template = next(row['argv'] for row in commands if '-c' in row['argv'])
flags = template[1:template.index('-c')]
if '-MF' in flags:
    pos = flags.index('-MF')
    del flags[pos:pos + 2]
flags = [flag for flag in flags if flag != '-MMD']
# This is the platform library, not the HWC's vendor variant. Keep platform
# exports and source behavior; do not inherit VNDK/vendor API selection.
flags = [flag for flag in flags if not flag.startswith(('-D__ANDROID_VNDK__', '-D__ANDROID_VENDOR__', '-D__ANDROID_VENDOR_API__='))]
flags += ['-I' + str(out / 'libcutils/include'), '-I' + str(source / 'libprocessgroup/include'),
          '-I' + str(source / 'include'), '-I' + str(bionic / 'async_safe/include')]
# Source lists from the pinned Android.bp: android + linux + sockets, no host code.
names = '''config_utils iosched_policy load_file native_handle properties record_stream
fs hashmap multiuser str_parms canned_fs_config fs_config android_reboot ashmem-dev
klog partition_utils qtaguid trace-dev uevent sockets android_get_control_file
socket_inaddr_any_server_unix socket_local_client_unix socket_local_server_unix
socket_network_client_unix sockets_unix'''.split()
objects = []
for name in names + ['strlcpy']:
    src = out / 'libcutils' / (name + ('.c' if name == 'strlcpy' else '.cpp'))
    obj = out / (name + '.o')
    opts = flags if src.suffix == '.cpp' else [f for f in flags if not f.startswith('-std=') and f != '-nostdinc++'] + ['-std=gnu17']
    record['inputs'][str(src)] = digest(src)
    run([template[0], *opts, '-c', str(src), '-o', str(obj)])
    objects.append(str(obj))

crt = json.loads((ROOT / 'dist/aosp16/crt-native-1/commands.json').read_text())[0]['argv']
crt_flags = crt[1:crt.index('-c')]
for name in ['crtbegin_so.c', 'crtend_so.S']:
    src = bionic / 'arch-common/bionic' / name
    obj = out / (Path(name).stem + '.o')
    record['inputs'][str(src)] = digest(src)
    run([crt[0], *crt_flags, '-fPIC', '-c', str(src), '-o', str(obj)])

gsi = ROOT / 'dist/aosp16/factory-inputs-3/root/system/lib64'
link = json.loads((ROOT / 'dist/aosp16/hwc3-wayland-1/link.json').read_text())['argv']
libs = [str(gsi / n) for n in ['liblog.so', 'libbase.so', 'libc++.so']]
for name in ['libc.so', 'libm.so', 'libdl.so']:
    item = next(Path(a[2:]) / name for a in link if a.startswith('-L') and (Path(a[2:]) / name).is_file())
    libs.append(str(item))
for path in libs:
    record['inputs'][path] = digest(Path(path))
target = out / 'libcutils.so'
run([link[0], '-shared', '--no-undefined', '-soname', 'libcutils.so', '-z', 'relro', '-z', 'now',
     str(out / 'crtbegin_so.o'), *objects, *libs, str(out / 'crtend_so.o'), '-o', str(target)])
record.update(terminal=True, library=str(target), sha256=digest(target), original_change=metadata)
(out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({'library': str(target), 'sha256': record['sha256'], 'scope': record['scope']}))
