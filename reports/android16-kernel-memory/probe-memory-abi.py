#!/usr/bin/env python3
"""Exercise the real x86_64 memfd/ashmem ABI; never set Android properties."""
import argparse
import datetime
import errno
import fcntl
import json
import mmap
import os
import platform
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
assert platform.machine() == 'x86_64', 'ioctl encodings below are x86_64 only'
assert not args.output.exists(), 'preserve prior evidence; choose a new output'
record = {
    'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
    'kernel': platform.release(),
    'boot_id': Path('/proc/sys/kernel/random/boot_id').read_text().strip(),
    'scope': 'Direct Linux x86_64 ABI execution, not original libcutils execution, MAC authorization or APK compatibility',
    'checks': {},
    'limits': ['No ARM/compat32 test', 'No legacy /dev/ashmem test',
               'ACK shim retains read/execute mapping permissions; not full legacy ashmem semantics'],
}
checks = record['checks']
fd = os.memfd_create('archtv-memory-abi', os.MFD_CLOEXEC | os.MFD_ALLOW_SEALING)
region = None
try:
    os.ftruncate(fd, 4096)
    region = mmap.mmap(fd, 4096, flags=mmap.MAP_SHARED,
                       prot=mmap.PROT_READ | mmap.PROT_WRITE)
    region[:4] = b'ABI!'
    # Same necessary capability gate used by original libcutils, plus negatives.
    fcntl.fcntl(fd, fcntl.F_ADD_SEALS, 0x10)  # F_SEAL_FUTURE_WRITE
    checks['future_write_seal'] = bool(fcntl.fcntl(fd, fcntl.F_GET_SEALS) & 0x10)
    try:
        size = fcntl.ioctl(fd, 0x7704, 0)  # ASHMEM_GET_SIZE
        checks['ashmem_get_size'] = {'value': size, 'pass': size == 4096}
    except OSError as exc:
        checks['ashmem_get_size'] = {'errno': exc.errno, 'pass': False}
    # Existing writable mappings must remain usable while new ones are denied.
    region[:4] = b'OLD!'
    checks['existing_mapping_writable'] = region[:4] == b'OLD!'
    try:
        with mmap.mmap(fd, 4096, flags=mmap.MAP_SHARED,
                       prot=mmap.PROT_READ | mmap.PROT_WRITE):
            checks['new_writable_mapping_denied'] = False
    except OSError as exc:
        checks['new_writable_mapping_denied'] = exc.errno == errno.EPERM
    try:
        os.pwrite(fd, b'BAD!', 0)
        checks['pwrite_denied'] = False
    except OSError as exc:
        checks['pwrite_denied'] = exc.errno == errno.EPERM
    with mmap.mmap(fd, 4096, flags=mmap.MAP_SHARED, prot=mmap.PROT_READ) as reader:
        checks['read_mapping_preserves_data'] = reader[:4] == b'OLD!'
    try:
        fcntl.ioctl(fd, 0x77ff, 0)
        checks['unknown_ioctl_denied'] = False
    except OSError as exc:
        checks['unknown_ioctl_denied'] = exc.errno == errno.ENOTTY
    try:
        # GET_PROT_MASK after sealing must not advertise PROT_WRITE.
        mask = fcntl.ioctl(fd, 0x7706, 0)
        checks['ashmem_protection_mask'] = {'value': mask, 'pass': mask == 5}
        try:
            fcntl.ioctl(fd, 0x40087705, 7)  # SET_PROT_MASK cannot restore write
            checks['ashmem_restore_write_denied'] = False
        except OSError as exc:
            checks['ashmem_restore_write_denied'] = exc.errno == errno.EINVAL
        # Explicitly expose the upstream limitation: removing read/exec is a nop.
        result = fcntl.ioctl(fd, 0x40087705, 0)
        mask = fcntl.ioctl(fd, 0x7706, 0)
        record['read_exec_removal_observation'] = {'set_return': result, 'remaining_mask': mask}
    except OSError as exc:
        checks['ashmem_protection_mask'] = {'errno': exc.errno, 'pass': False}
finally:
    if region is not None:
        region.close()
    os.close(fd)
record['abi_gate_pass'] = all(v.get('pass', False) if isinstance(v, dict) else v
                              for v in checks.values())
args.output.parent.mkdir(parents=True, exist_ok=True)
with args.output.open('x') as stream:
    json.dump(record, stream, indent=2)
    stream.write('\n')
print(json.dumps(record, indent=2))
raise SystemExit(0 if record['abi_gate_pass'] else 1)
