"""Regression tests for prerequisite reporting, never runtime compatibility tests."""
import gzip
import importlib.util
import mmap
from pathlib import Path
import struct
import tempfile
import unittest

spec = importlib.util.spec_from_file_location('host_security', Path(__file__).with_name('check_host_security.py'))
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HostSecurityReporting(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.root = Path(self.directory.name)

    def put(self, path, value):
        target = self.root / path
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(value if isinstance(value, bytes) else value.encode())

    def snapshot(self, enforcing=1, sequence=2, loads=1):
        self.put('sys/kernel/security/lsm', 'capability,selinux,bpf')
        self.put('sys/fs/selinux/enforce', str(enforcing))
        self.put('sys/fs/selinux/policyvers', '33')
        self.put('sys/fs/selinux/status', struct.pack('=5I', 1, sequence, enforcing, loads, 1)
                 + bytes(mmap.PAGESIZE - 20))
        for name, permissions in module.REQUIRED_PERMISSIONS.items():
            for number, permission in enumerate(permissions, 1):
                self.put(f'sys/fs/selinux/class/{name}/perms/{permission}', str(number))

    def test_compiled_library_or_missing_interfaces_cannot_pass(self):
        self.put('proc/config.gz', gzip.compress(b'CONFIG_SECURITY_SELINUX=y\n'))
        result = module.inspect(self.root)
        self.assertEqual(result['observations']['optional_build_config']['CONFIG_SECURITY_SELINUX'], 'y')
        self.assertFalse(result['kernel_prerequisites_passed'])
        self.assertEqual(result['observations']['status']['state'], 'absent')

    def test_offline_complete_snapshot_never_claims_runtime_or_live_host(self):
        self.snapshot()
        result = module.inspect(self.root)
        self.assertTrue(result['observed_checks_passed'])
        self.assertFalse(result['kernel_prerequisites_passed'])
        self.assertEqual(result['observation_mode'], 'offline_snapshot')
        self.assertFalse(result['runtime_ready'])
        self.assertFalse(result['policy_semantics_verified'])

    def test_permissive_is_not_enforcement(self):
        self.snapshot(enforcing=0)
        self.assertFalse(module.inspect(self.root)['kernel_prerequisites_passed'])

    def test_odd_sequence_is_unknown_not_accepted_as_status(self):
        self.snapshot(sequence=3)
        result = module.inspect(self.root)
        self.assertEqual(result['observations']['status']['state'], 'unknown')
        self.assertFalse(result['kernel_prerequisites_passed'])

    def test_policy_not_loaded_cannot_pass(self):
        self.snapshot(loads=0)
        self.assertFalse(module.inspect(self.root)['kernel_prerequisites_passed'])

    def test_missing_android_userspace_class_is_explicit(self):
        self.snapshot()
        (self.root / 'sys/fs/selinux/class/service_manager/perms/find').unlink()
        result = module.inspect(self.root)
        self.assertFalse(result['checks']['required_class_permissions_exposed'])

    def test_unreadable_interface_is_unknown_not_absent(self):
        self.snapshot()
        target = self.root / 'sys/fs/selinux/class/binder/perms/call'
        target.unlink()
        target.mkdir()
        result = module.inspect(self.root)
        self.assertEqual(result['observations']['classes']['binder']['call']['state'], 'unknown')
        self.assertFalse(result['kernel_prerequisites_passed'])

    def test_empty_regular_status_is_unknown_and_not_native_dereferenced(self):
        self.snapshot()
        self.put('sys/fs/selinux/status', b'')
        result = module.inspect(self.root)
        self.assertEqual(result['observations']['status']['state'], 'unknown')
        self.assertFalse(result['kernel_prerequisites_passed'])

    def test_malformed_status_is_unknown(self):
        self.snapshot()
        self.put('sys/fs/selinux/status', b'truncated')
        self.assertEqual(module.inspect(self.root)['observations']['status']['state'], 'unknown')


if __name__ == '__main__':
    unittest.main()
