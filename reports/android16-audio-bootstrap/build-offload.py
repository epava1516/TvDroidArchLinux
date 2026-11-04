#!/usr/bin/env python3
"""Build the whole original Rust LE Audio dependency with its original Binder API.

Reuses the previously verified original Binder Cargo adapter and pinned offline
AOSP crates. This produces build inputs, never Bluetooth/service acceptance.
"""
from pathlib import Path
import hashlib
import json
import os
import shutil
import subprocess
import sys

repo = Path(__file__).resolve().parents[2]
out = (repo / sys.argv[1]).resolve()
out.mkdir()
study = Path('/home/tv/.cache/archtv/aosp16-qpr2/audio-original-study-1')
source = study / 'bluetooth-offload/leaudio'
inputs = Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs')
previous = Path('/home/tv/.cache/archtv/keystore2-source-build-1')
binder = previous / 'binder-platform'
original_binder = inputs / 'binder-rust-original/source/frameworks/native/libs/binder/rust'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
# Reuse the original implementation, not the stripped image's metadata-less .so.
for src in (original_binder / 'src').rglob('*.rs'):
    assert sha(src) == sha(binder / 'binder' / src.relative_to(original_binder))
assert sha(original_binder / 'sys/lib.rs') == sha(binder / 'binder-sys/lib.rs')
record = {'scope': 'Whole original LE Audio Rust static library compilation; no runtime acceptance',
          'source_acquisition': json.loads((study / 'bluetooth-offload.acquisition.json').read_text()),
          'commands': [], 'source_sha256': {str(p): sha(p) for p in (source / 'audio').glob('*.rs')},
          'binder_adapter': json.loads((binder / 'adapter-platform.json').read_text())}
env = dict(os.environ, RUSTC=str(binder / 'rustc-aosp'), CARGO_BUILD_JOBS='2',
           ARCHTV_BINDER_BINDINGS=str(previous / 'bindings-platform.rs'),
           LD_LIBRARY_PATH=':'.join(str(inputs / n) for n in
                                    ['rust188-driver', 'rust188-llvm', 'rust188-host-libcxx']))

def run(args, name, cwd=repo):
    args = list(map(str, args))
    result = subprocess.run(args, cwd=cwd, env=env, capture_output=True, timeout=300)
    log = out / (name + '.log')
    log.write_bytes(result.stdout + result.stderr)
    record['commands'].append({'argv': args, 'exit': result.returncode, 'log': str(log)})
    (out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
    print(name, result.returncode, flush=True)
    if result.returncode:
        print(result.stderr.decode(errors='replace')[-2500:])
        raise SystemExit(result.returncode)

api = out / 'api'
api.mkdir()
run([repo / 'dist/aosp16/aidl-host-build-4/aidl', '--lang=rust', '--structured',
     '--out=' + str(api / 'generated'), '-I' + str(source / 'aidl'),
     *sorted((source / 'aidl').rglob('*.aidl'))], 'aidl')
run(['python', inputs / 'aidl-rust-original/source/system/tools/aidl/build/aidl_rust_glue.py',
     api / 'lib.rs', api / 'generated', *sorted((api / 'generated').rglob('*.rs'))], 'glue')
(api / 'Cargo.toml').write_text(
    '[package]\nname="android_hardware_bluetooth_offload_leaudio"\nversion="0.1.0"\nedition="2021"\n'
    '[lib]\npath="lib.rs"\n[dependencies]\nbinder={path="' + str(binder / 'binder') +
    '"}\nasync-trait="=0.1.89"\n')
(out / 'Cargo.toml').write_text(
    '[workspace]\nmembers=["api"]\n[package]\nname="bluetooth_offload_leaudio_audio"\n'
    'version="0.1.0"\nedition="2021"\n[lib]\npath="' + str(source / 'audio/lib.rs') +
    '"\ncrate-type=["staticlib"]\n[features]\ndefault=["lc3","opus"]\nlc3=[]\nopus=[]\n'
    '[dependencies]\nandroid_hardware_bluetooth_offload_leaudio={path="api"}\nbinder={path="' +
    str(binder / 'binder') + '"}\nlibc={version="=0.2.172",features=["extra_traits"]}\n'
    'log="=0.4.27"\n[profile.dev]\npanic="abort"\n')
(out / '.cargo').mkdir()
shutil.copyfile(binder / '.cargo/config.toml', out / '.cargo/config.toml')
run(['cargo', 'build', '--offline', '--target', 'x86_64-linux-android',
     '-p', 'bluetooth_offload_leaudio_audio'], 'cargo', out)
archive = out / 'target/x86_64-linux-android/debug/libbluetooth_offload_leaudio_audio.a'
record['exit'] = 0
record['archive'] = {'path': str(archive), 'sha256': sha(archive)}
record['cargo_lock_sha256'] = sha(out / 'Cargo.lock')
(out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
