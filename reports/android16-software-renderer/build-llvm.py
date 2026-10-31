#!/usr/bin/env python3
"""Build the complete original SwiftShader Android LLVM16 module, offline only."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shlex
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('/home/tv/.cache/archtv/aosp16-qpr2/swiftshader-source-1')
REVISION = 'd70203d9df3c70c4fc63fb29325d24e9c12dc43f'


def module(text, name):
    # This pinned file contains literal properties only. Preserve quoted //
    # visibility paths while removing actual comments, then select one module.
    text = re.sub(r'"(?:\\.|[^"\\])*"|//[^\n]*|/\*[\s\S]*?\*/',
                  lambda m: m[0] if m[0].startswith('"') else '', text)
    position = text.index('name: "' + name + '"')
    start = text.rfind('{', 0, position)
    tokens = list(re.finditer(r'"(?:\\.|[^"\\])*"|[{}]', text[start:]))
    depth = 0
    for token in tokens:
        if token[0] == '{':
            depth += 1
        elif token[0] == '}':
            depth -= 1
            if depth == 0:
                body = text[start:start+token.end()]
                body = re.sub(r'([,{]\s*)([A-Za-z_]\w*)\s*:', r'\1"\2":', body)
                return json.loads(re.sub(r',\s*([}\]])', r'\1', body))
    raise ValueError('Unbalanced original module')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--jobs', type=int, default=2, choices=[1, 2])
    args = parser.parse_args()
    assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == REVISION
    subprocess.run(['git', '-C', str(SOURCE), 'diff', '--quiet', 'HEAD', '--', '.'], check=True)
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    llvm = SOURCE / 'third_party/llvm-16.0'
    blueprint = llvm / 'Android.bp'
    selected = module(blueprint.read_text(), 'libLLVM16_swiftshader_defaults')
    sources = selected['srcs'] + selected['arch']['x86_64']['srcs']
    assert len(sources) == len(set(sources)) and len(sources) > 500
    previous = json.loads((ROOT / 'reports/android16-hwc3-frontend/build.json').read_text())['results'][0]['argv']
    system_includes = []
    for i, flag in enumerate(previous):
        if flag == '-isystem':
            system_includes += [flag, previous[i+1]]
    assert system_includes and any('libcxx' in f or 'libc++' in f for f in system_includes)
    common = ['--target=x86_64-linux-android36', '-nostdinc', '-nostdinc++',
              *system_includes, '-fPIC', '-O2', '-g0', '-DNDEBUG', '-DANDROID',
              '-D__ANDROID_VENDOR__', '-ffunction-sections', '-fdata-sections',
              '-fstack-protector-strong', '-D_FORTIFY_SOURCE=2']
    includes = ['-I' + str(llvm / p) for p in selected['local_include_dirs'] + selected['export_include_dirs']]
    compiler = previous[0]
    records = []
    ninja = ['rule compile', '  command = prlimit --as=2147483648 --cpu=180 -- $compiler $flags -MMD -MF $out.d -c $in -o $out',
             '  depfile = $out.d', '  deps = gcc', '  description = LLVM16 $in',
             'rule archive', '  command = /usr/bin/llvm-ar rcs $out @$out.rsp',
             '  rspfile = $out.rsp', '  rspfile_content = $in']
    objects = []
    for name in sources:
        path = llvm / name
        assert path.is_file(), path
        obj = out / (name.replace('/', '__') + '.o')
        cpp = path.suffix != '.c'
        flags = common + (['-std=c++17', '-fno-exceptions', '-fno-rtti'] if cpp else ['-std=c11']) + includes + selected['cflags']
        if not cpp:
            flags.remove('-nostdinc++')
        record = {'source': str(path), 'source_sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                  'object': str(obj), 'argv': [compiler, *flags, '-c', str(path), '-o', str(obj)]}
        records.append(record)
        ninja += [f'build {obj}: compile {path}', '  compiler = ' + shlex.quote(compiler),
                  '  flags = ' + shlex.join(flags).replace('$', '$$')]
        objects.append(str(obj))
    archive = out / 'libLLVM16_swiftshader.a'
    ninja += ['build ' + str(archive) + ': archive ' + ' '.join(objects), 'default ' + str(archive)]
    (out / 'build.ninja').write_text('\n'.join(ninja) + '\n')
    state = {'source_revision': REVISION, 'module': selected['name'],
             'blueprint_sha256': hashlib.sha256(blueprint.read_bytes()).hexdigest(),
             'compiler_sha256': hashlib.sha256(Path(compiler).read_bytes()).hexdigest(),
             'sources': records, 'jobs': args.jobs,
             'scope': 'Complete Android x86_64 LLVM16 static module only; not SwiftShader ICD, RenderEngine, SurfaceFlinger or APK acceptance. Prototype flags, not complete Soong equivalence.'}
    (out / 'inputs.json').write_text(json.dumps(state, indent=2) + '\n')
    with (out / 'build.log').open('w') as log:
        child = subprocess.Popen(['ninja', '-C', str(out), '-j', str(args.jobs)], stdout=log, stderr=subprocess.STDOUT)
        (out / 'process.json').write_text(json.dumps({'pid': child.pid, 'status': 'running', 'ninja_log': str(out / 'build.log')}) + '\n')
        code = child.wait()
    (out / 'process.json').write_text(json.dumps({'pid': child.pid, 'status': 'terminal', 'exit': code}) + '\n')
    if code == 0:
        (out / 'artifact.json').write_text(json.dumps({'path': str(archive), 'sha256': hashlib.sha256(archive.read_bytes()).hexdigest(), 'units': len(records)}, indent=2) + '\n')
    print('LLVM16 build', code, out, flush=True)
    raise SystemExit(code)


if __name__ == '__main__':
    main()
