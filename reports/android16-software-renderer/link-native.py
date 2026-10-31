#!/usr/bin/env python3
"""Strict-link original Android SwiftShader after both source builds finish."""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import re
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('/home/tv/.cache/archtv/aosp16-qpr2/swiftshader-source-1')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    llvm = ROOT / 'dist/aosp16/swiftshader-llvm16-1'
    native = ROOT / 'dist/aosp16/swiftshader-native-1'
    for directory in [llvm, native]:
        state = json.loads((directory / 'process.json').read_text())
        assert state['status'] == 'terminal' and state['exit'] == 0, (directory, state)
    artifact = json.loads((llvm / 'artifact.json').read_text())
    assert hashlib.sha256(Path(artifact['path']).read_bytes()).hexdigest() == artifact['sha256']
    inputs = json.loads((native / 'inputs.json').read_text())
    for row in inputs['sources']:
        assert hashlib.sha256(Path(row['source']).read_bytes()).hexdigest() == row['source_sha256']
        assert Path(row['object']).is_file()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    lib = out / 'link-libs'
    lib.mkdir()
    original = ROOT / 'dist/aosp16/factory-inputs-3/root'
    spec = importlib.util.spec_from_file_location('audit', ROOT / 'tools/aosp/audit_boot_inputs.py')
    audit = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(audit)
    direct = ['libnativewindow.so', 'libhardware.so', 'libsync.so', 'liblog.so',
              'libcutils.so', 'libc++.so', 'libc.so', 'libm.so', 'libdl.so']
    queue, seen, providers = list(direct), set(), []
    while queue:
        name = queue.pop(0)
        if name in seen:
            continue
        seen.add(name)
        vendor = ROOT / 'dist/aosp16/vendor-native-link-2/vendor/lib64' / name
        logical = ('/apex/com.android.runtime/lib64/bionic/' if name in
                   ['libc.so', 'libm.so', 'libdl.so', 'libdl_android.so'] else '/system/lib64/') + name
        source = vendor if vendor.is_file() else audit.inside(original, logical)
        assert source.is_file(), source
        needed = re.findall(r'\(NEEDED\).*?\[([^]]+)\]', subprocess.check_output(['readelf', '-d', str(source)], text=True))
        queue += needed
        (lib / name).symlink_to(source)
        providers.append({'name': name, 'path': str(source), 'needed': needed,
                          'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    ld = '/home/tv/.cache/archtv/aosp16-qpr2/native-toolchain-1/bin/ld.lld'
    crt = ROOT / 'dist/aosp16/hwc2on1-build-1'
    script = SOURCE / 'src/Vulkan/android_vk_swiftshader.lds'
    target = out / 'vulkan.pastel.so'
    driver_archive = str(native / 'libswiftshader-driver.a')
    support_archives = [a for a in inputs['archives'] if a != driver_archive]
    assert len(support_archives) == 5
    command = [ld, '--no-undefined', '--no-allow-shlib-undefined', '--as-needed',
        '-shared', '--soname=vulkan.pastel.so', '--gc-sections', '-Bsymbolic',
        '--version-script=' + str(script), '-z', 'relro', '-z', 'now',
        '--rpath-link=' + str(lib), str(crt / 'crtbegin_so.c.o'),
        # The original cc_library_shared driver units are direct inputs, not
        # lazy static dependencies. Force their archive members in, then resolve
        # their real dependencies from the remaining original static modules.
        '--start-group', '--whole-archive', driver_archive, '--no-whole-archive',
        *support_archives, artifact['path'], '--end-group',
        '-L' + str(lib), *['-l:' + name for name in direct],
        '/home/tv/.cache/archtv/graphics-candidates-1/compiler-builtins/libclang_rt.builtins-x86_64-android.a',
        str(crt / 'crtend_so.S.o'), '-o', str(target)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=180)
    record = {'argv': command, 'exit': result.returncode, 'stderr': result.stderr,
              'providers': providers, 'export_map_sha256': hashlib.sha256(script.read_bytes()).hexdigest(),
              'scope': 'Strict native linkage only; not loaded ICD, Vulkan device/AHB/draw, SF, MAC or APK acceptance.'}
    if result.returncode == 0:
        record['binary_sha256'] = hashlib.sha256(target.read_bytes()).hexdigest()
        symbols = subprocess.check_output(['readelf', '--dyn-syms', '--wide', str(target)], text=True)
        defined = {fields[7].split('@')[0] for line in symbols.splitlines()
                   if len(fields := line.split()) >= 8 and fields[6] != 'UND'}
        required = {'HMI', 'vk_icdGetInstanceProcAddr', 'vk_icdNegotiateLoaderICDInterfaceVersion',
                    'vk_icdGetPhysicalDeviceProcAddr'}
        record['required_exports'] = sorted(required)
        record['missing_exports'] = sorted(required - defined)
    (out / 'link.json').write_text(json.dumps(record, indent=2) + '\n')
    print('Original SwiftShader Android strict link', result.returncode, out)
    raise SystemExit(result.returncode or (1 if record.get('missing_exports') else 0))


if __name__ == '__main__':
    main()
