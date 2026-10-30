#!/usr/bin/env python3
"""Execute the original counter DEX on host ART and test its API subset."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import selectors
import stat
import subprocess
import zipfile
from apk_inventory import dex_inventory

parser = argparse.ArgumentParser()
parser.add_argument('--art', type=Path, required=True)
parser.add_argument('--runtime-dex', type=Path, required=True)
parser.add_argument('--linux-library', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
apk = root/'fixtures/apk/counter/golden/counter.apk'
dex = args.runtime_dex.resolve()
library = args.linux_library.resolve(strict=True)
assert not any(name.startswith('Lorg/archtv/probe/') for name in dex_inventory(dex.read_bytes())[1])
art = args.art.resolve()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
(out/'art-data').mkdir(mode=0o700)
environment = {key: value for key, value in os.environ.items()
               if not key.startswith('ANDROID_') and key not in ('LD_PRELOAD', 'LD_LIBRARY_PATH', 'CLASSPATH')}
environment.update(ANDROID_DATA=str(out/'art-data'), ANDROID_LOG_TAGS='*:w')
original_hash = hashlib.sha256(apk.read_bytes()).hexdigest()
if original_hash != 'f07c9b92ab3353237276081c22e11ce06168b8c9f71a99ea32968b2ce0f00e28':
    raise SystemExit('Original fixture checksum mismatch')
results = {}


def kill_group(process):
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except ProcessLookupError:
        pass
    process.communicate()


def execute(name, artifact, data, commands, expected_exit):
    command = [str(art/'bin/art'), '--64', '--no-compile', '--', '-Xint', '-Darchtv.linux.library='+str(library), '-cp',
               str(dex)+':'+str(artifact), 'org.archtv.apkruntime.Main', str(artifact),
               'org.archtv.probe.MainActivity', str(data)]
    with subprocess.Popen(command, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                          env=environment, cwd=out, start_new_session=True) as process:
        try:
            stdout, stderr = process.communicate(commands.encode(), timeout=60)
        except BaseException:
            kill_group(process)
            raise
    (out/(name+'.stdout')).write_bytes(stdout)
    (out/(name+'.stderr')).write_bytes(stderr)
    results[name] = {'exit_code': process.returncode, 'command': command}
    if process.returncode != expected_exit:
        raise AssertionError(name+' unexpected exit; see '+str(out/(name+'.stderr')))
    if expected_exit == 0:
        actions = commands.splitlines()
        if not actions or actions[-1] != 'quit':
            actions.append('quit')  # EOF is an ordered close request.
        expected = ['APK_UI_DISPATCH '+action+' thread=main' for action in ['create', *actions]]
        observed = [line for line in stderr.decode().splitlines() if line.startswith('APK_UI_DISPATCH ')]
        assert observed == expected, (name, observed, expected)
    return [json.loads(line) for line in stdout.splitlines()], stderr


def check_tree(event, prefix, count):
    tree = event['root']
    assert tree['class'] == 'android.widget.LinearLayout' and tree['orientation'] == 1
    assert tree['padding'] == [24, 24, 24, 24]
    assert len(tree['children']) == 2
    label, button = tree['children']
    assert label['class'] == 'android.widget.TextView' and label['text'] == prefix+' '+str(count)
    assert label['text_size'] == 28
    assert button['class'] == 'android.widget.Button' and button['text'] == 'Incrementar' and button['focused']


data = out/'app-data'
events, _ = execute('first-process', apk, data, 'activate\nactivate\nquit\n', 0)
assert [event['event'] for event in events] == ['ready', 'updated', 'updated', 'closed']
for event, count in zip(events, (0, 1, 2)):
    check_tree(event, 'Contador:', count)
events, _ = execute('second-process', apk, data, 'activate\nquit\n', 0)
assert [event['event'] for event in events] == ['ready', 'updated', 'closed']
check_tree(events[0], 'Contador:', 2)
check_tree(events[1], 'Contador:', 3)
assert stat.S_IMODE(data.stat().st_mode) == 0o700
assert stat.S_IMODE((data/'counter.properties').stat().st_mode) == 0o600

# A live owner must exclude a second process, then release its data lock on close.
with (out/'lock-owner.stderr').open('wb') as error_log:
    with subprocess.Popen(results['first-process']['command'], stdin=subprocess.PIPE,
                          stdout=subprocess.PIPE, stderr=error_log, env=environment,
                          cwd=out, start_new_session=True) as owner:
        try:
            with selectors.DefaultSelector() as selector:
                selector.register(owner.stdout, selectors.EVENT_READ)
                if not selector.select(60):
                    raise TimeoutError('Lock owner did not become ready')
            ready = owner.stdout.readline()
            check_tree(json.loads(ready), 'Contador:', 3)
            events, stderr = execute('lock-contender', apk, data, 'quit\n', 1)
            assert not events and b'App data already in use' in stderr
            remaining, _ = owner.communicate(b'quit\n', timeout=60)
            assert owner.returncode == 0 and json.loads(remaining) == {'event': 'closed'}
            (out/'lock-owner.stdout').write_bytes(ready+remaining)
        except BaseException:
            kill_group(owner)
            raise
events, _ = execute('after-lock-release', apk, data, 'quit\n', 0)
check_tree(events[0], 'Contador:', 3)
assert events[-1] == {'event': 'closed'}

# More commands than the 16-slot ingress queue must be processed exactly once.
events, _ = execute('bounded-burst', apk, out/'burst-data', 'activate\n'*64+'quit\n', 0)
assert len(events) == 66 and events[-1] == {'event': 'closed'}
for index, event in enumerate(events[:-1]):
    check_tree(event, 'Contador:', index)
events, _ = execute('eof-close', apk, out/'eof-data', 'activate\n', 0)
check_tree(events[1], 'Contador:', 1)
assert events[-1] == {'event': 'closed'}
events, stderr = execute('invalid-command', apk, out/'invalid-data', 'invalid\n', 1)
assert len(events) == 1 and events[0]['event'] == 'ready'
assert b'Unknown command: invalid' in stderr and b'APK_UI_DISPATCH destroy-after-failure thread=main' in stderr
assert b'android.os.Handler.dispatchMessage' in stderr and b'android.os.Looper.loop' in stderr
events, _ = execute('after-invalid-command', apk, out/'invalid-data', 'quit\n', 0)
check_tree(events[0], 'Contador:', 0)

# Same app DEX, changed unsigned resource table: proves text comes from the APK.
with zipfile.ZipFile(apk) as archive:
    content = {entry.filename: archive.read(entry) for entry in archive.infolist()
               if not entry.filename.startswith('META-INF/')}
assert content['resources.arsc'].count(b'Contador:') == 1
changed = dict(content)
changed['resources.arsc'] = content['resources.arsc'].replace(b'Contador:', b'Registro:')
variant = out/'resource-variant-unsigned.apk'
with zipfile.ZipFile(variant, 'w') as archive:
    for name, payload in changed.items():
        archive.writestr(name, payload)
with zipfile.ZipFile(variant) as archive:
    assert archive.read('classes.dex') == content['classes.dex']
events, _ = execute('resource-variant', variant, out/'variant-data', 'activate\nquit\n', 0)
check_tree(events[0], 'Registro:', 0)
check_tree(events[1], 'Registro:', 1)
assert events[-1] == {'event': 'closed'}

malformed = out/'truncated-resources-unsigned.apk'
with zipfile.ZipFile(malformed, 'w') as archive:
    for name, payload in content.items():
        archive.writestr(name, payload[:20] if name == 'resources.arsc' else payload)
events, stderr = execute('truncated-resources', malformed, out/'malformed-data', 'quit\n', 1)
assert not events and b'Unsupported or invalid APK resources' in stderr

(data/'counter.properties').write_text('count=invalid\n')
events, stderr = execute('corrupt-preferences', apk, data, 'quit\n', 1)
assert not events and b'Cannot read preferences' in stderr
assert (data/'counter.properties').read_text() == 'count=invalid\n'
assert hashlib.sha256(apk.read_bytes()).hexdigest() == original_hash
results.update(original_apk_sha256=original_hash, runtime_dex_sha256=hashlib.sha256(dex.read_bytes()).hexdigest(),
               linux_library_sha256=hashlib.sha256(library.read_bytes()).hexdigest(),
               headless_counter_pass=True, original_ui_looper_pass=True, wayland_pass=False,
               scope='Original APK DEX lifecycle, listener, resources and integer persistence. Separate unsigned resource variant and malformed inputs. No Wayland UI, signature enforcement, isolation, full Android API or stable general APK support.')
(out/'result.json').write_text(json.dumps(results, indent=2)+'\n')
print(json.dumps({'headless_counter_pass': True, 'wayland_pass': False, 'output': str(out)}))
