#!/usr/bin/env python3
"""Execute the owned metrics APK: application code must observe resources and callbacks."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
from apk_inventory import dex_inventory

parser = argparse.ArgumentParser()
for name in ('art','runtime-dex','linux-library','resources-library','output'):
    parser.add_argument('--'+name,type=Path,required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
fixture = root/'fixtures/apk/context-metrics'
apk = fixture/'golden/context-metrics.apk'
metadata = json.loads((fixture/'golden/metadata.json').read_text())
assert hashlib.sha256(apk.read_bytes()).hexdigest() == metadata['sha256']
assert not any(name.startswith('Lorg/archtv/metrics/') for name in dex_inventory(args.runtime_dex.read_bytes())[1])
out = args.output.resolve();out.mkdir(parents=True,exist_ok=False)
(out/'art-data').mkdir(mode=0o700)
env = {k:v for k,v in os.environ.items() if not k.startswith('ANDROID_') and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','CLASSPATH')}
env.update(ANDROID_DATA=str(out/'art-data'),ANDROID_LOG_TAGS='*:w')
command = [str(args.art.resolve()/'bin/art'),'--64','--no-compile','--','-Xint','-Xcheck:jni',
 '-Darchtv.linux.library='+str(args.linux_library.resolve()),
 '-Darchtv.resources.library='+str(args.resources_library.resolve()),'-cp',
 str(args.runtime_dex.resolve())+':'+str(apk),'org.archtv.apkruntime.Main',str(apk),metadata['activity'],str(out/'data')]
inputs = 'configure 1920 1080\nconfigure 1080 1920\nquit\n'
with subprocess.Popen(command,stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,start_new_session=True) as process:
    try: stdout,stderr = process.communicate(inputs.encode(),timeout=45)
    except BaseException:
        try: os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError: pass
        process.communicate();raise
(out/'metrics.stdout').write_bytes(stdout);(out/'metrics.stderr').write_bytes(stderr)
assert process.returncode == 0, str(out/'metrics.stderr')
events = [json.loads(line) for line in stdout.splitlines()]
assert [event['event'] for event in events] == ['ready','updated','updated','closed']
for event,(width,height,count) in zip(events[:3],[(1280,720,0),(1920,1080,1),(1080,1920,2)]):
    assert event['display'] == [width,height]
    assert event['root']['class'] == 'android.widget.TextView'
    assert event['root']['text'] == f'Metrics: {width}x{height} callbacks={count}'
    assert f'APK_METRICS Metrics: {width}x{height} callbacks={count} thread=main'.encode() in stderr
assert b'APK_UI_DISPATCH quit thread=main' in stderr
(out/'result.json').write_text(json.dumps({'metrics_apk_pass':True,'command':command,'commands':inputs.splitlines(),
 'apk':metadata,'sha256':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in (args.runtime_dex,args.linux_library,args.resources_library)},
 'scope':'Second owned APK compiled against public SDK only; real Application cast, Context resources, matching configuration/dp/orientation and callbacks on main. No host classes in app or app classes in runtime; no full Activity/View or general APK compatibility claim.'},indent=2)+'\n')
print(out/'result.json')
