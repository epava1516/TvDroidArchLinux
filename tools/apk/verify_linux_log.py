#!/usr/bin/env python3
"""Exercise original AOSP Log and Linux JNI filtering/output on ART."""
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
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
(out/'classes').mkdir(); (out/'dex').mkdir(); (out/'art-data').mkdir(mode=0o700)
proof = json.loads((args.aosp_build/'provenance.json').read_text())
dex = args.aosp_build.resolve()/'dex/classes.dex'
assert hashlib.sha256(dex.read_bytes()).hexdigest() == proof['dex_sha256']
assert hashlib.sha256((args.aosp_build/'framework.jar').read_bytes()).hexdigest() == proof['framework_jar_sha256']
assert 'android/util/Log.class' in proof['runtime_classes']
assert proof['original_sources_modified'] is False
manifest = json.loads((root/'runtime/aosp/framework-study.json').read_text())
path = 'core/java/android/util/Log.java'
sha = next(item['sha256'] for item in manifest['files'] if item['path']==path)
assert any(name.endswith('/'+path) and digest==sha for name,digest in proof['original_sources_sha256'].items())
source = root/'fixtures/aosp-log/LogProbe.java'
sources = [source]
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
assert definitions == {'Lorg/archtv/aospprobe/LogProbe;'}
base = [str(args.art.resolve()/'bin/art'),'--64','--no-compile','--','-Xint','-Xcheck:jni','-cp',
 ':'.join(map(str,[dex,out/'dex/classes.dex'])),'org.archtv.aospprobe.LogProbe',str(args.linux_library.resolve())]
base_env = {k:v for k,v in os.environ.items() if not k.startswith(('ANDROID_','ARCHTV_ANDROID_PROPERTY_')) and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','CLASSPATH')}
base_env.update(ANDROID_DATA=str(out/'art-data'),ANDROID_LOG_TAGS='*:w')
cases = [
 ('default',{},4,4),
 ('tag-debug',{'log.tag.Probe':'DEBUG','persist.log.tag.Probe':'ERROR','log.tag':'WARN'},3,5),
 ('persistent-fallback',{'log.tag.Probe':'invalid','persist.log.tag.Probe':'ERROR','log.tag':'WARN'},6,5),
 ('global-silent',{'log.tag':'SILENT'},8,8)]
results=[]
for name,properties,minimum,global_minimum in cases:
    env = dict(base_env,**{'ARCHTV_ANDROID_PROPERTY_'+key:value for key,value in properties.items()})
    command = base+[str(minimum),str(global_minimum)]
    with subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,start_new_session=True) as process:
        try: stdout,stderr=process.communicate(timeout=30)
        except BaseException:
            try: os.killpg(process.pid,signal.SIGKILL)
            except ProcessLookupError: pass
            process.communicate();raise
    (out/(name+'.stdout')).write_bytes(stdout);(out/(name+'.stderr')).write_bytes(stderr)
    assert process.returncode == 0 and b'AOSP_LINUX_LOG_OK' in stdout, str(out/(name+'.stderr'))
    assert (b'Hola \xc3\xb1 \xf0\x9f\x93\xba' in stderr) == (minimum<=4)
    stderr.decode('utf-8')  # UTF-16 JNI input must become valid UTF-8, including truncation.
    entries = [line for line in stderr.splitlines() if line.startswith(b'ANDROID_LOG ')]
    expected_entries = (2 if minimum<=4 else 0)+(1 if minimum<=4 and global_minimum<=4 else 0)+(3 if minimum<=6 else 0)
    assert len(entries)==expected_entries
    if minimum<=4:
        assert any(line.endswith('ñ'.encode()*2030) for line in entries)
    for channel in ('radio','system','crash'):
        assert any(b'buffer='+channel.encode()+b' ' in line for line in entries)==(minimum<=6)
    for marker in (b'BINARY_BUFFER_REJECTED',b'INVALID_PRIORITY_REJECTED',b'OVERSIZED_TAG_REJECTED'):
        assert marker not in stderr
    results.append({'case':name,'properties':properties,'minimum':minimum,'global_minimum':global_minimum,'command':command})
(out/'result.json').write_text(json.dumps({'original_log_linux_pass':True,'cases':results,'build_commands':commands,
 'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),
 'sha256':{str(path.resolve()):hashlib.sha256(path.read_bytes()).hexdigest() for path in
    (args.linux_library,out/'dex/classes.dex',dex,args.aosp_build/'framework.jar')},
 'scope':'Original AOSP Log Java on ART with three Linux JNI methods, actual stderr UTF8 text, property thresholds and precedence, null message/tag, long tag, payload boundary and explicit unsupported binary buffer. No logd, Android ring buffers, WTF handler, throwable writer or full StrictMode support claim.'},indent=2)+'\n')
print(out/'result.json')
