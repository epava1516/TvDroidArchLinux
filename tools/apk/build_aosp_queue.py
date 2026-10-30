#!/usr/bin/env python3
"""Compile unmodified original AOSP queue classes and a separate linkage probe."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess
import zipfile
from view_resource_bindings import generate as generate_view_bindings

parser = argparse.ArgumentParser()
parser.add_argument('--sources', type=Path, required=True)
parser.add_argument('--reference', type=Path, required=True)
parser.add_argument('--tools', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--with-views', action='store_true', help='Experimental original View/ViewGroup compilation; not runtime integration')
parser.add_argument('--with-context', action='store_true', help='Compile original Context, ContextWrapper, Application and component callbacks')
parser.add_argument('--with-public-resources', action='store_true', help='Compile original Resources/ResourcesImpl and their recorded dependency set')
parser.add_argument('--with-resources', action='store_true', help='Compile original AssetManager, ApkAssets and TypedValue as well')
parser.add_argument('--jdk', type=Path, default=Path('/usr/lib/jvm/java-17-openjdk'))
args = parser.parse_args()
if args.with_views:
    args.with_context = True
if args.with_context:
    args.with_public_resources = True
if args.with_public_resources:
    args.with_resources = True
root = Path(__file__).resolve().parents[2]
manifest = json.loads((root/'runtime/aosp/framework-study.json').read_text())
reference = json.loads((root/'runtime/aosp/compile-reference.json').read_text())
tools = json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())


def verify(path, expected):
    with path.open('rb') as stream:
        actual = hashlib.file_digest(stream, 'sha256').hexdigest()
    if actual != expected:
        raise SystemExit('Checksum mismatch: '+str(path))


verify(args.reference, reference['sha256'])
for item in tools['artifacts']:
    if item['file'] in ('android.jar', 'r8.jar'):
        verify(args.tools/item['file'], item['sha256'])
paths = ['core/java/android/os/'+name+'.java' for name in ('Looper', 'Handler', 'Message', 'MessageQueue', 'Parcelable', 'SystemClock', 'ThreadLocalWorkSource')]
paths += ['core/java/android/util/SparseArray.java', 'core/java/android/util/ContainerHelpers.java',
          'core/java/com/android/internal/util/ArrayUtils.java', 'core/java/com/android/internal/util/GrowingArrayUtils.java']
paths += ['core/java/android/os/Binder.java', 'core/java/android/os/IBinder.java',
          'core/java/android/util/IntArray.java', 'core/java/com/android/internal/os/BinderInternal.java']
paths += ['core/java/android/os/Process.java', 'core/java/android/os/ZygoteProcess.java',
          'core/java/android/os/SystemProperties.java', 'core/java/android/net/LocalSocketAddress.java']
if args.with_resources:
    paths += ['core/java/android/content/res/AssetManager.java', 'core/java/android/content/res/ApkAssets.java', 'core/java/android/content/res/StringBlock.java', 'core/java/android/util/TypedValue.java']
if args.with_resources:
    paths += ['core/java/com/android/internal/util/Parcelling.java']
    paths += ['core/java/android/util/'+name+'.java' for name in ('ArrayMap', 'ArraySet', 'MapCollections')]
    paths += ['core/java/android/content/pm/'+name+'.java' for name in ('ActivityInfo', 'ComponentInfo', 'PackageItemInfo')]
if args.with_public_resources:
    paths += manifest['public_resources_sources']
if args.with_context:
    paths += manifest['context_sources']
if args.with_views:
    paths += manifest['view_sources']
sources = []
for path in paths:
    item = next(item for item in manifest['files'] if item['path'] == path)
    source = args.sources/path
    verify(source, item['sha256'])
    sources.append(source.resolve())
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
for name in ('classes', 'stubs', 'dex'):
    (out/name).mkdir()
reference_path = args.reference.resolve()
tool_path = args.tools.resolve()
stubs = sorted((root/'runtime/aosp/compile-stubs').rglob('*.java'))
probes = sorted((root/'fixtures/aosp-queue').glob('*.java'))
if args.with_resources:
    probes += sorted((root/'fixtures/aosp-resources').glob('*.java'))
if args.with_public_resources:
    probes += sorted((root/'fixtures/aosp-public-resources').glob('*.java'))
if args.with_views:
    probes += sorted((root/'fixtures/aosp-views').glob('*.java'))
commands = []


def run(name, command):
    command = [str(part) for part in command]
    commands.append({'name': name, 'command': command})
    with (out/(name+'.stdout')).open('w') as stdout, (out/(name+'.stderr')).open('w') as stderr:
        result = subprocess.run(command, stdout=stdout, stderr=stderr, timeout=120)
    if result.returncode != 0:
        raise SystemExit('Build failed: '+name+'; see '+str(out))


run('compile-private-declarations', [args.jdk/'bin/javac', '--release', '8', '-d', out/'stubs', *stubs])
run('pack-private-declarations', [args.jdk/'bin/jar', 'cf', out/'compile-only.jar', '-C', out/'stubs', '.'])
boot = ':'.join(str(path) for path in [out/'compile-only.jar', reference_path, tool_path/'android.jar'])
run('compile-original', [args.jdk/'bin/javac', '-source', '8', '-target', '8', '-bootclasspath', boot,
                         '-d', out/'classes', *sources])
view_bindings = {}
if args.with_views:
    generated_source, view_bindings = generate_view_bindings(args.sources, manifest, out/'generated')
    run('compile-view-resource-binding', [args.jdk/'bin/javac', '--release', '8', '-d', out/'classes', generated_source])
    binding_check = root/'fixtures/aosp-view-bindings/ResourceBindingCheck.java'
    (out/'binding-check').mkdir()
    run('compile-view-binding-check', [args.jdk/'bin/javac', '--release', '8', '-d', out/'binding-check', binding_check])
    run('verify-view-resource-binding', [args.jdk/'bin/java', '-cp', out/'binding-check', 'ResourceBindingCheck', out/'classes', reference_path])
    view_bindings['reference_comparison_pass'] = True
    view_bindings['check_source_sha256'] = hashlib.sha256(binding_check.read_bytes()).hexdigest()
prebuilt_bindings = {}
if args.with_public_resources:
    prebuilt_bindings = json.loads((root/'runtime/aosp/prebuilt-bindings.json').read_text())
    verify(args.reference, prebuilt_bindings['artifact_sha256'])
    with zipfile.ZipFile(args.reference) as archive:
        for name, expected in prebuilt_bindings['classes'].items():
            data = archive.read(name)
            if len(data) != expected['bytes'] or hashlib.sha256(data).hexdigest() != expected['sha256']:
                raise SystemExit('Generated binding mismatch: '+name)
            destination = out/'classes'/name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(data)
run('pack-framework', [args.jdk/'bin/jar', 'cf', out/'framework.jar', '-C', out/'classes', '.'])
run('compile-probe', [args.jdk/'bin/javac', '--release', '8', '-classpath', str(out/'classes')+':'+str(reference_path),
                      '-d', out/'classes', *probes])
run('pack-original', [args.jdk/'bin/jar', 'cf', out/'queue.jar', '-C', out/'classes', '.'])
with zipfile.ZipFile(out/'queue.jar') as archive:
    classes = sorted(name for name in archive.namelist() if name.endswith('.class'))
    if any(not name.startswith(('android/os/', 'android/util/', 'android/net/', 'android/content/', 'android/content/pm/', 'android/app/', 'android/view/', 'android/graphics/', 'android/text/', 'android/sysprop/', 'com/android/internal/R.class', 'com/android/internal/R$', 'com/android/internal/util/', 'com/android/internal/os/', 'org/archtv/aospprobe/')) for name in classes):
        raise SystemExit('Unexpected compile-only class in runtime artifact')
run('dex-original', [args.jdk/'bin/java', '-cp', tool_path/'r8.jar', 'com.android.tools.r8.D8', '--release',
                     '--min-api', '28', '--lib', tool_path/'android.jar', '--output', out/'dex', out/'queue.jar'])
(out/'provenance.json').write_text(json.dumps({
    'source_revision': manifest['revision'],
    'original_sources_sha256': {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
    'original_sources_modified': False,
    'framework_jar_sha256': hashlib.sha256((out/'framework.jar').read_bytes()).hexdigest(),
    'compile_reference': reference,
    'prebuilt_bindings': prebuilt_bindings,
    'view_resource_bindings': view_bindings,
    'compile_only_declarations_sha256': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in stubs},
    'probes_sha256': {str(path.relative_to(root)): hashlib.sha256(path.read_bytes()).hexdigest() for path in probes},
    'runtime_classes': classes, 'commands': commands,
    'dex_sha256': hashlib.sha256((out/'dex/classes.dex').read_bytes()).hexdigest(),
    'scope': 'Original AOSP queue source compilation and DEX generation. Compile-only jar, declarations and full framework reference excluded except recorded allowlisted generated bindings. JNI, functional queue and APK compatibility not proved.',
}, indent=2)+'\n')
print(out/'dex/classes.dex')
