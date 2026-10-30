#!/usr/bin/env python3
"""Build pinned original Skia's Linux host configuration for the ART/HWUI port."""
import argparse
import ast
import hashlib
import json
from pathlib import Path
import subprocess


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--androidfw-sources', type=Path, required=True)
    parser.add_argument('--gn', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--resume', action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    sources, androidfw = args.sources.resolve(), args.androidfw_sources.resolve()
    skia = sources/'skia'
    manifests = {}
    for name, cache in [('hwui', sources), ('androidfw', androidfw),
                        ('skia-extra', skia/'third_party/externals')]:
        path = root/'runtime/aosp'/(name+'-sources.json')
        manifest = json.loads(path.read_text())
        manifests[name] = digest(path)
        for component in manifest['components']:
            for filename, expected in component['files'].items():
                original = cache/component['name']/filename
                if (not original.is_file() or original.stat().st_size != expected['bytes']
                        or digest(original) != expected['sha256']):
                    raise SystemExit('Original source mismatch: '+str(original))
    gn = args.gn.resolve()
    tool = json.loads((root/'runtime/aosp/skia-gn-tool.json').read_text())
    if digest(gn) != tool['gn_sha256']:
        raise SystemExit('Pinned GN checksum mismatch')
    # Reuse the original host arguments without running gn_to_bp's file writers.
    generator = skia/'gn/gn_to_bp.py'
    function = next(n for n in ast.parse(generator.read_text()).body
                    if isinstance(n, ast.FunctionDef) and n.name == 'generate_args')
    namespace = {}
    exec(compile(ast.Module(body=[function], type_ignores=[]), str(generator), 'exec'), namespace)
    settings = namespace['generate_args']('"linux"', False)
    out = args.output.resolve()
    atomic_header = skia/'third_party/externals/bionic-headers/stdatomic.h'
    compatibility = root/'runtime/aosp/native/skcms-clang-compat.h'
    native_includes = json.loads((root/'runtime/aosp/androidfw-build.json').read_text())['includes']
    settings.update(target_cpu='"x64"', cc='"clang"', cxx='"clang++"',
                    extra_cflags=json.dumps(['-fPIC', '-O1', '-I'+str(skia/'linux'),
                                             '-I'+str(skia/'include/config'),
                                             '-include', str(compatibility),
                                             *['-I'+str(androidfw/p) for p in native_includes]]),
                    extra_cflags_cc=json.dumps(['-nostdinc++', '-isystem', str(androidfw/'libcxx'),
                                                '-I'+str(out/'host-headers')]))
    text = '\n'.join(k+' = '+v for k, v in sorted(settings.items()))+'\n'
    packages = ['ninja', 'pkgconf', 'libwebp', 'libjpeg-turbo', 'libpng', 'freetype2',
                'expat', 'zlib', 'harfbuzz', 'icu']
    package_info = subprocess.run(['pacman', '-Q', *packages], capture_output=True, text=True)
    identity = {'sources': str(sources), 'androidfw_sources': str(androidfw),
                'manifests': manifests, 'gn_sha256': digest(gn), 'args_gn': text,
                'compiler_compatibility_sha256': digest(compatibility),
                'original_bionic_stdatomic_sha256': digest(atomic_header),
                'compiler': subprocess.check_output(['clang++', '--version'], text=True),
                'ninja': subprocess.check_output(['ninja', '--version'], text=True).strip(),
                'system_packages': package_info.stdout, 'package_query_stderr': package_info.stderr}
    out.mkdir(parents=True, exist_ok=args.resume)
    config = out/'configuration.json'
    if args.resume:
        if json.loads(config.read_text()) != identity:
            raise SystemExit('Cannot resume with different sources, tools or configuration')
    else:
        config.write_text(json.dumps(identity, indent=2)+'\n')
    (out/'host-headers').mkdir(exist_ok=args.resume)
    # Export only this original C++ compatibility header, never Bionic's full
    # libc include directory into a glibc build. C sources keep host stdatomic.
    exported_atomic = out/'host-headers/stdatomic.h'
    if not exported_atomic.exists() or digest(exported_atomic) != digest(atomic_header):
        exported_atomic.write_bytes(atomic_header.read_bytes())
    (out/'args.gn').write_text(text)
    with (out/'generate.log').open('w') as log:
        subprocess.run([str(gn), 'gen', str(out)], cwd=skia, stdout=log,
                       stderr=subprocess.STDOUT, check=True, timeout=60)
    with (out/'build.log').open('a' if args.resume else 'w') as log:
        result = subprocess.run(['ninja', '-C', str(out), '-j1', 'skia'],
                                stdout=log, stderr=subprocess.STDOUT)
    libraries = sorted(out.glob('lib*.a'))
    proof = {'build_pass': result.returncode == 0, 'exit_code': result.returncode,
             'scope': 'Original Linux CPU Skia static libraries; HWUI/ART execution and GPU presentation unverified',
             'configuration': identity, 'script_sha256': digest(Path(__file__)),
             'archives': {p.name: digest(p) for p in libraries}, 'build_log_sha256': digest(out/'build.log')}
    (out/'result.json').write_text(json.dumps(proof, indent=2)+'\n')
    print(json.dumps({'build_pass': proof['build_pass'], 'archives': list(proof['archives'])}), flush=True)
    return result.returncode


if __name__ == '__main__':
    raise SystemExit(main())
