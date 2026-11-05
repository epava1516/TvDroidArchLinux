"""Scoped development host labels, applied before compositor/enforcing.

Reuse original refpolicy devices.fc, init.fc and systemd.fc types plus the
existing explicit compositor-device adapter. Never relabel the whole host,
create service state, change DAC, load policy or manufacture readiness.
"""
from pathlib import Path
import ctypes
import hashlib
import json
import os
import stat
import subprocess

POLICY69 = 'd8b79d1fb58c875f06ee804c83fa3ee90dcd2a5fb0b356f425179e392cbeb818'
PREFIX = 'linux.system_u:linux.object_r:'


def prepare(cp, lib):
    assert os.geteuid() == 0
    assert not subprocess.check_output(['systemctl', 'list-units', '--state=running',
        '--no-legend', 'archtv-package-runner-*', 'archtv-apex-*'], text=True).strip()
    record = cp/'host-label-preparation.json'
    assert not record.exists(), 'Immutable run already has host label preparation'
    control = Path('/run/archtv-host-label-query')
    control.mkdir(exist_ok=True)
    subprocess.run(['mount', '-t', 'selinuxfs', '-o', 'ro,nosuid,nodev,noexec',
                    'selinuxfs', str(control)], check=True)
    changed = []
    rows = []
    lib.lsetfilecon_raw.argtypes = [ctypes.c_char_p, ctypes.c_char_p]
    lib.lsetfilecon_raw.restype = ctypes.c_int
    try:
        assert (control/'enforce').read_text().strip() == '0'
        assert hashlib.sha256((control/'policy').read_bytes()).hexdigest() == POLICY69
        targets = {}
        for path in ['/dev', '/dev/dri', '/dev/input']:
            targets[Path(path)] = ('dir', 'linux.device_t')
        # Original refpolicy devices.fc45/100/118/140/170.
        for name, kind in [('null', 'null'), ('full', 'null'), ('zero', 'zero'),
                           ('random', 'random'), ('urandom', 'urandom')]:
            targets[Path('/dev')/name] = ('chr', 'linux.'+kind+'_device_t')
        # Existing linux-compositor.cil admits only explicitly typed seat nodes.
        for pattern in ['/dev/dri/card[0-9]*', '/dev/dri/renderD[0-9]*',
                        '/dev/input/event[0-9]*']:
            for p in Path('/').glob(pattern.lstrip('/')):
                targets[p] = ('chr', 'archtv_compositor_device')
        for path in ['/dev/tty', '/dev/tty0', '/dev/tty2']:
            targets[Path(path)] = ('chr', 'archtv_compositor_device')
        targets[Path('/run/systemd')] = ('dir', 'linux.init_runtime_t')
        # Original systemd.fc119/120/121/122; original udev scoped database.
        for path, kind in [('/run/systemd/seats', 'systemd_sessions_runtime_t'),
                           ('/run/systemd/sessions', 'systemd_sessions_runtime_t'),
                           ('/run/systemd/users', 'systemd_logind_runtime_t'),
                           ('/run/systemd/shutdown', 'systemd_logind_runtime_t'),
                           ('/run/udev', 'udev_runtime_t')]:
            root = Path(path)
            if not root.exists():
                rows.append({'path': path, 'absent': True,
                             'scope': 'No directory or service state created'})
                continue
            children = [root, *root.rglob('*')]
            assert len(children) <= 4096, 'Unexpected host state volume'
            for p in children:
                targets[p] = ('runtime', 'linux.'+('udev_rules_t' if path == '/run/udev' and p.is_relative_to(Path('/run/udev/rules.d')) else kind))
        for path, (kind, type_) in targets.items():
            try:
                info = path.lstat()
                assert (kind == 'chr' and stat.S_ISCHR(info.st_mode) or
                        kind == 'dir' and stat.S_ISDIR(info.st_mode) or
                        kind == 'runtime' and (stat.S_ISDIR(info.st_mode) or
                           stat.S_ISREG(info.st_mode) or stat.S_ISLNK(info.st_mode) or
                           stat.S_ISSOCK(info.st_mode) or stat.S_ISFIFO(info.st_mode))), str(path)
                before = os.getxattr(path, 'security.selinux', follow_symlinks=False)
                after = (PREFIX+type_+':s0').encode()
                row = {'path': str(path), 'device': info.st_dev, 'inode': info.st_ino,
                       'uid': info.st_uid, 'gid': info.st_gid, 'mode': oct(stat.S_IMODE(info.st_mode)),
                       'rdev': info.st_rdev, 'before': before.rstrip(b'\0').decode(),
                       'expected': after.decode()}
                if before.rstrip(b'\0') != after:
                    assert lib.lsetfilecon_raw(os.fsencode(path), after) == 0, (str(path), ctypes.get_errno())
                    changed.append((path, info, before))
                current = path.lstat()
                assert (info.st_dev, info.st_ino, info.st_mode, info.st_uid, info.st_gid, info.st_rdev) == (
                    current.st_dev, current.st_ino, current.st_mode, current.st_uid, current.st_gid, current.st_rdev)
                assert os.getxattr(path, 'security.selinux', follow_symlinks=False).rstrip(b'\0') == after
                row['verified'] = True
                rows.append(row)
            except FileNotFoundError:
                if kind != 'runtime' or path.exists() or path.is_symlink():
                    raise
                rows.append({'path': str(path), 'retired_during_scan': True,
                             'scope': 'Original transient service metadata disappeared; no file/state created or label inferred'})
        with record.open('x') as stream:
            json.dump({'policy_sha256': POLICY69, 'mode': 0, 'rows': rows,
                'Linux_libselinux': lib._name, 'scope': 'Scoped host labeling only; original service state/DAC retained. No API, permission grant, policy/enforcing change or APK/MAC acceptance.'}, stream, indent=2)
        os.chown(record, 1000, 1000)
    except BaseException:
        for path, info, before in reversed(changed):
            try:
                if path.lstat().st_ino == info.st_ino:
                    assert lib.lsetfilecon_raw(os.fsencode(path), before) == 0, str(path)
            except FileNotFoundError:
                pass  # The retired original inode cannot be relabelled; never recreate it.
        raise
    finally:
        subprocess.run(['umount', str(control)], check=True)
