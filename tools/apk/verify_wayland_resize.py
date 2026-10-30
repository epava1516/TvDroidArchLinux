#!/usr/bin/env python3
"""Exercise real Wayland configure→ART Resources→SHM resize using the existing winit test hook."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import tempfile
import time

parser = argparse.ArgumentParser()
for name in ('target', 'runtime-dex', 'linux-library', 'resources-library', 'output'):
    parser.add_argument('--'+name, type=Path, required=True)
parser.add_argument('--apk', type=Path)
parser.add_argument('--activity', default='org.archtv.probe.MainActivity')
parser.add_argument('--text-before', default='Contador: 0')
parser.add_argument('--text-after', default='Contador: 0')
parser.add_argument('--art', type=Path, default=Path.home()/'.cache/archtv/art-host/host/art-13.0.0')
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
target = args.target.resolve()
apk = args.apk.resolve() if args.apk else root/'fixtures/apk/counter/golden/counter.apk'
processes = []
logs = []


def start(command, name, env):
    log = (out/name).open('wb')
    logs.append(log)
    process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, env=env,
                               start_new_session=True, cwd=root)
    processes.append(process)
    return process


def wait_for(predicate, process, seconds=45):
    deadline = time.monotonic()+seconds
    while time.monotonic() < deadline:
        if predicate(): return
        if process.poll() is not None: raise RuntimeError('Process exited before resize proof')
        time.sleep(0.1)
    raise RuntimeError('Timed out waiting for Wayland resize proof')


runtime_directory = tempfile.TemporaryDirectory(prefix='archtv-apk-resize-', dir='/tmp')
try:
    runtime = runtime_directory.name
    os.chmod(runtime, 0o700)
    env = dict(os.environ, XDG_RUNTIME_DIR=runtime, LIBGL_ALWAYS_SOFTWARE='1',
               GALLIUM_DRIVER='llvmpipe', EGL_PLATFORM='wayland',
               ARCHTV_APK_LINUX_LIBRARY=str(args.linux_library.resolve()),
               ARCHTV_APK_RESOURCES_LIBRARY=str(args.resources_library.resolve()))
    env.pop('DISPLAY', None)
    env.pop('WAYLAND_SOCKET', None)
    weston = start(['setpriv', '--inh-caps=-all', '--ambient-caps=-all', 'weston',
        '--backend=headless', '--renderer=pixman', '--fake-seat', '--width=1280', '--height=720',
        '--socket=archtv-host', '--no-config', '--idle-time=0', '--log='+str(out/'weston.log')],
        'weston.stderr', env)
    wait_for(lambda: (Path(runtime)/'archtv-host').is_socket(), weston)
    env.update(WAYLAND_DISPLAY='archtv-host', RUST_LOG='archtv_compositor=debug,smithay=warn')
    command = ['setpriv', '--inh-caps=-all', '--ambient-caps=-all', str(target/'debug/archtv-compositor'),
        '--winit', '--mode', '960x540', '--test-resize', '8', '800x450', '--exit-after', '45', '--',
        str(target/'debug/archtv-apk-host'), str(args.art.resolve()),
        str(args.runtime_dex.resolve()), str(apk),
        args.activity, str(out/'data'), str(out/'art.stderr'), str(out/'frames')]
    compositor = start(command, 'compositor.log', env)
    def ready():
        text = (out/'compositor.log').read_text(errors='replace')
        return bool(re.search(r'APK_FRAME \d+ 800x450', text))
    wait_for(ready, compositor)
    text = (out/'compositor.log').read_text()
    initial = text.index('APK_FRAME 1 960x540')
    resized = text.index('APK_DISPLAY 800x450')
    assert initial < resized
    assert text.count('APK_DISPLAY 960x540') == 1
    assert text.count('APK_DISPLAY 800x450') >= 1
    trace = (out/'art.stderr').read_text()
    assert 'APK_UI_DISPATCH configure 800 450 thread=main' in trace
    assert 'APK_VIEW updated' in text
    assert 'text: Some("'+args.text_before+'")' in text[:initial]
    assert 'text: Some("'+args.text_after+'")' in text[initial:]
    dimensions = []
    for image in sorted((out/'frames').glob('*.png')):
        info = json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries',
            'stream=width,height','-of','json',str(image)], text=True, timeout=15))['streams'][0]
        dimensions.append([info['width'], info['height']])
    assert [960,540] in dimensions and dimensions[-1] == [800,450]
    result = {'wayland_live_resize_pass':True, 'initial':[960,540], 'resized':[800,450],
        'frame_sizes':dimensions, 'command':command,
        'app_text_before':args.text_before,'app_text_after':args.text_after,
        'scope':'Real nested Wayland resize after the first frame, original Resources on the main Handler, and client SHM dimensions. No physical mode switch, HiDPI, Activity recreation or native scanout resize claim.',
        'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
            (apk,args.runtime_dex,args.linux_library,args.resources_library,target/'debug/archtv-apk-host',target/'debug/archtv-compositor')}}
    (out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
finally:
    # Compositor SIGTERM runs its supervisor cleanup, including the child's private group.
    for process in reversed(processes):
        if process.poll() is None:
            process.terminate()
            try: process.wait(timeout=15)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid, signal.SIGKILL)
                process.wait()
    for log in logs: log.close()
    runtime_directory.cleanup()
print(out/'result.json')
