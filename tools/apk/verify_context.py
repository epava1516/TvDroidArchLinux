#!/usr/bin/env python3
"""Build a separate Context/ContextWrapper probe and execute it on the actual APK runtime."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess

parser = argparse.ArgumentParser()
for name in ('runtime-build', 'aosp-build', 'tools', 'art', 'linux-library', 'resources-library', 'output'):
    parser.add_argument('--'+name, type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
(out/'classes').mkdir(); (out/'dex').mkdir(); (out/'art-data').mkdir(mode=0o700)
proof = json.loads((args.runtime_build/'provenance.json').read_text())
dex = args.runtime_build.resolve()/'dex/classes.dex'
assert hashlib.sha256(dex.read_bytes()).hexdigest() == proof['dex_sha256']
assert hashlib.sha256((args.runtime_build/'runtime.jar').read_bytes()).hexdigest() == proof['runtime_jar_sha256']
assert 'runtime/apk/java/android/content/Context.java' not in proof['sources_sha256']
assert 'android/content/Context.class' in proof['framework_class_files']
assert hashlib.sha256((args.aosp_build/'framework.jar').read_bytes()).hexdigest() == proof['aosp_build']['framework_jar_sha256']
source = root/'fixtures/aosp-context/ContextProbe.java'
jdk = Path('/usr/lib/jvm/java-17-openjdk/bin')
reference = Path.home()/'.cache/archtv/aosp-compile-tools/android-all-13.jar'
assert hashlib.sha256(reference.read_bytes()).hexdigest() == json.loads((root/'runtime/aosp/compile-reference.json').read_text())['sha256']
toolchain = json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())
r8 = args.tools.resolve()/'r8.jar'
for name in ('r8.jar', 'android.jar'):
    assert hashlib.sha256((args.tools/name).read_bytes()).hexdigest() == next(item['sha256'] for item in toolchain['artifacts'] if item['file']==name)
commands = [
 [str(jdk/'javac'), '--release','8','-classpath',':'.join(map(str,[args.runtime_build.resolve()/'runtime.jar',args.aosp_build.resolve()/'framework.jar',reference])), '-d',str(out/'classes'),str(source)],
 [str(jdk/'jar'),'cf',str(out/'probe.jar'),'-C',str(out/'classes'),'.'],
 [str(jdk/'java'),'-cp',str(r8),'com.android.tools.r8.D8','--release','--min-api','28','--lib',str(args.tools.resolve()/'android.jar'),'--output',str(out/'dex'),str(out/'probe.jar')]]
for index, command in enumerate(commands):
    with (out/('build-'+str(index)+'.log')).open('wb') as log:
        subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT,timeout=120)
apk = root/'fixtures/apk/counter/golden/counter.apk'
assert hashlib.sha256(apk.read_bytes()).hexdigest() == 'f07c9b92ab3353237276081c22e11ce06168b8c9f71a99ea32968b2ce0f00e28'
command = [str(args.art.resolve()/'bin/art'),'--64','--no-compile','--','-Xint','-Xcheck:jni','-cp',
 ':'.join(map(str,[dex,out/'dex/classes.dex',apk])), 'org.archtv.apkruntime.ContextProbe',
 str(args.linux_library.resolve()),str(args.resources_library.resolve()),str(apk),str(out/'data')]
env = {k:v for k,v in os.environ.items() if not k.startswith('ANDROID_') and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','CLASSPATH')}
env.update(ANDROID_DATA=str(out/'art-data'),ANDROID_LOG_TAGS='*:w')
with subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,start_new_session=True) as process:
    try: stdout,stderr=process.communicate(timeout=30)
    except BaseException:
        try: os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError: pass
        process.communicate();raise
(out/'context.stdout').write_bytes(stdout);(out/'context.stderr').write_bytes(stderr)
passed = process.returncode == 0 and stdout.strip() == b'AOSP_CONTEXT_OK'
(out/'result.json').write_text(json.dumps({'context_pass':passed,'exit_code':process.returncode,'command':command,
 'probe_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(), 'runtime_dex_sha256':hashlib.sha256(dex.read_bytes()).hexdigest(),
 'inputs_sha256':{str(path.resolve()):hashlib.sha256(path.read_bytes()).hexdigest() for path in (args.linux_library,args.resources_library,out/'dex/classes.dex',apk,args.runtime_build/'runtime.jar',args.aosp_build/'framework.jar')},
 'scope':'Original Context resource methods, ContextWrapper delegation/attach guard, original Application identity/component callbacks (manual memory dispatch), six real Linux hooks and explicit unsupported service. No ContextImpl, full Activity/View, system services or general APK compatibility claim.'},indent=2)+'\n')
if not passed:raise SystemExit('Context probe failed: '+str(out/'context.stderr'))
print(out/'result.json')
