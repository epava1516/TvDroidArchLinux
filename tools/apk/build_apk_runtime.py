#!/usr/bin/env python3
"""Build the host API subset to DEX. APK application sources are not inputs."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--tools', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--aosp-build', type=Path, required=True)
parser.add_argument('--reference', type=Path, default=Path.home()/'.cache/archtv/aosp-compile-tools/android-all-13.jar')
parser.add_argument('--jdk', type=Path, default=Path('/usr/lib/jvm/java-17-openjdk'))
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
tools = args.tools.resolve()
aosp_build = args.aosp_build.resolve()
framework = aosp_build/'framework.jar'
aosp_provenance = json.loads((aosp_build/'provenance.json').read_text())
with framework.open('rb') as stream:
    if hashlib.file_digest(stream, 'sha256').hexdigest() != aosp_provenance['framework_jar_sha256']:
        raise SystemExit('Framework jar checksum mismatch')
if aosp_provenance['original_sources_modified'] is not False:
    raise SystemExit('Expected unmodified original framework sources')
with zipfile.ZipFile(framework) as archive:
    if any(name.startswith(('org/archtv/', 'java/')) for name in archive.namelist()):
        raise SystemExit('Framework jar contains probes or compile-only classes')
    required = {'android/app/Application.class', 'android/content/Context.class', 'android/content/res/Resources.class', 'android/content/res/ResourcesImpl.class', 'android/content/res/AssetManager.class', 'android/content/res/ApkAssets.class', 'android/content/res/StringBlock.class'}
    if not required.issubset(archive.namelist()):
        raise SystemExit('Build original framework with --with-context first')
    framework_classes = sorted(name for name in archive.namelist() if name.endswith('.class'))
manifest = json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())
for item in manifest['artifacts']:
    if item['file'] in ('r8.jar', 'android.jar'):
        with (tools/item['file']).open('rb') as stream:
            if hashlib.file_digest(stream, 'sha256').hexdigest() != item['sha256']:
                raise SystemExit('Tool checksum mismatch: '+item['file'])
reference = json.loads((root/'runtime/aosp/compile-reference.json').read_text())
if hashlib.sha256(args.reference.read_bytes()).hexdigest() != reference['sha256']:
    raise SystemExit('Internal compiler reference mismatch')
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
(out/'classes').mkdir()
(out/'dex').mkdir()
sources = sorted((root/'runtime/apk/java').rglob('*.java'))
commands = [
    [args.jdk/'bin/javac', '--release', '8', '-classpath', str(framework)+':'+str(args.reference.resolve())+':'+str(tools/'android.jar'),
     '-encoding', 'UTF-8', '-d', out/'classes', *sources],
    [args.jdk/'bin/jar', 'cf', out/'runtime.jar', '-C', out/'classes', '.'],
    [args.jdk/'bin/java', '-cp', tools/'r8.jar', 'com.android.tools.r8.D8', '--release',
     '--min-api', '28', '--lib', tools/'android.jar', '--output', out/'dex', out/'runtime.jar', framework],
]
for command in commands:
    subprocess.run([str(part) for part in command], check=True, timeout=120)
(out/'provenance.json').write_text(json.dumps({
    'sources_sha256': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest()
                       for path in sources},
    'dex_sha256': hashlib.sha256((out/'dex/classes.dex').read_bytes()).hexdigest(),
    'runtime_jar_sha256': hashlib.sha256((out/'runtime.jar').read_bytes()).hexdigest(),
    'host_compile_reference': reference,
    'toolchain': manifest,
    'aosp_build': aosp_provenance,
    'framework_class_files': framework_classes,
    'scope': 'Host API subset only. No application classes compiled or included; no APK compatibility claim from a build.',
}, indent=2)+'\n')
print(out/'dex/classes.dex')
