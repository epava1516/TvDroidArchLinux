#!/usr/bin/env python3
"""Exercise the original ServiceManager cache with a real local endpoint lifecycle."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
from apk_inventory import dex_inventory

parser = argparse.ArgumentParser()
for name in ('aosp-build', 'tools', 'art', 'linux-library', 'output'):
    parser.add_argument('--'+name, type=Path, required=True)
parser.add_argument('--window-bindings',type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
(out/'classes').mkdir(); (out/'dex').mkdir(); (out/'art-data').mkdir(mode=0o700)
proof = json.loads((args.aosp_build/'provenance.json').read_text())
dex = args.aosp_build.resolve()/'dex/classes.dex'
assert hashlib.sha256(dex.read_bytes()).hexdigest() == proof['dex_sha256']
assert hashlib.sha256((args.aosp_build/'framework.jar').read_bytes()).hexdigest() == proof['framework_jar_sha256']
assert 'android/os/ServiceManager.class' in proof['runtime_classes']
assert 'android/os/IInterface.class' in proof['runtime_classes']
assert proof['original_sources_modified'] is False
manifest=json.loads((root/'runtime/aosp/framework-study.json').read_text())
for source_path in ('core/java/android/os/ServiceManager.java','core/java/android/os/IInterface.java','core/java/com/android/internal/util/StatLogger.java'):
    expected=next(item['sha256'] for item in manifest['files'] if item['path']==source_path)
    assert any(name.endswith('/'+source_path) and digest==expected for name,digest in proof['original_sources_sha256'].items())
source = root/'fixtures/aosp-services/ServiceCacheProbe.java'
adapter = root/'runtime/aosp/linux-services/org/archtv/aosplinux/LocalServiceBinder.java'
sources = [source,adapter]
jdk = Path('/usr/lib/jvm/java-17-openjdk/bin')
reference = Path.home()/'.cache/archtv/aosp-compile-tools/android-all-13.jar'
assert hashlib.sha256(reference.read_bytes()).hexdigest() == json.loads((root/'runtime/aosp/compile-reference.json').read_text())['sha256']
toolchain = json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())
r8 = args.tools.resolve()/'r8.jar'
for name in ('r8.jar', 'android.jar'):
    assert hashlib.sha256((args.tools/name).read_bytes()).hexdigest() == next(item['sha256'] for item in toolchain['artifacts'] if item['file']==name)
commands = [
 [str(jdk/'javac'), '--release','8','-classpath',':'.join(map(str,[args.aosp_build.resolve()/'framework.jar',reference])), '-d',str(out/'classes'),*map(str,sources)],
 [str(jdk/'jar'),'cf',str(out/'probe.jar'),'-C',str(out/'classes'),'.'],
 [str(jdk/'java'),'-cp',str(r8),'com.android.tools.r8.D8','--release','--min-api','28','--lib',str(args.tools.resolve()/'android.jar'),'--output',str(out/'dex'),str(out/'probe.jar')]]
for index, command in enumerate(commands):
    with (out/('build-'+str(index)+'.log')).open('wb') as log:
        subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT,timeout=120)
definitions = dex_inventory((out/'dex/classes.dex').read_bytes())[1]
assert not any(name.startswith('Landroid/') for name in definitions)
command = [str(args.art.resolve()/'bin/art'),'--64','--no-compile','--','-Xint','-Xcheck:jni','-cp',
 ':'.join(map(str,[dex,out/'dex/classes.dex'])),'org.archtv.aospprobe.ServiceCacheProbe',str(args.linux_library.resolve())]
window_contract=None
if args.window_bindings:
    binding=args.window_bindings.resolve()
    window_proof=json.loads((binding/'provenance.json').read_text())
    assert hashlib.sha256((binding/'bindings.jar').read_bytes()).hexdigest()==window_proof['bindings_jar_sha256']
    assert hashlib.sha256((binding/'dex/classes.dex').read_bytes()).hexdigest()==window_proof['dex_sha256']
    assert window_proof['original_aidl_inputs']==json.loads((root/'runtime/aosp/window-aidl-sources.json').read_text())
    assert window_proof['toolchain']==json.loads((root/'runtime/aosp/aidl-toolchain.json').read_text())
    assert window_proof['reference_methods_equal'] and window_proof['reference_transaction_ids_equal']
    assert window_proof['compile_reference']==proof['compile_reference']
    command[command.index('-cp')+1]+=':'+str(binding/'dex/classes.dex')
    command.append('window-contract')
    window_contract={'bindings_dex_sha256':window_proof['dex_sha256'],
        'provenance_sha256':hashlib.sha256((binding/'provenance.json').read_bytes()).hexdigest()}
env = {k:v for k,v in os.environ.items() if not k.startswith(('ANDROID_','ARCHTV_ANDROID_PROPERTY_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','CLASSPATH')}
env.update(ANDROID_DATA=str(out/'art-data'),ANDROID_LOG_TAGS='*:w')
with subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,start_new_session=True) as process:
    try: stdout,stderr=process.communicate(timeout=30)
    except BaseException:
        try: os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError: pass
        process.communicate();raise
(out/'services.stdout').write_bytes(stdout);(out/'services.stderr').write_bytes(stderr)
passed = process.returncode==0 and b'AOSP_SERVICE_CACHE_OK' in stdout
(out/'result.json').write_text(json.dumps({'original_service_cache_pass':passed,'exit_code':process.returncode,
 'command':command,'build_commands':commands,'adapter_classes':sorted(definitions),
 'sources_sha256':{str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest() for p in sources},
 'sha256':{str(p.resolve()):hashlib.sha256(p.read_bytes()).hexdigest() for p in (dex,out/'dex/classes.dex',args.linux_library)},
 'framework_provenance':proof,'window_contract':window_contract,
 'window_contract_load_pass':b'WINDOW_CONTRACT_LOADED classes=4' in stdout if window_contract else None,
 'scope':'Original ServiceManager boot cache getService/getServiceOrThrow/checkService and duplicate-init guard, with own local IBinder/IInterface endpoint identity and real close/death callbacks. No native Binder holder, IPC transport, global servicemanager, WindowManager service, compositor connection or APK UI integration proved.'},indent=2)+'\n')
if not passed:raise SystemExit('Service cache probe failed: '+str(out/'services.stderr'))
if window_contract and b'WINDOW_CONTRACT_LOADED classes=4' not in stdout:
    raise SystemExit('Window contract class loading failed: '+str(out/'services.stderr'))
print(out/'result.json')
