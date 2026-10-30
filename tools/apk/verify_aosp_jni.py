#!/usr/bin/env python3
"""Verify the Linux JNI boundary using original AOSP MessageQueue public FD listeners."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--art', type=Path, required=True)
parser.add_argument('--dex', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
(out/'art-data').mkdir(mode=0o700)
environment = {key: value for key, value in os.environ.items()
               if not key.startswith('ANDROID_') and key not in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'CLASSPATH')}
environment.update(ANDROID_DATA=str(out/'art-data'), ANDROID_LOG_TAGS='*:w')
command = [str(args.art.resolve()/'bin/art'), '--64', '--no-compile', '--', '-Xint', '-cp',
           str(args.dex.resolve()), 'org.archtv.aospprobe.NativeQueueProbe', str(args.library.resolve())]
with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment,
                      cwd=out, start_new_session=True) as process:
    try:
        stdout, stderr = process.communicate(timeout=30)
    except BaseException:
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except ProcessLookupError:
            pass
        process.communicate()
        raise
(out/'jni.stdout').write_bytes(stdout)
(out/'jni.stderr').write_bytes(stderr)
passed = process.returncode == 0 and stdout.strip() == b'AOSP_QUEUE_JNI_OK'
result = {'command': command, 'exit_code': process.returncode, 'native_queue_jni_pass': passed,
          'handler_dispatch_pass': False, 'apk_uses_original_framework': False,
          'sha256': {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in (args.dex, args.library)},
          'scope': 'Original MessageQueue JNI creation, polling, wake across threads, public FD listener on Linux pipe, listener removal and disposal. Not Handler/Looper scheduling, full framework, APK integration or stability proof.'}
(out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'native_queue_jni_pass': passed, 'handler_dispatch_pass': False}))
if not passed:
    raise SystemExit(1)
