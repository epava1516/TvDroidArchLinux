#!/usr/bin/env python3
"""Build a distinct LTS candidate at two jobs; never install or boot it."""
from pathlib import Path
import argparse, datetime, fcntl, hashlib, json, os, signal, subprocess, time

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--source', type=Path, required=True)
parser.add_argument('--build', type=Path, required=True)
parser.add_argument('--base-config', type=Path, required=True)
args = parser.parse_args()
source, build = args.source.resolve(), args.build.resolve()
os.umask(0o077)
def digest(path):
    result = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(2*1024*1024), b''):
            result.update(block)
    return result.hexdigest()
def config(path):
    result = {}
    for line in path.read_text().splitlines():
        if line.startswith('CONFIG_'):
            key, value = line.split('=', 1)
            result[key] = value
        elif line.startswith('# CONFIG_') and line.endswith(' is not set'):
            result[line[2:-11]] = 'n'
    return result
before, after = config(args.base_config), config(build / '.config')
changes = {key: [before.get(key), after.get(key)] for key in before.keys() | after.keys()
           if before.get(key) != after.get(key)}
assert set(changes) == {'CONFIG_LOCALVERSION', 'CONFIG_LOCALVERSION_AUTO', 'CONFIG_MEMFD_ASHMEM_SHIM'}, changes
for name in ['CONFIG_RUST', 'CONFIG_ANDROID_BINDER_IPC_RUST', 'CONFIG_SECURITY_SELINUX', 'CONFIG_MEMFD_ASHMEM_SHIM']:
    assert after[name] == 'y', name
assert after['CONFIG_LOCALVERSION'] == '"-archtv-aosp16-1"'
assert (build / 'mm/memfd-ashmem-shim.o').is_file()
lock = (build / '.full-kernel.lock').open('w')
fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
# The lock prevents concurrent invocations of this runner; recovery must still
# contrast real processes/tool handles, not infer termination from a lock file.
argv = ['nice', '-n', '10', 'make', '-C', str(source), 'O='+str(build), '-j2', 'bzImage', 'modules']
record = {'started_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'scope': 'Full candidate build only; no install/boot, kernel ABI runtime, services, security or APK acceptance',
    'argv': argv, 'config_changes': changes, 'config_sha256': digest(build / '.config'),
    'shim_object_sha256': digest(build / 'mm/memfd-ashmem-shim.o'),
    'pid_namespace': os.readlink('/proc/self/ns/pid'), 'state': 'starting',
    'log': str(build / 'full-build.log')}
path = build / 'full-build.json'
def save():
    path.write_text(json.dumps(record, indent=2)+'\n')
save()
child = None
interrupted = False
def stop(signum, frame):
    global interrupted
    interrupted = True
    if child is not None and child.poll() is None:
        os.killpg(child.pid, signal.SIGTERM)
        try:
            child.wait(timeout=10)
        except subprocess.TimeoutExpired:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
signal.signal(signal.SIGTERM, stop)
signal.signal(signal.SIGINT, stop)
start = time.monotonic()
with (build / 'full-build.log').open('w') as stream:
    child = subprocess.Popen(argv, stdout=stream, stderr=subprocess.STDOUT, start_new_session=True)
    record.update(state='running', pid_in_tool_namespace=child.pid)
    save()
    print('KERNEL_BUILD_STARTED '+str(path), flush=True)
    code = child.wait()
record.update(state='interrupted' if interrupted else 'terminal', exit=code,
              seconds=time.monotonic()-start, active=False)
if code == 0 and not interrupted:
    image = build / 'arch/x86/boot/bzImage'
    record['image_sha256'] = digest(image)
    record['vmlinux_sha256'] = digest(build / 'vmlinux')
    record['module_count'] = sum(1 for _ in build.rglob('*.ko'))
    record['kernel_release'] = (build / 'include/config/kernel.release').read_text().strip()
save()
print('KERNEL_BUILD_TERMINAL '+str(code)+' '+str(path), flush=True)
raise SystemExit(code if code else 130 if interrupted else 0)
