#!/usr/bin/env python3
"""Observe the original AOSP queue's first native boundary on host ART."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
from apk_inventory import dex_inventory

parser = argparse.ArgumentParser()
parser.add_argument('--art', type=Path, required=True)
parser.add_argument('--dex', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
dex = args.dex.resolve()
definitions = sorted(dex_inventory(dex.read_bytes())[1])
if any(not name.startswith(('Landroid/os/', 'Lorg/archtv/aospprobe/')) for name in definitions):
    raise SystemExit('Unexpected class in queue runtime DEX')
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
(out/'art-data').mkdir(mode=0o700)
environment = {key: value for key, value in os.environ.items()
               if not key.startswith('ANDROID_') and key not in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'CLASSPATH')}
environment.update(ANDROID_DATA=str(out/'art-data'), ANDROID_LOG_TAGS='*:w')
command = [str(args.art.resolve()/'bin/art'), '--64', '--no-compile', '--', '-Xint',
           '-cp', str(dex), 'org.archtv.aospprobe.QueueLinkProbe']
with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                      env=environment, cwd=out, start_new_session=True) as process:
    try:
        stdout, stderr = process.communicate(timeout=60)
    except BaseException:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise
(out/'link.stdout').write_bytes(stdout)
(out/'link.stderr').write_bytes(stderr)
fd_pass = b'ART_FD_GETINT=int' in stdout
boundary = (process.returncode != 0 and b'java.lang.UnsatisfiedLinkError' in stderr
            and b'android.os.MessageQueue.nativeInit()' in stderr)
result = {'command': command, 'exit_code': process.returncode,
          'art_private_fd_api_verified': fd_pass, 'original_queue_native_boundary_observed': boundary,
          'queue_functional_pass': False, 'dex_sha256': hashlib.sha256(dex.read_bytes()).hexdigest(),
          'dex_defined_classes': definitions,
          'scope': 'Original Looper.prepare reaches original MessageQueue constructor and missing nativeInit on ART. No functional queue, JNI port, full dependency closure or APK compatibility proof.'}
(out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({key: result[key] for key in
                  ('art_private_fd_api_verified', 'original_queue_native_boundary_observed', 'queue_functional_pass')}))
if not fd_pass or not boundary:
    raise SystemExit(1)
