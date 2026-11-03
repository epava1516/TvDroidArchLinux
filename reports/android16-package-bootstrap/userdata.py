"""Owned experimental Linux /data storage; Android alone creates its state."""
from pathlib import Path
import fcntl
import json
import os
import re
import shutil
import stat
import subprocess
import uuid

BASE = Path('/home/tv/.local/share/archtv/experimental-userdata')


def prepare(root, out, name):
    assert os.geteuid() == 0 and re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,47}', name)
    assert Path('/proc/self/ns/mnt').stat().st_ino != Path('/proc/1/ns/mnt').stat().st_ino
    BASE.mkdir(parents=True, mode=0o700, exist_ok=True)
    assert BASE.resolve() == BASE and BASE.lstat().st_uid == 0
    assert stat.S_IMODE(BASE.stat().st_mode) == 0o700
    store = BASE / name
    store.mkdir(mode=0o700, exist_ok=True)
    assert store.resolve() == store and store.lstat().st_uid == 0
    assert stat.S_IMODE(store.stat().st_mode) == 0o700
    lock = os.open(store / 'lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    assert os.fstat(lock).st_uid == 0
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    data = store / 'data'
    data.mkdir(mode=0o755, exist_ok=True)
    assert data.resolve() == data and stat.S_ISDIR(data.lstat().st_mode)
    assert data.stat().st_uid in (0, 1000) and not (data.stat().st_mode & 0o002)
    marker = store / 'store.json'
    if not marker.exists():
        assert not any(data.iterdir()), 'Never adopt unknown nonempty Android data'
        with marker.open('x') as stream:
            json.dump({'format': 'archtv-experimental-userdata-v1', 'name': name,
                       'storage_uuid': str(uuid.uuid4())}, stream)
        marker.chmod(0o600)
    assert stat.S_ISREG(marker.lstat().st_mode) and marker.stat().st_uid == 0
    metadata = json.loads(marker.read_text())
    assert metadata['format'] == 'archtv-experimental-userdata-v1' and metadata['name'] == name
    prior = None
    diagnostic = data / 'local/tmp/archtv-mc1'
    if diagnostic.exists() or diagnostic.is_symlink():
        info = diagnostic.lstat()
        assert stat.S_ISDIR(info.st_mode) and info.st_uid == 2000 and info.st_gid == 1000
        assert stat.S_IMODE(info.st_mode) == 0o750
        archive = store / 'diagnostics'
        archive.mkdir(mode=0o700, exist_ok=True)
        assert archive.resolve() == archive and archive.stat().st_uid == 0
        prior = archive / out.name
        assert not prior.exists()
        diagnostic.rename(prior)  # Preserve evidence; remove no application data.
    prior_root_client = None
    root_client = data / 'local/tmp/archtv-apex-client'
    if root_client.exists() or root_client.is_symlink():
        info = root_client.lstat()
        assert stat.S_ISDIR(info.st_mode) and info.st_uid == 0 and info.st_gid == 0
        assert stat.S_IMODE(info.st_mode) == 0o700
        archive = store / 'diagnostics'
        archive.mkdir(mode=0o700, exist_ok=True)
        assert archive.resolve() == archive and archive.stat().st_uid == 0
        prior_root_client = archive / (out.name + '-apex-root-client')
        assert not prior_root_client.exists()
        root_client.rename(prior_root_client)
    subprocess.run(['mount', '--bind', str(data), str(root / 'data')], check=True)
    source = data.stat()
    target = (root / 'data').stat()
    assert (source.st_dev, source.st_ino) == (target.st_dev, target.st_ino)
    fd = os.open(data, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC)
    record = {**metadata, 'path': str(data), 'device': source.st_dev, 'inode': source.st_ino,
              'prior_diagnostics': str(prior) if prior else None,
              'prior_root_client_diagnostics': str(prior_root_client) if prior_root_client else None,
              'scope': 'Owned private experimental data; no APK, user, key, permission or readiness seeded. No encryption/MAC acceptance.'}
    (out / 'userdata-mount.json').write_text(json.dumps(record, indent=2) + '\n')
    print('LINUX_PRIVATE_USERDATA_MOUNT ' + json.dumps(record), flush=True)
    return lock, fd
