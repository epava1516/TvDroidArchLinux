#!/usr/bin/env python3
"""Build isolated Linux context adapters and attempt the original View constructor on ART."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
from apk_inventory import dex_inventory

parser = argparse.ArgumentParser()
for name in ('aosp-build', 'tools', 'art', 'linux-library', 'resources-library', 'output'):
    parser.add_argument('--'+name, type=Path, required=True)
parser.add_argument('--system-resources-build',type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
(out/'classes').mkdir(); (out/'dex').mkdir(); (out/'art-data').mkdir(mode=0o700)
proof = json.loads((args.aosp_build/'provenance.json').read_text())
dex = args.aosp_build.resolve()/'dex/classes.dex'
assert hashlib.sha256(dex.read_bytes()).hexdigest() == proof['dex_sha256']
assert hashlib.sha256((args.aosp_build/'framework.jar').read_bytes()).hexdigest() == proof['framework_jar_sha256']
assert 'android/view/View.class' in proof['runtime_classes']
assert proof['original_sources_modified'] is False
manifest = json.loads((root/'runtime/aosp/framework-study.json').read_text())
view_path = 'core/java/android/view/View.java'
view_sha = next(item['sha256'] for item in manifest['files'] if item['path']==view_path)
assert any(path.endswith('/'+view_path) and sha==view_sha
           for path,sha in proof['original_sources_sha256'].items())
source = root/'fixtures/aosp-view-constructor/ViewConstructorProbe.java'
sources = [root/'runtime/apk/java/org/archtv/apkruntime'/name for name in
    ('HostProfile.java','LinuxContext.java','AppEnvironment.java','ApkResources.java','IntPreferences.java')]
sources += [root/'runtime/apk/java/android/content/SharedPreferences.java',source,
            root/'fixtures/aosp-view-constructor/SystemResourcesChecks.java']
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
adapter_types = dex_inventory((out/'dex/classes.dex').read_bytes())[1]
assert not any(name.startswith(('Landroid/view/', 'Landroid/widget/', 'Landroid/app/', 'Lorg/archtv/probe/')) for name in adapter_types)
apk = root/'fixtures/apk/counter/golden/counter.apk'
assert hashlib.sha256(apk.read_bytes()).hexdigest() == 'f07c9b92ab3353237276081c22e11ce06168b8c9f71a99ea32968b2ce0f00e28'
command = [str(args.art.resolve()/'bin/art'),'--64','--no-compile','--','-Xint','-Xcheck:jni','-cp',
 ':'.join(map(str,[dex,out/'dex/classes.dex'])), 'org.archtv.apkruntime.ViewConstructorProbe',
 str(args.linux_library.resolve()),str(args.resources_library.resolve()),str(apk),str(out/'data')]
system_proof = None
if args.system_resources_build:
    system_apk = args.system_resources_build.resolve()/'framework-res.apk'
    system_proof = json.loads((args.system_resources_build/'provenance.json').read_text())
    assert hashlib.sha256(system_apk.read_bytes()).hexdigest()==system_proof['apk_sha256']
    command.append(str(system_apk))
env = {k:v for k,v in os.environ.items() if not k.startswith('ANDROID_') and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','CLASSPATH')}
env.update(ANDROID_DATA=str(out/'art-data'),ANDROID_LOG_TAGS='*:w')
with subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,start_new_session=True) as process:
    try: stdout,stderr=process.communicate(timeout=30)
    except BaseException:
        try: os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError: pass
        process.communicate();raise
(out/'constructor.stdout').write_bytes(stdout);(out/'constructor.stderr').write_bytes(stderr)
assert process.returncode == 0 and b'VIEW_CONSTRUCTOR_DIAGNOSTIC_DONE' in stdout, str(out/'constructor.stderr')
if system_proof:
    assert b'SYSTEM_RESOURCES_OK count=18 density=160 app-cookie=2' in stdout
    assert b'SYSTEM_RESOURCES_OK count=18 density=320 app-cookie=2' in stdout
constructed = b'VIEW_CONSTRUCTOR_OK android.view.View' in stdout
assert constructed != (b'VIEW_CONSTRUCTOR_BLOCKED ' in stdout)
(out/'result.json').write_text(json.dumps({'diagnostic_completed':True,'original_view_constructed':constructed,
 'exit_code':process.returncode,'command':command,'build_commands':commands,
 'adapter_classes':sorted(adapter_types),
 'sources_sha256':{str(path.relative_to(root)):hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
 'framework_provenance':proof,'system_resources':system_proof,
 'inputs_sha256':{str(path.resolve()):hashlib.sha256(path.read_bytes()).hexdigest() for path in
    (args.linux_library,args.resources_library,out/'dex/classes.dex',apk,args.aosp_build/'framework.jar',dex,out/'probe.jar')},
 'scope':'Actual original View constructor with existing LinuxContext and original Application/Resources, APK assets and original main Looper. Isolated adapter DEX includes prototype integer SharedPreferences but excludes own Activity/View/ViewGroup/widgets and app classes. Full reference is compiler-only. Blocked constructor is incomplete work, not a functional UI pass.'},indent=2)+'\n')
print(out/'result.json')
