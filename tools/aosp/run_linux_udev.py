#!/usr/bin/env python3
"""Run upstream SELinux-enabled udev in an existing private mount namespace.

This prepares a real libselinux view, never loads policy or changes enforcing.
The selected development label database is scoped; it is not a host relabel.
"""
import ctypes
import hashlib
import json
import os
from pathlib import Path
import stat
import subprocess
import sys


def main():
    assert os.geteuid() == 0
    asset = Path(sys.argv[1])
    assert asset.is_absolute() and asset.parent == Path('/opt/archtv/experimental/udev')
    assert os.readlink('/proc/self/ns/mnt') != os.readlink('/proc/1/ns/mnt'), 'private mounts required'
    for parent in [asset, *asset.parents]:
        info = parent.lstat()
        assert stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022
    manifest = json.loads((asset / 'manifest.json').read_text())
    for name, digest in manifest['files'].items():
        path = asset / name
        info = path.lstat()
        assert stat.S_ISREG(info.st_mode) and info.st_uid == 0 and not info.st_mode & 0o022
        assert hashlib.sha256(path.read_bytes()).hexdigest() == digest, name
    assert not any(' - selinuxfs ' in line for line in Path('/proc/self/mountinfo').read_text().splitlines())
    subprocess.run(['mount', '--make-rprivate', '/'], check=True)
    target = Path('/sys/fs/selinux')
    assert target.is_dir()
    # Original libselinux init.c deliberately rejects a read-only selinuxfs.
    # Keep the root mount writable for its detection, but make every child
    # read-only except the original query/validation transaction endpoints.
    # In particular load/enforce/booleans remain read-only in this namespace.
    subprocess.run(['mount', '-t', 'selinuxfs', '-o', 'nosuid,nodev,noexec', 'selinuxfs', str(target)], check=True)
    query_endpoints = {'access', 'create', 'relabel', 'user', 'context', 'validatetrans'}
    for child in target.iterdir():
        if child.name in query_endpoints:
            continue
        subprocess.run(['mount', '--bind', str(child), str(child)], check=True)
        subprocess.run(['mount', '-o', 'remount,bind,ro,nosuid,nodev,noexec', str(child)], check=True)
    assert all(os.statvfs(target / name).f_flag & os.ST_RDONLY for name in ['load', 'enforce', 'booleans'])
    config = Path('/etc/selinux')
    config.mkdir(exist_ok=True)
    subprocess.run(['mount', '--bind', str(asset / 'selinux'), str(config)], check=True)
    subprocess.run(['mount', '-o', 'remount,bind,ro,nosuid,nodev,noexec', str(config)], check=True)
    lib = ctypes.CDLL(str(asset / 'lib/libselinux.so.1'), use_errno=True)
    assert lib.is_selinux_enabled() == 1, 'original libselinux must detect SELinux'
    print(json.dumps({'event': 'ORIGINAL_LINUX_SELINUX_VIEW', 'enabled': True,
                      'enforce': lib.security_getenforce(), 'policy_sha256': hashlib.sha256((target / 'policy').read_bytes()).hexdigest(),
                      'mount_namespace': os.readlink('/proc/self/ns/mnt'),
                      'scope': 'Observed state; no policy load, enforcing change or hotplug acceptance'}), flush=True)
    if len(sys.argv) > 2 and sys.argv[2] == '--probe':
        return
    os.environ['LD_LIBRARY_PATH'] = str(asset / 'lib')
    # The original multicall binary selects daemon mode using its invocation name.
    os.execve(str(asset / 'udevadm.standalone'), ['systemd-udevd'], os.environ)


if __name__ == '__main__':
    main()
