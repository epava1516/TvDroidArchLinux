"""Publish the existing existence-only DRM capture request through an owned FD.

The compositor consumes/unlinks this name. Publication is not capture or APK
acceptance. No temporary names, rename/link permissions or policy changes.
"""
import os
import uuid


def publish_capture_request(directory_fd, run_id, uid=1000, gid=1000):
    assert str(uuid.UUID(run_id)) == run_id
    try:
        fd = os.open('capture.request', os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                     os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=directory_fd)
    except (FileExistsError, FileNotFoundError):
        return False  # Already pending, or the owned runtime is closing.
    try:
        # Consumption can happen now. The FD remains valid after unlink; never
        # chown or reopen the disappearing name. The consumer tests existence.
        os.fchown(fd, uid, gid)
        data = (run_id + '\n').encode('ascii')
        assert os.write(fd, data) == len(data)
        return True
    finally:
        os.close(fd)
