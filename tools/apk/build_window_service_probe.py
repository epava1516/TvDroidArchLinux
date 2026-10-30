#!/usr/bin/env python3
"""Build the typed Linux window service and a separate live-provider probe."""
import argparse,hashlib,json,subprocess,zipfile
from pathlib import Path
parser=argparse.ArgumentParser()
for name in ('aosp-build','bindings','tools','output'):parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--accessibility-bindings',type=Path)
parser.add_argument('--service-registry-bindings',type=Path)
args=parser.parse_args();root=Path(__file__).resolve().parents[2]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
framework=args.aosp_build.resolve();bindings=args.bindings.resolve();tools=args.tools.resolve()
fproof=json.loads((framework/'provenance.json').read_text());bproof=json.loads((bindings/'provenance.json').read_text())
assert sha(framework/'framework.jar')==fproof['framework_jar_sha256'] and sha(framework/'dex/classes.dex')==fproof['dex_sha256']
assert sha(bindings/'bindings.jar')==bproof['bindings_jar_sha256'] and sha(bindings/'dex/classes.dex')==bproof['dex_sha256']
assert 'android/graphics/Point.class' in fproof['runtime_classes']
assert fproof['compile_reference']==bproof['compile_reference']
reference=Path.home()/'.cache/archtv/aosp-compile-tools/android-all-13.jar';assert sha(reference)==fproof['compile_reference']['sha256']
manifest=json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())
for item in manifest['artifacts']:
    if item['file'] in ('r8.jar','android.jar'):assert sha(tools/item['file'])==item['sha256']
extra_classpath=[];accessibility_proof=None
if args.accessibility_bindings:
    extra=args.accessibility_bindings.resolve()
    accessibility_proof=json.loads((extra/'provenance.json').read_text())
    assert sha(extra/'bindings.jar')==accessibility_proof['bindings_jar_sha256']
    assert sha(extra/'dex/classes.dex')==accessibility_proof['dex_sha256']
    assert accessibility_proof['compile_reference']==fproof['compile_reference']
    extra_classpath.append(extra/'bindings.jar')
registry_proof=None
if args.service_registry_bindings:
    extra=args.service_registry_bindings.resolve();registry_proof=json.loads((extra/'provenance.json').read_text())
    assert sha(extra/'bindings.jar')==registry_proof['bindings_jar_sha256'] and sha(extra/'dex/classes.dex')==registry_proof['dex_sha256']
    assert registry_proof['compile_reference']==fproof['compile_reference']
    extra_classpath.append(extra/'bindings.jar')
source=root/'runtime/aosp/linux-services/org/archtv/aosplinux'
sources=[source/name for name in ('LocalServiceBinder.java','WindowPolicyState.java','LinuxWindowService.java')]
if args.service_registry_bindings:
    sources.append(source/'LinuxServiceRegistry.java')
    sources.append(root/'fixtures/aosp-window-service/ServiceRegistryChecks.java')
sources+=[root/'runtime/apk/java/org/archtv/apkruntime'/name for name in ('HostProfile.java','LinuxContext.java','AppEnvironment.java','ApkResources.java','ApkMetadata.java','IntPreferences.java')]
sources+=[root/'runtime/apk/java/android/content/SharedPreferences.java',root/'fixtures/aosp-window-service/WindowServiceProbe.java',root/'fixtures/aosp-window-service/AnimationPolicyChecks.java']
subprocess.run(['python',str(root/'tools/apk/generate_linux_window_service.py'),'--bindings',str(bindings),'--output',str(source/'LinuxWindowService.java'),'--check'],check=True)
out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
for name in ('classes','dex'):(out/name).mkdir()
jdk=Path('/usr/lib/jvm/java-17-openjdk/bin')
commands=[
 [jdk/'javac','--release','8','-classpath',':'.join(map(str,[bindings/'bindings.jar',framework/'framework.jar',reference,*extra_classpath])),'-d',out/'classes',*sources],
 [jdk/'jar','cf',out/'service.jar','-C',out/'classes','.'],
 [jdk/'java','-cp',tools/'r8.jar','com.android.tools.r8.D8','--release','--min-api','28','--lib',tools/'android.jar','--output',out/'dex',out/'service.jar']]
for i,command in enumerate(commands):
    with (out/('build-'+str(i)+'.log')).open('wb') as log:subprocess.run(list(map(str,command)),check=True,stdout=log,stderr=subprocess.STDOUT,timeout=120)
with zipfile.ZipFile(out/'service.jar') as archive:
    assert not any(n.endswith('.class') and n.startswith('android/') and n not in ('android/content/SharedPreferences.class','android/content/SharedPreferences$Editor.class') for n in archive.namelist())
(out/'provenance.json').write_text(json.dumps({'sources_sha256':{str(p.relative_to(root)):sha(p) for p in sources},
 'service_registry_bindings_dex_sha256':registry_proof['dex_sha256'] if registry_proof else None,
 'accessibility_bindings_dex_sha256':accessibility_proof['dex_sha256'] if accessibility_proof else None,
 'framework_dex_sha256':fproof['dex_sha256'],'bindings_dex_sha256':bproof['dex_sha256'],
 'service_jar_sha256':sha(out/'service.jar'),'dex_sha256':sha(out/'dex/classes.dex'),'commands':[list(map(str,c)) for c in commands],
 'scope':'Own Linux IWindowManager implementation: 7 host-state getters, 126 explicit unsupported methods. Original contract/Point/ServiceManager in separate verified artifacts. No window creation/rendering/global WM or APK integration from this build.'},indent=2)+'\n')
print(out/'dex/classes.dex')
