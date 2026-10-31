#!/usr/bin/env python3
"""Read-only Linux SELinux prerequisites; never certifies APK or policy semantics."""
import argparse
import ctypes
import gzip
import json
import mmap
import os
from pathlib import Path
import struct

REQUIRED_PERMISSIONS = {
    "binder": ["impersonate", "call", "transfer", "set_context_mgr"],
    "service_manager": ["add", "find", "list"],
    "hwservice_manager": ["add", "find", "list"],
    "property_service": ["set"],
}


def read_text(root, path):
    try:
        return {"state": "observed", "value": (root / path.lstrip('/')).read_text().strip()}
    except FileNotFoundError:
        return {"state": "absent"}
    except (OSError, UnicodeError) as exc:
        return {"state": "unknown", "error": type(exc).__name__, "errno": getattr(exc, 'errno', None)}


def status_snapshot(read):
    # Kernel status uses a seqlock. Never accept an inconsistent snapshot.
    for _ in range(20):
        before = struct.unpack('=I', read(4, 4))[0]
        if before & 1:
            continue
        values = struct.unpack('=5I', read(0, 20))
        after = struct.unpack('=I', read(4, 4))[0]
        if before == after == values[1] and not after & 1:
            return {"state": "observed", **dict(zip(
                ['version', 'sequence', 'enforcing', 'policyload', 'deny_unknown'], values))}
    return {"state": "unknown", "reason": "status changed throughout bounded snapshot"}


def zero_size_selinux_status(stream):
    # Python mmap rejects a page beyond st_size=0. selinuxfs intentionally has
    # zero-sized virtual files. Check its filesystem before native mapping so an
    # empty regular file can never cause SIGBUS when dereferenced.
    libc = ctypes.CDLL(None, use_errno=True)
    stat = ctypes.create_string_buffer(256)  # Linux statfs fits; f_type is first long.
    libc.fstatfs.argtypes = [ctypes.c_int, ctypes.c_void_p]
    if libc.fstatfs(stream.fileno(), stat) != 0:
        raise OSError(ctypes.get_errno(), "fstatfs status")
    if ctypes.c_long.from_buffer(stat).value & 0xffffffff != 0xf97cff8c:
        raise ValueError("zero-sized status is not on selinuxfs")
    libc.mmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t, ctypes.c_int,
                          ctypes.c_int, ctypes.c_int, ctypes.c_long]
    libc.mmap.restype = ctypes.c_void_p
    libc.munmap.argtypes = [ctypes.c_void_p, ctypes.c_size_t]
    address = libc.mmap(None, mmap.PAGESIZE, mmap.PROT_READ, mmap.MAP_SHARED, stream.fileno(), 0)
    if address == ctypes.c_void_p(-1).value:
        raise OSError(ctypes.get_errno(), "mmap selinux status")
    try:
        return status_snapshot(lambda offset, size: ctypes.string_at(address + offset, size))
    finally:
        libc.munmap(address, mmap.PAGESIZE)


def read_status(root):
    path = root / 'sys/fs/selinux/status'
    try:
        with path.open('rb') as stream:
            if os.fstat(stream.fileno()).st_size == 0:
                return zero_size_selinux_status(stream)
            with mmap.mmap(stream.fileno(), mmap.PAGESIZE, flags=mmap.MAP_SHARED,
                           prot=mmap.PROT_READ) as area:
                return status_snapshot(lambda offset, size: area[offset:offset + size])
    except FileNotFoundError:
        return {"state": "absent"}
    except (OSError, ValueError, struct.error) as exc:
        return {"state": "unknown", "error": type(exc).__name__, "errno": getattr(exc, 'errno', None)}


def inspect(root):
    lsm = read_text(root, '/sys/kernel/security/lsm')
    enforce = read_text(root, '/sys/fs/selinux/enforce')
    status = read_status(root)
    version = read_text(root, '/sys/fs/selinux/policyvers')
    classes = {}
    for name, permissions in REQUIRED_PERMISSIONS.items():
        classes[name] = {permission: read_text(root,
            f'/sys/fs/selinux/class/{name}/perms/{permission}') for permission in permissions}
    checks = {
        'selinux_active_lsm': lsm['state'] == 'observed' and 'selinux' in lsm['value'].split(','),
        'enforcing': enforce.get('value') == '1' and status.get('enforcing') == 1,
        'status_v1_consistent': status.get('version') == 1 and status.get('state') == 'observed',
        'policy_loaded': status.get('policyload', 0) > 0,
        'policy_version_exposed': version.get('value', '').isdigit() and int(version['value']) > 0,
        'required_class_permissions_exposed': all(
            row['state'] == 'observed' and row['value'].isdigit() and int(row['value']) > 0
            for permissions in classes.values() for row in permissions.values()),
    }
    config = {}
    try:
        with gzip.open(root / 'proc/config.gz', 'rt') as stream:
            for line in stream:
                if line.startswith(('CONFIG_SECURITY_SELINUX=', 'CONFIG_LSM=',
                                    'CONFIG_ANDROID_BINDER_IPC_RUST=')):
                    key, value = line.strip().split('=', 1)
                    config[key] = value
    except (OSError, UnicodeError):
        pass  # Optional build facts cannot replace observed live kernel interfaces.
    live = root.resolve() == Path('/')
    return {
        'scope': 'Kernel prerequisites only. Does not prove service readiness, labels, transitions, '
                 'AVC decisions, Binder caller identity, app isolation or APK compatibility.',
        'observation_mode': 'current_mount_view' if live else 'offline_snapshot',
        'observation_root': str(root.resolve()),
        'euid': os.geteuid(),
        'observations': {'active_lsm': lsm, 'enforce': enforce, 'status': status,
                         'policy_version': version, 'classes': classes, 'optional_build_config': config},
        'checks': checks,
        'observed_checks_passed': all(checks.values()),
        'kernel_prerequisites_passed': live and all(checks.values()),
        'policy_semantics_verified': False,
        'runtime_ready': False,
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path('/'),
                        help='Read an offline snapshot instead; never identifies it as a live host')
    args = parser.parse_args()
    result = inspect(args.root)
    print(json.dumps(result, indent=2))
    return 0 if result['kernel_prerequisites_passed'] else 2


if __name__ == '__main__':
    raise SystemExit(main())
