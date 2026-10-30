#!/usr/bin/env python3
"""Compile original HWUI translation units; this does not link a graphics runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--sources', type=Path, required=True)
    parser.add_argument('--androidfw-sources', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    parser.add_argument('--unit', action='append', help='Original HWUI .cpp path; repeatable')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    sources = args.sources.resolve()
    androidfw = args.androidfw_sources.resolve()
    units = args.unit or ['RenderNode.cpp', 'jni/android_graphics_RenderNode.cpp']
    manifests = {}
    verified_files = 0
    for name, cache in [('hwui', sources), ('androidfw', androidfw)]:
        manifest_path = root/'runtime/aosp'/(name+'-sources.json')
        manifest = json.loads(manifest_path.read_text())
        manifests[name] = {'path': str(manifest_path), 'sha256': sha256(manifest_path)}
        for component in manifest['components']:
            for filename, expected in component['files'].items():
                path = cache/component['name']/filename
                if (not path.is_file() or path.stat().st_size != expected['bytes']
                        or sha256(path) != expected['sha256']):
                    raise SystemExit('Original source mismatch: '+str(path))
                verified_files += 1
    original = json.loads((root/'runtime/aosp/hwui-sources.json').read_text())
    files = next(c['files'] for c in original['components'] if c['name'] == 'hwui')
    if len(set(units)) != len(units) or any(u not in files or not u.endswith('.cpp') for u in units):
        raise SystemExit('Units must be distinct pinned original HWUI C++ sources')
    recipe = json.loads((root/'runtime/aosp/androidfw-build.json').read_text())
    include_paths = [androidfw/p for p in recipe['includes']]
    include_paths += [sources/p for p in ['hwui', 'hwui/jni', 'skia', 'skia/linux',
                                        'skia/src/codec', 'skia/src/core', 'skia/src/effects',
                                        'skia/src/image', 'skia/src/images',
                                        'skia/client_utils/android',
                                        'nativehelper/include', 'nativehelper/include_platform',
                                        'nativehelper/header_only_include', 'nativehelper/include_jni',
                                        'minikin/include', 'harfbuzz',
                                        'ui-headers', 'gui-headers', 'vulkan-headers']]
    include_paths += sorted(p for p in (sources/'skia/include').iterdir() if p.is_dir())
    # Match ART's libc++ headers used by the existing native resource port.
    # C++20 supports the bitfield initializers in the original HWUI sources.
    common = ['clang++', '-std=gnu++20', '-nostdinc++', '-isystem', str(androidfw/'libcxx'),
              '-fPIC', '-O0', '-g0', '-DSTATIC_ANDROIDFW_FOR_TOOLS', '-DFMT_HEADER_ONLY',
              '-DNDEBUG', *['-I'+str(p) for p in include_paths]]
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    results = []
    for index, unit in enumerate(units):
        target = out/(str(index)+'.o')
        command = [*common, '-c', str(sources/'hwui'/unit), '-o', str(target)]
        log = out/(str(index)+'.stderr')
        with log.open('w') as stream:
            result = subprocess.run(command, stdout=stream, stderr=subprocess.STDOUT, timeout=180)
        entry = {'unit': unit, 'command': command, 'exit_code': result.returncode,
                 'log': log.name, 'log_sha256': sha256(log)}
        if result.returncode == 0:
            entry['object_sha256'] = sha256(target)
            symbols = subprocess.check_output(['nm', '-C', '--undefined-only', str(target)], text=True)
            (out/(str(index)+'.undefined.txt')).write_text(symbols)
        results.append(entry)
        print(unit+': '+('compiled' if result.returncode == 0 else 'failed; see '+str(log)), flush=True)
    passed = all(entry['exit_code'] == 0 for entry in results)
    (out/'result.json').write_text(json.dumps({
        'all_requested_units_compiled': passed, 'linked': False, 'executed': False,
        'scope': 'Original translation-unit compilation only; no RenderNode JNI execution or drawing claim',
        'verified_original_files': verified_files, 'manifests': manifests,
        'compiler': subprocess.check_output(['clang++', '--version'], text=True),
        'probe_sha256': sha256(Path(__file__)), 'results': results,
    }, indent=2)+'\n')
    return 0 if passed else 1


if __name__ == '__main__':
    raise SystemExit(main())
