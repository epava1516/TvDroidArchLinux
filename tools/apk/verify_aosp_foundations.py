#!/usr/bin/env python3
"""Verify selected original AOSP framework behavior on ART and the Linux adapter."""
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
parser.add_argument('--queue-repeats', type=int, default=1)
args = parser.parse_args()
if not 1 <= args.queue_repeats <= 20:
    parser.error('--queue-repeats must be between 1 and 20')
args.art = args.art.resolve(strict=True)
args.dex = args.dex.resolve(strict=True)
args.library = args.library.resolve(strict=True)
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
(out/'art-data').mkdir(mode=0o700)
environment = {key: value for key, value in os.environ.items()
               if not key.startswith('ANDROID_') and key not in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'CLASSPATH')}
environment.update(ANDROID_DATA=str(out/'art-data'), ANDROID_LOG_TAGS='*:w')
environment['ARCHTV_ANDROID_PROPERTY_archtv.queue.test'] = '42'
environment['ARCHTV_ANDROID_PROPERTY_archtv.queue.malformed'] = 'bad'
environment.pop('ARCHTV_ANDROID_PROPERTY_archtv.queue.absent', None)
results = {}
probes = [('ClockNativeProbe', b'AOSP_CLOCK_JNI_OK'), ('LocalContextProbe', b'AOSP_LOCAL_CONTEXT_OK'),
          ('HandlerDispatchProbe', b'AOSP_HANDLER_DISPATCHED'), ('QueueSemanticsProbe', b'AOSP_QUEUE_SEMANTICS_OK'),
          ('NativeQueueProbe', b'AOSP_QUEUE_JNI_OK')]
probes += [('QueueSemanticsProbe-'+str(index), b'AOSP_QUEUE_SEMANTICS_OK') for index in range(1, args.queue_repeats)]
for probe, marker in probes:
    class_name = probe.split('-')[0]
    command = [str(args.art/'bin/art'), '--64', '--no-compile', '--', '-Xint', '-cp', str(args.dex),
               'org.archtv.aospprobe.'+class_name, str(args.library)]
    with subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=environment,
                          cwd=out, start_new_session=True) as process:
        try:
            stdout, stderr = process.communicate(timeout=45)
            timed_out = False
        except subprocess.TimeoutExpired:
            os.killpg(process.pid, signal.SIGKILL)
            stdout, stderr = process.communicate()
            timed_out = True
        except BaseException:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.communicate()
            raise
    (out/(probe+'.stdout')).write_bytes(stdout)
    (out/(probe+'.stderr')).write_bytes(stderr)
    passed = process.returncode == 0 and stdout.splitlines()[-1:] == [marker] and not timed_out
    results[probe] = {'command': command, 'exit_code': process.returncode, 'pass': passed, 'timed_out': timed_out}
result = {'probes': results, 'selected_foundations_pass': all(item['pass'] for item in results.values()),
          'apk_uses_original_framework': False, 'binder_ipc_pass': False,
          'sha256': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in (args.dex, args.library)},
          'scope': 'Selected clock, local identity, read-only host property, original Handler/Looper scheduling and native FD tests. Not all framework APIs, Binder IPC/global property service, APK integration, performance or prolonged stability.'}
(out/'result.json').write_text(json.dumps(result, indent=2)+'\n')
print(json.dumps({name: item['pass'] for name, item in results.items()}))
if not result['selected_foundations_pass']:
    raise SystemExit(1)
