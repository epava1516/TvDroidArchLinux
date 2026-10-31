#!/usr/bin/env python3
"""Build complete original Android SwiftShader modules, excluding LLVM/link."""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('/home/tv/.cache/archtv/aosp16-qpr2/swiftshader-source-1')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('llvm_recipe', Path(__file__).with_name('build-llvm.py'))
    recipe = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(recipe)
    assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == recipe.REVISION
    subprocess.run(['git', '-C', str(SOURCE), 'diff', '--quiet', 'HEAD', '--', '.'], check=True)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    generated = ROOT / 'dist/aosp16/swiftshader-generated-1'
    assert all(row['exit'] == 0 for row in json.loads((generated / 'generation.json').read_text())['commands'])
    prior = json.loads((ROOT / 'dist/aosp16/swiftshader-llvm16-1/inputs.json').read_text())
    llvm_args = prior['sources'][0]['argv']
    compiler = llvm_args[0]
    first_include = next(i for i, a in enumerate(llvm_args) if a.startswith('-I'))
    base_flags = llvm_args[1:first_include]
    llvm_includes = [a for a in llvm_args if a.startswith('-I')]
    old = json.loads((ROOT / 'reports/android16-hwc3-frontend/build.json').read_text())['results'][0]['argv']
    native = [a for a in old if a.startswith('-I') and any(p in a for p in
        ['libbase', 'fmtlib', 'liblog/include', 'libcutils/include', 'libsystem/include',
         'libutils/include', 'libs/nativewindow/include', 'libs/arect/include', 'frameworks-native/include',
         'libhardware/include_all', 'libsync/include'])]
    vk_headers = Path('/home/tv/.cache/archtv/aosp16-qpr2/software-renderer-study-1/frameworks-native/vulkan/include')
    assert (vk_headers / 'hardware/hwvulkan.h').is_file()
    core_text = (SOURCE / 'src/Android.bp').read_text()
    core = lambda name: recipe.module(core_text, name)
    root_defaults = recipe.module((SOURCE / 'Android.bp').read_text(), 'swiftshader_common')
    llvm_defaults = core('libswiftshadervk_llvm_defaults')
    driver = core('libvk_swiftshader_common_defaults')
    android_defaults = core('libvk_swiftshader_defaults')
    groups = [
        ('debug', SOURCE / 'src', [core('swiftshader_debug')]),
        ('marl', SOURCE / 'third_party/marl', [recipe.module((SOURCE / 'third_party/marl/Android.bp').read_text(), 'swiftshader_marl')]),
        ('astc', SOURCE / 'third_party/astc-encoder', [recipe.module((SOURCE / 'third_party/astc-encoder/Android.bp').read_text(), 'swiftshader_astc')]),
        ('spirv', SOURCE / 'third_party/SPIRV-Tools', [recipe.module((SOURCE / 'third_party/SPIRV-Tools/Android.bp').read_text(), 'swiftshader_spirv-tools')]),
        ('reactor', SOURCE / 'src', [llvm_defaults]),
        ('driver', SOURCE / 'src', [root_defaults, android_defaults, driver]),
    ]
    includes = [SOURCE / p for p in ['src', 'src/Vulkan', 'include', 'third_party/marl/include',
        'third_party/astc-encoder/Source', 'third_party/SPIRV-Tools/include',
        'third_party/SPIRV-Headers/include', 'third_party/SPIRV-Headers/include/spirv/unified1']]
    extra = ['-I' + str(p) for p in [*includes, generated, vk_headers]] + native
    rules = ['rule compile', '  command = prlimit --as=1073741824 --cpu=180 -- $compiler $flags -MMD -MF $out.d -c $in -o $out',
             '  depfile = $out.d', '  deps = gcc', '  description = SWIFTSHADER $in',
             'rule archive', '  command = /usr/bin/llvm-ar rcs $out @$out.rsp',
             '  rspfile = $out.rsp', '  rspfile_content = $in']
    records = []
    archives = []
    for group, directory, modules in groups:
        sources, flags, local = [], [], []
        for original in modules:
            for selected in [original, original.get('arch', {}).get('x86_64', {}), original.get('target', {}).get('android', {})]:
                sources += selected.get('srcs', [])
                flags += selected.get('cflags', []) + selected.get('cppflags', [])
                local += ['-I' + str(directory / p) for p in selected.get('local_include_dirs', []) + selected.get('export_include_dirs', [])]
        selected_sources = []
        for pattern in sources:
            matches = sorted(directory.glob(pattern))
            assert matches, (group, pattern)
            selected_sources += matches
        assert len(selected_sources) == len(set(selected_sources)), group
        objects = []
        for source in selected_sources:
            obj = out / (group + '__' + str(source.relative_to(directory)).replace('/', '__') + '.o')
            actual_flags = base_flags + extra + ['-I' + str(directory)] + local + flags
            if group == 'reactor':
                actual_flags += llvm_includes
            if source.suffix in ['.c', '.S']:
                actual_flags = [f for f in actual_flags if f not in ['-std=c++17', '-fno-exceptions', '-fno-rtti', '-nostdinc++']]
                if source.suffix == '.c':
                    actual_flags += ['-std=c11']
            records.append({'group': group, 'source': str(source),
                'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
                'object': str(obj), 'argv': [compiler, *actual_flags, '-c', str(source), '-o', str(obj)]})
            rules += [f'build {obj}: compile {source}', '  compiler = ' + shlex.quote(compiler),
                      '  flags = ' + shlex.join(actual_flags).replace('$', '$$')]
            objects.append(str(obj))
        archive = out / ('libswiftshader-' + group + '.a')
        rules += ['build ' + str(archive) + ': archive ' + ' '.join(objects)]
        archives.append(str(archive))
    rules += ['build native-modules: phony ' + ' '.join(archives), 'default native-modules']
    (out / 'build.ninja').write_text('\n'.join(rules) + '\n')
    (out / 'inputs.json').write_text(json.dumps({'revision': recipe.REVISION, 'groups': [g[0] for g in groups],
        'sources': records, 'archives': archives, 'scope': 'Whole original Android modules, not final ICD or runtime. Fresh prototype flags and shared-STL consumer profile are not complete Soong/product equivalence.',
        'resource_limits': 'One extra compiler with AS1GiB/CPU180s; concurrent LLVM two compilers each AS2GiB. Total compiler AS ceiling5GiB, leaving host memory; no runtime/security changes.'}, indent=2) + '\n')
    with (out / 'build.log').open('w') as log:
        child = subprocess.Popen(['ninja', '-C', str(out), '-j', '1'], stdout=log, stderr=subprocess.STDOUT)
        (out / 'process.json').write_text(json.dumps({'pid': child.pid, 'status': 'running'}) + '\n')
        code = child.wait()
    (out / 'process.json').write_text(json.dumps({'pid': child.pid, 'status': 'terminal', 'exit': code}) + '\n')
    print('Original native modules', code, out, flush=True)
    raise SystemExit(code)


if __name__ == '__main__':
    main()
