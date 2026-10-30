#!/usr/bin/env python3
"""Build the original AOSP androidfw host source set with one compiler job."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('--sources', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--art', type=Path, required=True, help='Verified ART host bundle supplying the matching libc++.so')
parser.add_argument('--resume', action='store_true', help='Reuse only matching, checksummed objects after a terminal build failure')
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
sources = args.sources.resolve()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=args.resume)
for name in ('objects', 'logs'):
    (out/name).mkdir(exist_ok=args.resume)
manifest = json.loads((root/'runtime/aosp/androidfw-sources.json').read_text())
recipe = json.loads((root/'runtime/aosp/androidfw-build.json').read_text())
for component in manifest['components']:
    for name, expected in component['files'].items():
        path = sources/component['name']/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected['sha256']:
            raise SystemExit('Original source mismatch: '+str(path))
libcxx = args.art.resolve()/'lib64/libc++.so'
libcxx_hash = hashlib.sha256(libcxx.read_bytes()).hexdigest()
compiler = subprocess.check_output(['clang++', '--version'], text=True)
fingerprint = hashlib.sha256((json.dumps(manifest, sort_keys=True)+json.dumps({k: v for k, v in recipe.items() if k not in ('cpp_standards', 'component_flags')}, sort_keys=True)
                             +compiler+libcxx_hash).encode()).hexdigest()
includes = ['-I'+str(sources/path) for path in recipe['includes']]
common = ['-fPIC', '-O0', '-g0', '-DSTATIC_ANDROIDFW_FOR_TOOLS', '-DFMT_HEADER_ONLY',
          '-DNDEBUG', '-D_FILE_OFFSET_BITS=64', '-D_GNU_SOURCE', '-DLIBLOG_LOG_TAG=1006', '-DSNET_EVENT_LOG_TAG=1397638484']
cpp = ['clang++', '-std=gnu++17', '-stdlib=libc++', '-nostdinc++', '-isystem', str(sources/'libcxx'), *common, *includes]
objects, commands, archives = [], [], []
for component, files in recipe['components'].items():
    component_objects = []
    for filename in files:
        source = sources/component/filename
        key = component+'-'+filename.replace('/', '-')
        target = out/'objects'/(key+'.o')
        state = target.with_suffix('.json')
        command = (['clang', '-std=gnu11', *common, *includes] if source.suffix == '.c' else cpp)+['-c', str(source), '-o', str(target)]
        if component in recipe.get('cpp_standards', {}) and source.suffix != '.c':
            command[1] = '-std='+recipe['cpp_standards'][component]
        command.extend(recipe.get('component_flags', {}).get(component, []))
        command_hash = hashlib.sha256((fingerprint+json.dumps(command)).encode()).hexdigest()
        cached = json.loads(state.read_text()) if args.resume and state.exists() else {}
        if not (cached.get('command_hash') == command_hash and target.exists()
                and cached.get('object_sha256') == hashlib.sha256(target.read_bytes()).hexdigest()):
            print('Compiling '+component+'/'+filename, flush=True)
            with (out/'logs'/(key+'.log')).open('w') as log:
                result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=180)
            if result.returncode != 0:
                raise SystemExit('Compile failed; see '+str(out/'logs'/(key+'.log')))
            state.write_text(json.dumps({'command_hash': command_hash,
                'object_sha256': hashlib.sha256(target.read_bytes()).hexdigest()})+'\n')
        commands.append(command)
        objects.append(target)
        component_objects.append(target)
    archive = out/('lib'+component+'_host.a')
    command = ['ar', 'rcs', str(archive), *map(str, component_objects)]
    subprocess.run(command, check=True, timeout=60)
    commands.append(command)
    archives.append(archive)
library = out/'archtv-resource-probe'
probe = root/'runtime/aosp/native/resource-probe.cpp'
command = [*cpp, '-L'+str(libcxx.parent), '-Wl,-rpath,'+str(libcxx.parent), '-o', str(library), str(probe),
           '-Wl,--start-group', *map(str, archives), '-Wl,--end-group', '-lz', '-ldl', '-lpthread']
with (out/'link.log').open('w') as log:
    result = subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, timeout=120)
if result.returncode != 0:
    raise SystemExit('Link failed; see '+str(out/'link.log'))
(out/'provenance.json').write_text(json.dumps({'source_manifest': manifest, 'recipe': recipe, 'compiler': compiler,
    'libcxx_runtime_sha256': libcxx_hash, 'commands': commands+[command],
    'probe_source_sha256': hashlib.sha256(probe.read_bytes()).hexdigest(),
    'original_sources_modified': False, 'probe_sha256': hashlib.sha256(library.read_bytes()).hexdigest(),
    'archives': {path.name: hashlib.sha256(path.read_bytes()).hexdigest() for path in archives},
    'scope': 'Original Linux host androidfw build with matching original libc++ headers and ART libc++ runtime; no resource lookup, JNI integration, APK execution or distribution claim from this build.'}, indent=2)+'\n')
print(library)
