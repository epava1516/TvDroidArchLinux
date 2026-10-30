#!/usr/bin/env python3
"""Record original View linkage in ART without the full compile reference at runtime."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
from apk_inventory import dex_inventory

parser = argparse.ArgumentParser()
for name in ('aosp-build', 'art', 'linux-library', 'resources-library', 'output'):
    parser.add_argument('--'+name, type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
build = args.aosp_build.resolve()
proof = json.loads((build/'provenance.json').read_text())
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
dex = build/'dex/classes.dex'
assert digest(dex) == proof['dex_sha256']
assert digest(build/'framework.jar') == proof['framework_jar_sha256']
manifest = json.loads((root/'runtime/aosp/framework-study.json').read_text())
for path in manifest['view_sources']:
    name = Path(path).stem
    expected = next(item['sha256'] for item in manifest['files'] if item['path'] == path)
    assert any(source.endswith('/'+path) and sha == expected
               for source, sha in proof['original_sources_sha256'].items())
    package_path = path.split('/java/',1)[1][:-5]+'.class'
    assert package_path in proof['runtime_classes']
assert not any(name.startswith(('org/robolectric/', 'android/widget/')) for name in proof['runtime_classes'])
assert proof['view_resource_bindings']['reference_comparison_pass']
assert 'com/android/internal/R$styleable.class' in proof['runtime_classes']
source = root/'fixtures/aosp-views/ViewLinkageProbe.java'
assert proof['probes_sha256'][str(source.relative_to(root))] == digest(source)
out = args.output.resolve();out.mkdir(parents=True,exist_ok=False)
(out/'art-data').mkdir(mode=0o700)
command = [str(args.art.resolve()/'bin/art'),'--64','--no-compile','--','-Xint','-Xcheck:jni',
 '-cp',str(dex),'org.archtv.aospprobe.ViewLinkageProbe',str(args.linux_library.resolve()),
 str(args.resources_library.resolve())]
env = {k:v for k,v in os.environ.items() if not k.startswith('ANDROID_') and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','CLASSPATH')}
env.update(ANDROID_DATA=str(out/'art-data'),ANDROID_LOG_TAGS='*:w')
with subprocess.Popen(command,stdout=subprocess.PIPE,stderr=subprocess.PIPE,env=env,start_new_session=True) as process:
    try: stdout,stderr = process.communicate(timeout=45)
    except BaseException:
        try: os.killpg(process.pid,signal.SIGKILL)
        except ProcessLookupError: pass
        process.communicate();raise
(out/'views.stdout').write_bytes(stdout);(out/'views.stderr').write_bytes(stderr)
assert process.returncode == 0 and b'VIEW_LINKAGE_DIAGNOSTIC_DONE' in stdout
assert b'VIEW_STATESET_OK masks=1024' in stdout
types, definitions, methods = dex_inventory(dex.read_bytes())
external = sorted(name for name in types-definitions if name.startswith(('Landroid/', 'Lcom/android/')))
(out/'external-framework-types.json').write_text(json.dumps({'types':external,'count':len(external),'scope':'Static references absent from this DEX; not a reachability analysis or proof every type must be ported.'},indent=2)+'\n')
lines = stdout.decode().splitlines()
loaded = [line for line in lines if line.startswith('VIEW_LINKAGE_LOADED ')]
blocked = [line for line in lines if line.startswith('VIEW_LINKAGE_BLOCKED ')]
assert len(loaded)+len(blocked) == 3
(out/'result.json').write_text(json.dumps({'diagnostic_completed':True,'all_three_classes_linked':len(loaded)==3,
 'original_stateset_masks_checked':1024,
 'original_measurement_helpers_pass':b'VIEW_MEASUREMENT_HELPERS_OK' in stdout,
 'initialized':[line for line in lines if line.startswith('VIEW_LINKAGE_INITIALIZED ')],
 'loaded':loaded,'blocked':blocked,'command':command,
 'sha256':{str(path.resolve()):digest(path) for path in (dex,source,args.linux_library,args.resources_library)},
 'scope':'Pinned original View/ViewGroup/ContextThemeWrapper ART initialization and public constructor-signature resolution, StateSet masks/matching and static measurement helpers. Generated state binding checked at build time; no full reference on runtime classpath. Linkage failures remain incomplete work. No View object, instance measure/layout, rendering, input or APK integration proved.'},indent=2)+'\n')
print(out/'result.json')
