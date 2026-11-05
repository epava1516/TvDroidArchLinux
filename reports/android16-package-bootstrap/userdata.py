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
from contextlib import contextmanager


@contextmanager
def mounted_verity_store(name, out, capacity=256 * 1024 * 1024):
    """Own one preallocated ext4 data image, with original fs-verity support.

    Called by the Linux host owner, outside Android namespaces. The existing
    observer can read evidence until it returns; then this mount/loop closes.
    Existing directory stores are never migrated, adopted or overwritten.
    """
    assert os.geteuid() == 0 and re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,47}', name)
    assert capacity in (256 * 1024 * 1024, 1024 * 1024 * 1024)  # Explicit experimental sizes, not production sizing.
    out = Path(out)
    assert not (out / 'backing-before.json').exists(), 'Execution already started'
    BASE.mkdir(parents=True, mode=0o700, exist_ok=True)
    assert BASE.resolve() == BASE and BASE.stat().st_uid == 0
    assert stat.S_IMODE(BASE.stat().st_mode) == 0o700
    store = BASE / name
    store.mkdir(mode=0o700, exist_ok=True)
    assert store.resolve() == store and store.stat().st_uid == 0
    assert stat.S_IMODE(store.stat().st_mode) == 0o700
    lock = os.open(store / 'backing.lock', os.O_CREAT | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
    assert os.fstat(lock).st_uid == 0
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    image = store / 'data.ext4'
    marker = store / 'store.json'
    data = store / 'data'
    data.mkdir(mode=0o755, exist_ok=True)
    assert data.resolve() == data and data.stat().st_uid == 0
    assert not os.path.ismount(data) and not any(data.iterdir())
    try:
        if not marker.exists():
            assert not image.exists(), 'Never adopt an unrecorded image'
            free = os.statvfs(store)
            assert free.f_bavail * free.f_frsize >= capacity + 64 * 1024 * 1024, 'Preserve host headroom'
            fd = os.open(image, os.O_CREAT | os.O_EXCL | os.O_RDWR | os.O_NOFOLLOW | os.O_CLOEXEC, 0o600)
            try:
                os.posix_fallocate(fd, 0, capacity)  # Real reservation; no thin-provisioned free-space claim.
            finally:
                os.close(fd)
            subprocess.run(['mkfs.ext4', '-q', '-F', '-b', '4096', '-O', 'verity', '-m', '0',
                            '-E', 'nodiscard,lazy_itable_init=0,lazy_journal_init=0', str(image)], check=True)
            filesystem_uuid = subprocess.check_output(['blkid', '-s', 'UUID', '-o', 'value', str(image)], text=True).strip()
            metadata = {'format': 'archtv-experimental-userdata-v1', 'name': name,
                        'storage_uuid': str(uuid.uuid4()),
                        'backing': {'kind': 'preallocated-ext4-verity-v1', 'image': str(image),
                                    'capacity': capacity, 'filesystem_uuid': filesystem_uuid}}
            with marker.open('x') as stream:
                json.dump(metadata, stream)
            marker.chmod(0o600)
        assert marker.is_file() and marker.stat().st_uid == 0 and not marker.is_symlink()
        metadata = json.loads(marker.read_text())
        assert metadata['format'] == 'archtv-experimental-userdata-v1' and metadata['name'] == name
        backing = metadata['backing']
        assert backing['kind'] == 'preallocated-ext4-verity-v1' and backing['image'] == str(image)
        st = image.lstat()
        assert stat.S_ISREG(st.st_mode) and st.st_uid == 0 and stat.S_IMODE(st.st_mode) == 0o600
        assert st.st_size == backing['capacity'] == capacity and st.st_blocks * 512 >= capacity
        assert subprocess.check_output(['blkid', '-s', 'UUID', '-o', 'value', str(image)], text=True).strip() == backing['filesystem_uuid']
        features = subprocess.check_output(['tune2fs', '-l', str(image)], text=True)
        assert 'verity' in next(l.split(':', 1)[1].split() for l in features.splitlines() if l.startswith('Filesystem features:'))
        assert next(l.split(':', 1)[1].strip() for l in features.splitlines() if l.startswith('Block size:')) == '4096'
        assert not subprocess.check_output(['losetup', '-j', str(image)], text=True).strip()
        # Keep data outside the original APEX RW pool0..89 and payload128/129.
        loop_id = 130
        kernel = Path('/sys/devices/virtual/block/loop130')
        created_loop = not kernel.exists()
        control = os.open('/dev/loop-control', os.O_RDWR | os.O_CLOEXEC)
        try:
            if created_loop:
                fcntl.ioctl(control, 0x4c80, loop_id)
        finally:
            os.close(control)
        assert not (kernel / 'loop/backing_file').exists()
        major, minor = map(int, (kernel / 'dev').read_text().split(':'))
        node = store / 'loop130'
        assert not node.exists()
        os.mknod(node, stat.S_IFBLK | 0o600, os.makedev(major, minor))
        loop = str(node)
        subprocess.run(['losetup', loop, str(image)], check=True)
        record = {'store': metadata, 'image_inode': st.st_ino, 'image_device': st.st_dev,
                  'allocated_bytes': st.st_blocks * 512, 'loop': loop, 'mountpoint': str(data),
                  'loop_id': loop_id, 'created_loop': created_loop,
                  'scope': 'Original filesystem capability, no APK/key/permission/readiness seeded; no MAC/isolation acceptance'}
        def write_record(filename, value):
            p = out / filename
            p.write_text(json.dumps(value, indent=2) + '\n')
            os.chown(p, 1000, 1000)
        write_record('backing-before.json', record)
        mounted = False
        try:
            subprocess.run(['mount', '-t', 'ext4', '-o', 'nosuid,nodev,noatime', loop, str(data)], check=True)
            mounted = True
            subprocess.run(['mount', '--make-private', str(data)], check=True)
            record['mount_observation'] = subprocess.check_output(['findmnt', '-J', '-M', str(data)], text=True)
            write_record('backing-mounted.json', record)
            yield record
        finally:
            # Never detach another execution's device or force-unmount a live consumer.
            assert (kernel / 'loop/backing_file').read_text().strip() == str(image)
            # util-linux reports null back-file for our private node alias.
            # Query the canonical kernel node, verify sysfs and rdev as well.
            mapping = json.loads(subprocess.check_output(['losetup', '-J', '-l', '/dev/loop130'], text=True))['loopdevices']
            assert len(mapping) == 1 and Path(mapping[0]['back-file']).resolve() == image
            if mounted:
                subprocess.run(['umount', str(data)], check=True)
            subprocess.run(['losetup', '-d', loop], check=True)
            assert not os.path.ismount(data)
            assert not subprocess.check_output(['losetup', '-j', str(image)], text=True).strip()
            assert node.stat().st_rdev == os.makedev(major, minor)
            node.unlink()
            if created_loop:
                control = os.open('/dev/loop-control', os.O_RDWR | os.O_CLOEXEC)
                try:
                    fcntl.ioctl(control, 0x4c81, loop_id)
                finally:
                    os.close(control)
            write_record('backing-after.json', {**record, 'unmounted': True, 'loop_detached': True})
    finally:
        os.close(lock)


def verified_verity_backing(checkpoint):
    """Admit only the exact live data loop owned by this execution's host owner."""
    path = Path(checkpoint) / 'backing-mounted.json'
    if not path.exists():
        return None
    record = json.loads(path.read_text())
    before = json.loads((Path(checkpoint) / 'before-launch.json').read_text())
    name = before['userdata_override']['to']
    assert re.fullmatch(r'[a-z0-9][a-z0-9_-]{0,47}', name)
    store = BASE / name
    assert store.resolve() == store and store.stat().st_uid == 0
    metadata = json.loads((store / 'store.json').read_text())
    assert metadata == record['store'] and metadata['name'] == name
    image = store / 'data.ext4'
    assert metadata['backing']['kind'] == 'preallocated-ext4-verity-v1'
    assert metadata['backing']['image'] == str(image)
    st = image.lstat()
    assert stat.S_ISREG(st.st_mode) and st.st_uid == 0
    assert (st.st_dev, st.st_ino) == (record['image_device'], record['image_inode'])
    assert record['loop_id'] == 130 and record['mountpoint'] == str(store / 'data')
    assert Path('/sys/devices/virtual/block/loop130/loop/backing_file').read_text().strip() == str(image)
    assert os.path.ismount(store / 'data')
    return record

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
    backing = metadata.get('backing')
    if backing is not None:
        assert backing['kind'] == 'preallocated-ext4-verity-v1'
        assert os.path.ismount(data), 'Refuse to populate an unmounted image-backed store'
        actual_uuid = subprocess.check_output(['findmnt', '-n', '-o', 'UUID', '-M', str(data)], text=True).strip()
        assert actual_uuid == backing['filesystem_uuid']
    # Keep renames on the same filesystem. Archive only Linux diagnostics,
    # never application data; the private root-only archive is not readiness.
    archive_directory = data / '.archtv-diagnostics' if backing else store / 'diagnostics'
    prior = None
    diagnostic = data / 'local/tmp/archtv-mc1'
    if diagnostic.exists() or diagnostic.is_symlink():
        info = diagnostic.lstat()
        assert stat.S_ISDIR(info.st_mode) and info.st_uid == 2000 and info.st_gid == 1000
        assert stat.S_IMODE(info.st_mode) == 0o750
        archive = archive_directory
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
        archive = archive_directory
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
