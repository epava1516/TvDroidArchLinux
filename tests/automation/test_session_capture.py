"""Real filesystem race/ownership regressions, not APK or MAC acceptance."""
from pathlib import Path
import importlib.util
import os
import tempfile
import unittest
from unittest.mock import patch

SOURCE = Path(__file__).resolve().parents[2] / 'reports/android16-package-bootstrap/session_capture.py'
spec = importlib.util.spec_from_file_location('session_capture', SOURCE)
capture = importlib.util.module_from_spec(spec)
spec.loader.exec_module(capture)
RUN = '0e246f63-41e1-4142-8684-49a25169a3df'


class CaptureRequestTest(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.directory = Path(self.temporary.name)
        self.fd = os.open(self.directory, os.O_RDONLY | os.O_DIRECTORY)

    def tearDown(self):
        os.close(self.fd)
        self.temporary.cleanup()

    def publish(self):
        return capture.publish_capture_request(self.fd, RUN, os.getuid(), os.getgid())

    def test_consumed_between_create_and_ownership_keeps_valid_fd(self):
        real_fchown = os.fchown
        observed = []

        def consume_then_chown(fd, uid, gid):
            target = self.directory / 'capture.request'
            target.unlink()  # Actual compositor interleaving from run299.
            with self.assertRaises(FileNotFoundError):
                os.chown(target, uid, gid)  # The former path-based operation.
            real_fchown(fd, uid, gid)
            observed.append(os.fstat(fd).st_nlink)

        with patch.object(capture.os, 'fchown', consume_then_chown):
            self.assertTrue(self.publish())
        self.assertEqual(observed, [0])
        self.assertFalse((self.directory / 'capture.request').exists())

    def test_pending_request_is_not_truncated_or_reowned(self):
        self.assertTrue(self.publish())
        target = self.directory / 'capture.request'
        before = target.stat()
        self.assertFalse(self.publish())
        after = target.stat()
        self.assertEqual(target.read_text(), RUN + '\n')
        self.assertEqual((before.st_ino, before.st_uid, before.st_gid),
                         (after.st_ino, after.st_uid, after.st_gid))

    def test_symlink_cannot_redirect_privileged_publication(self):
        victim = self.directory / 'victim'
        victim.write_text('preserve')
        before = victim.stat()
        (self.directory / 'capture.request').symlink_to(victim)
        self.assertFalse(self.publish())
        self.assertEqual(victim.read_text(), 'preserve')
        self.assertEqual((before.st_ino, before.st_uid, before.st_gid),
                         (victim.stat().st_ino, victim.stat().st_uid, victim.stat().st_gid))


if __name__ == '__main__':
    unittest.main()
