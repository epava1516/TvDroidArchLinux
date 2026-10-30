#!/usr/bin/env python3
"""Run original AOSP Handler dispatch and record success or the actual remaining failure."""
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
args.dex = args.dex.resolve(strict=True)
args.library = args.library.resolve(strict=True)
args.art = args.art.resolve(strict=True)
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
(out/'art-data').mkdir(mode=0o700)
environment = {key: value for key, value in os.environ.items()
               if not key.startswith('ANDROID_') and key not in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'CLASSPATH')}
environment.update(ANDROID_DATA=str(out/'art-data'), ANDROID_LOG_TAGS='*:w')
command = [str(args.art.resolve()/'bin/art'), '--64', '--no-compile', '--', '-Xint', '-cp',
           str(args.dex.resolve()), 'org.archtv.aospprobe.HandlerDispatchProbe', str(args.library.resolve())]
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
(out/'handler.stdout').write_bytes(stdout)
(out/'handler.stderr').write_bytes(stderr)
passed = process.returncode == 0 and stdout.strip() == b'AOSP_HANDLER_DISPATCHED'
result = {'command': command, 'exit_code': process.returncode, 'single_handler_dispatch_pass': passed,
          'full_queue_semantics_pass': False, 'apk_uses_original_framework': False,
          'sha256': {str(path.resolve()): hashlib.sha256(path.read_bytes()).hexdigest()
                     for path in (args.dex, args.library)},
          'scope': 'One Runnable through original Handler.post and Looper.loop. Full ordering, delays, barriers, cancellation, quit semantics, APK integration and stability not proved.'}
(out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({'single_handler_dispatch_pass': passed, 'exit_code': process.returncode}))
if not passed:
    raise SystemExit(1)
