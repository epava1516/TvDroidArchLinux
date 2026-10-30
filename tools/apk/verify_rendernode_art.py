#!/usr/bin/env python3
"""Exercise original RenderNode Java/JNI/C++ object properties in ART."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
for name in ('build','linux-library','framework','art','tools','output'):
    parser.add_argument('--'+name,type=Path,required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
build, framework, tools, art = [p.resolve() for p in (args.build,args.framework,args.tools,args.art)]
proof = json.loads((build/'result.json').read_text())
library = build/'libarchtv_rendernode_host.so'
if not proof['build_pass'] or sha(library)!=proof['library_sha256']:
    raise SystemExit('RenderNode library build not verified')
fproof = json.loads((framework/'provenance.json').read_text())
if sha(framework/'framework.jar')!=fproof['framework_jar_sha256'] or sha(framework/'dex/classes.dex')!=fproof['dex_sha256']:
    raise SystemExit('Original framework modified')
for item in json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())['artifacts']:
    if item['file'] in ('r8.jar','android.jar') and sha(tools/item['file'])!=item['sha256']:
        raise SystemExit('DEX tool modified')
out = args.output.resolve()
out.mkdir(parents=True,exist_ok=False)
for name in ('classes','dex','art-data'):
    (out/name).mkdir(mode=0o700)
source = root/'fixtures/aosp-rendernode/RenderNodeProbe.java'
commands = [
    ['/usr/lib/jvm/java-17-openjdk/bin/javac','--release','8','-classpath',str(framework/'framework.jar'),'-d',str(out/'classes'),str(source)],
    ['/usr/lib/jvm/java-17-openjdk/bin/jar','cf',str(out/'probe.jar'),'-C',str(out/'classes'),'.'],
    ['/usr/lib/jvm/java-17-openjdk/bin/java','-cp',str(tools/'r8.jar'),'com.android.tools.r8.D8','--release','--min-api','28',
     '--lib',str(tools/'android.jar'),'--output',str(out/'dex'),str(out/'probe.jar')],
]
(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n')
for i,command in enumerate(commands):
    with (out/(str(i)+'.build.log')).open('w') as log:
        subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,check=True,timeout=120)
with zipfile.ZipFile(out/'probe.jar') as jar:
    if any(p.startswith('android/') for p in jar.namelist()):
        raise SystemExit('Probe must not replace original Android classes')
environment = {k:v for k,v in os.environ.items() if not k.startswith('ANDROID_') and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','CLASSPATH')}
environment.update(ANDROID_DATA=str(out/'art-data'),ANDROID_LOG_TAGS='*:w')
command = [str(art/'bin/art'),'--64','--no-compile','--','-Xint','-Xcheck:jni','-cp',
           str(framework/'dex/classes.dex')+':'+str(out/'dex/classes.dex'),'org.archtv.aospprobe.RenderNodeProbe',
           str(args.linux_library.resolve()),str(library)]
run = subprocess.run(command,capture_output=True,text=True,env=environment,timeout=30)
(out/'art.stdout').write_text(run.stdout)
(out/'art.stderr').write_text(run.stderr)
passed = run.returncode==0 and 'AOSP_RENDERNODE_PROPERTIES_OK objects=64 registered_methods=16 unsupported_rejected=1' in run.stdout
(out/'result.json').write_text(json.dumps({'original_rendernode_properties_pass':passed,'exit_code':run.returncode,'command':command,
    'source_sha256':sha(source),'verifier_sha256':sha(Path(__file__)),'library_sha256':sha(library),
    'library_provenance_sha256':sha(build/'result.json'),'framework_dex_sha256':fproof['dex_sha256'],
    'probe_dex_sha256':sha(out/'dex/classes.dex'),'linux_library_sha256':sha(args.linux_library),
    'scope':'Original Java RenderNode constructor and 16-entry native object/property profile. No recorded drawing, View construction, Wayland presentation or GC/lifetime/stability proof.'},indent=2)+'\n')
print(json.dumps({'original_rendernode_properties_pass':passed}))
if not passed:
    raise SystemExit(1)
