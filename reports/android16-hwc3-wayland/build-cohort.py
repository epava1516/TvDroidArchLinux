#!/usr/bin/env python3
"""Build experimental original-service cohort and API client; never execute it."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess

ROOT = Path(__file__).resolve().parents[2]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    records = []

    def execute(argv):
        result = subprocess.run(argv, capture_output=True, text=True, timeout=180)
        records.append({'argv': argv, 'exit': result.returncode, 'stderr': result.stderr})
        (out / 'build.json').write_text(json.dumps({'commands': records,
            'scope': 'Build only, no services, MAC, graphics or APK acceptance'}, indent=2) + '\n')
        print('BUILD', Path(argv[-1]).name, result.returncode, result.stderr[-2500:], flush=True)
        result.check_returncode()

    # Linux/glibc supervisor runs from the explicit private /archtv closure,
    # never through the Android/Bionic linker or a host /lib64 symlink.
    execute(['/usr/bin/env', 'CARGO_TARGET_DIR=' + str(out / 'cargo'),
             'cargo', 'rustc', '-p', 'archtv-core', '--example', 'native_supervisor', '--',
             '-C', 'link-arg=-Wl,--dynamic-linker=/archtv/lib/ld-linux-x86-64.so.2',
             '-C', 'link-arg=-Wl,-rpath,/archtv/lib'])

    old = json.loads((ROOT / 'reports/android16-hwmanager-cohort/worker-descriptor-build.json').read_text())
    worker = list(old[0]['argv'])
    previous_object = worker[worker.index('-o') + 1]
    worker[worker.index('-o') + 1] = str(out / 'worker.o')
    execute(worker)
    link = [str(out / 'worker.o') if a == previous_object else a for a in old[1]['argv']]
    link[link.index('-o') + 1] = str(out / 'property-coordinator')
    execute(link)
    helper = json.loads((ROOT / 'reports/android16-hwmanager-cohort/helper-build.json').read_text())['argv']
    helper[helper.index('-o') + 1] = str(out / 'linux-exec-context-image')
    execute(helper)
    hwc = ROOT / 'dist/aosp16/hwc3-wayland-1'
    build = json.loads((hwc / 'build.json').read_text())
    flags = list(build['commands'][0]['argv'])
    flags = flags[:flags.index('-MMD')]
    source = ROOT / 'runtime/aosp/native/linux-graphics-client.cpp'
    execute(flags + ['-c', str(source), '-o', str(out / 'graphics-client.o')])
    link = json.loads((hwc / 'link.json').read_text())['argv']
    # Reuse the exact native-provider closure, not the HWC implementation/main.
    link = [a for a in link if not (a.endswith('.o') and
        (a.startswith(str(hwc)) or a.endswith('/wayland-output-3/xdg.o')))
        and not a.endswith('/libwayland-client-bionic.a')]
    link[link.index('-o') + 1] = str(out / 'graphics-client')
    link.insert(1, '--as-needed')
    link.insert(link.index('-o'), '-l:android.hardware.graphics.allocator-V2-ndk.so')
    link.insert(next(i for i,a in enumerate(link) if a.endswith('/NativeHandle.o')), str(out / 'graphics-client.o'))
    execute(link)
    supervisor = out / 'cargo/debug/examples/native_supervisor'
    elf_headers = subprocess.check_output(['readelf', '-l', str(supervisor)], text=True)
    assert '[Requesting program interpreter: /archtv/lib/ld-linux-x86-64.so.2]' in elf_headers
    inventory = {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                 for name in ['property-coordinator', 'linux-exec-context-image', 'graphics-client', 'cargo/debug/examples/native_supervisor']}
    (out / 'artifacts.json').write_text(json.dumps(inventory, indent=2) + '\n')


if __name__ == '__main__':
    main()
