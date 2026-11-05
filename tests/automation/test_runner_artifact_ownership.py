"""Exercise the runner's actual ownership loop without starting a runtime."""
import ast
import os
from pathlib import Path
import tempfile
import unittest


class ArtifactOwnership(unittest.TestCase):
    @unittest.skipUnless(os.geteuid() in (0, 1000), "runner transfers artifacts to UID/GID1000")
    def test_ephemeral_capture_and_foreign_target(self):
        source = Path(__file__).resolve().parents[2] / "reports/android16-apex-bootstrap/run.py"
        tree = ast.parse(source.read_text())
        loops = [node for node in ast.walk(tree) if isinstance(node, ast.For)
                 and ast.unparse(node.iter) == "recovery.iterdir()"]
        self.assertEqual(len(loops), 1)
        code = compile(ast.Module(body=loops, type_ignores=[]), str(source), "exec")
        with tempfile.TemporaryDirectory() as directory:
            base = Path(directory)
            recovery = base / "checkpoint"
            recovery.mkdir()
            target = base / "outside-checkpoint"
            target.write_text("test-only")
            before = target.stat()
            (recovery / "screen.ppm").symlink_to(target)
            (recovery / "capture.request").symlink_to(base / "consumed-request")
            (recovery / "result.json").write_text("test-only")
            exec(code, {"os": os, "recovery": recovery})
            after = target.stat()
            self.assertEqual((before.st_uid, before.st_gid), (after.st_uid, after.st_gid))
            self.assertEqual(target.read_text(), "test-only")
            for path in recovery.iterdir():
                self.assertEqual((path.lstat().st_uid, path.lstat().st_gid), (1000, 1000))


if __name__ == "__main__":
    unittest.main()
