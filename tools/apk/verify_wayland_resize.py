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
parser.add_argument('--window-service-build',type=Path)
parser.add_argument('--window-framework',type=Path)
parser.add_argument('--window-bindings',type=Path)
parser.add_argument('--window-system-resources',type=Path)
parser.add_argument('--window-rendernode-build',type=Path)
args = parser.parse_args()
assert all((args.window_service_build,args.window_framework,args.window_bindings,args.window_system_resources)) or not any((args.window_service_build,args.window_framework,args.window_bindings,args.window_system_resources))
assert args.window_rendernode_build is None or args.window_service_build
root = Path(__file__).resolve().parents[2]
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
target = args.target.resolve()
apk = args.apk.resolve() if args.apk else root/'fixtures/apk/counter/golden/counter.apk'
processes = []
logs = []


def start(command, name, env, input_pipe=False):
    log = (out/name).open('wb')
    logs.append(log)
    process = subprocess.Popen(command, stdin=subprocess.PIPE if input_pipe else None, stdout=log, stderr=subprocess.STDOUT, env=env,
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
    if args.window_service_build: env['ARCHTV_APK_ANIMATOR_SCALE']='0.5'
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
    service = None
    service_info = None
    if args.window_service_build:
        wait_for(lambda: 'APK_FRAME 1 960x540' in (out/'compositor.log').read_text(errors='replace'),compositor)
        policy = out/'data/window-policy.properties'
        (out/'window-policy-before.properties').write_bytes(policy.read_bytes())
        values = dict(line.split('=',1) for line in policy.read_text().splitlines())
        owner = int(values['owner_pid'])
        builds = [args.window_framework.resolve(),args.window_bindings.resolve(),args.window_service_build.resolve()]
        proofs = [json.loads((build/'provenance.json').read_text()) for build in builds]
        for build,proof in zip(builds,proofs):
            assert hashlib.sha256((build/'dex/classes.dex').read_bytes()).hexdigest()==proof['dex_sha256']
        assert proofs[2]['framework_dex_sha256']==proofs[0]['dex_sha256']
        assert proofs[2]['bindings_dex_sha256']==proofs[1]['dex_sha256']
        (out/'service-art-data').mkdir(mode=0o700)
        service_env = {key:value for key,value in env.items() if not key.startswith('ANDROID_') and key not in ('LD_LIBRARY_PATH','LD_PRELOAD','CLASSPATH')}
        service_env.update(ANDROID_DATA=str(out/'service-art-data'),ANDROID_LOG_TAGS='*:w')
        system_apk=args.window_system_resources.resolve()/'framework-res.apk'
        system_proof=json.loads((args.window_system_resources/'provenance.json').read_text())
        assert hashlib.sha256(system_apk.read_bytes()).hexdigest()==system_proof['apk_sha256']
        rendernode_options=[]
        rendernode_sha256=None
        if args.window_rendernode_build:
            rendernode_build=args.window_rendernode_build.resolve()
            rendernode_proof=json.loads((rendernode_build/'result.json').read_text())
            rendernode_library=rendernode_build/'libarchtv_rendernode_host.so'
            assert rendernode_proof['build_pass']
            rendernode_sha256=hashlib.sha256(rendernode_library.read_bytes()).hexdigest()
            assert rendernode_sha256==rendernode_proof['library_sha256']
            rendernode_options=['-Darchtv.rendernode.library='+str(rendernode_library)]
        service_command = [str(args.art.resolve()/'bin/art'),'--64','--no-compile','--','-Xint','-Xcheck:jni',*rendernode_options,'-cp',
            ':'.join(str(build/'dex/classes.dex') for build in builds),'org.archtv.apkruntime.WindowServiceProbe',
            str(args.linux_library.resolve()),str(policy),str(args.resources_library.resolve()),str(apk),str(system_apk),str(out/'service-data')]
        service = start(service_command,'window-service.log',service_env,input_pipe=True)
        def service_check(command,marker):
            service.stdin.write((command+'\n').encode());service.stdin.flush()
            wait_for(lambda:marker in (out/'window-service.log').read_text(errors='replace'),service,seconds=20)
        service_check('check 960 540 960 540 0.5','WINDOW_SERVICE_OK 960x540')
        assert 'AOSP_ANIMATION_POLICY_OK scale=0.5 callbacks=3 interpolators=2' in (out/'window-service.log').read_text()
        service_info={'command':service_command,'system_resources_sha256':system_proof['apk_sha256'],'sha256':{str(build/'dex/classes.dex'):proof['dex_sha256'] for build,proof in zip(builds,proofs)}}
        service_info['rendernode_library_sha256']=rendernode_sha256
    def ready():
        text = (out/'compositor.log').read_text(errors='replace')
        return bool(re.search(r'APK_FRAME \d+ 800x450', text))
    wait_for(ready, compositor)
    if service:
        (out/'window-policy-after.properties').write_bytes(policy.read_bytes())
        service_check('check 800 450 960 540 0.5','WINDOW_SERVICE_OK 800x450')
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
    if service:
        compositor.terminate();compositor.wait(timeout=20)
        def provider_dead():
            try:
                stat=Path('/proc/'+str(owner)+'/stat').read_text()
                return stat.rsplit(')',1)[1].split()[0] in ('Z','X')
            except FileNotFoundError:return True
        wait_for(provider_dead,service,seconds=20)
        service_check('dead','WINDOW_SERVICE_DEAD')
        service_check('quit','WINDOW_SERVICE_CLOSED')
        assert service.wait(timeout=15)==0
        service_info['real_wayland_service_pass']=True
        service_info['original_animation_policy_pass']=True
        service_log=(out/'window-service.log').read_text()
        service_info['view_constructed']='VIEW_CONSTRUCTOR_OK' in service_log
        service_info['view_constructor_failures']=[line for line in service_log.splitlines() if line.startswith('VIEW_CONSTRUCTOR_BLOCKED ')]
    result = {'wayland_live_resize_pass':True, 'window_service':service_info, 'initial':[960,540], 'resized':[800,450],
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
