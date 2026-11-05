#!/usr/bin/env python3
"""Build the complete original Keystore2 with explicit SOFTWARE boot-key support.

Reuses the pinned Bionic workspace/toolchain. Never changes pristine AOSP sources;
the two adapted workspace files are restored after Cargo, even on build failure.
Compilation/linking do not demonstrate keys, boot revocation or APK compatibility.
"""
import argparse, hashlib, json, os, shutil, subprocess
from pathlib import Path

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('output', type=Path)
args = parser.parse_args()
repo = Path(__file__).resolve().parents[2]
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
cache = Path('/home/tv/.cache/archtv/keystore2-source-build-1')
workspace = cache / 'binder-platform'
inputs = Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs')
patch = repo / 'runtime/aosp/android16-qpr2/patches/keystore2-software-boot-level.patch'
metadata = json.loads(patch.with_suffix('.json').read_text())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(patch) == metadata['patch_sha256']
pristine = inputs / 'security-original-full/source/system/security/keystore2/src'
saved = {}
for name, digest in metadata['pristine_source_sha256'].items():
    path = workspace / 'keystore2/src' / name
    assert sha(pristine / name) == digest and sha(path) == digest, name
    saved[path] = path.read_bytes()
    (out / (name + '.before')).write_bytes(saved[path])
# Preserve the existing SOFTWARE executable and all other workspace adaptations.
old_binary = cache / 'keystore2-linux-software'
old_sha = sha(old_binary)
linker = out / 'link-bionic.py'
s = (cache / 'link-bionic-original.py').read_text()
s = s.replace(str(cache / 'keystore2-native-link.json'), str(out / 'native-link.json'))
linker.write_text(s)
linker.chmod(0o755)
record = {'scope': __doc__, 'previous_software_sha256': old_sha,
          'patch_sha256': sha(patch), 'sources': {}, 'exit': None}
try:
    patch_result = subprocess.run(['patch', '--batch', '--fuzz=0', '-p4',
                                   '-i', str(patch)], cwd=workspace / 'keystore2',
                                  capture_output=True, text=True)
    (out / 'patch.log').write_text(patch_result.stdout + patch_result.stderr)
    assert patch_result.returncode == 0, 'Patch did not apply exactly'
    for path in saved:
        record['sources'][str(path)] = sha(path)
        shutil.copyfile(path, out / path.name)
    env = dict(os.environ, RUSTC=str(workspace / 'rustc-aosp'),
               CARGO_BUILD_JOBS='2', ARCHTV_BINDER_BINDINGS=str(cache / 'bindings-platform.rs'),
               LD_LIBRARY_PATH=':'.join(str(inputs / n) for n in
                                       ['rust188-driver', 'rust188-llvm', 'rust188-host-libcxx']))
    argv = ['cargo', 'build', '--offline', '--target', 'x86_64-linux-android',
            '-p', 'keystore2-service', '--features', 'keystore2/linux_software_keystore',
            '--config', 'target.x86_64-linux-android.linker=' + json.dumps(str(linker))]
    record['argv'] = argv
    with (out / 'build.log').open('w') as log:
        process = subprocess.run(argv, cwd=workspace, env=env, stdout=log, stderr=subprocess.STDOUT)
    record['exit'] = process.returncode
    if process.returncode == 0:
        binary = out / 'keystore2-linux-software-boot'
        shutil.copyfile(workspace / 'target/x86_64-linux-android/debug/keystore2-original', binary)
        record.update(binary=str(binary), binary_sha256=sha(binary))
        assert json.loads((out / 'native-link.json').read_text())['exit'] == 0
finally:
    for path, contents in saved.items():
        path.write_bytes(contents)
    record['workspace_sources_restored'] = all(path.read_bytes() == contents for path, contents in saved.items())
    assert sha(old_binary) == old_sha
    (out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
assert record['exit'] == 0, 'Original complete build failed; see build.log'
print(json.dumps({k: record[k] for k in ['exit', 'binary', 'binary_sha256', 'workspace_sources_restored']}))
