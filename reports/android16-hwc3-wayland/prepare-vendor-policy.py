#!/usr/bin/env python3
"""Prepare original graphics vendor TE for composition; never load policy."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[2]
SOURCE = Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/sepolicy/source/system/sepolicy')

# External declarations only. Permissions and transitions below come from the
# original TE/m4 inputs, not from this module's require interface.
REQUIRE = '''module graphics_vendor 1.0;
require {
 attribute domain; attribute file_type; attribute exec_type; attribute vendor_file_type;
 attribute halserverdomain; attribute hal_graphics_allocator_server; attribute hal_graphics_allocator;
 attribute hal_graphics_composer_server; attribute hal_graphics_composer;
 type init; type tmpfs; type unlabeled; type hal_graphics_composer_server_tmpfs;
 role r;
 class file { getattr open read execute map entrypoint write ioctl relabelfrom };
 class process { transition noatsecure siginh rlimitinh };
 class dir search;
}
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    inputs = [SOURCE / name for name in (
        'public/global_macros', 'public/ioctl_defines', 'public/ioctl_macros',
        'public/te_macros', 'vendor/hal_graphics_allocator_default.te',
        'vendor/hal_graphics_composer_default.te')]
    command = ['m4', '-Dtarget_full_treble=true', '-Dtarget_build_variant=user', *map(str, inputs)]
    expanded = subprocess.run(command, capture_output=True, text=True, check=True)
    (out / 'expanded.te').write_text(expanded.stdout)
    (out / 'graphics_vendor.te').write_text(REQUIRE + expanded.stdout +
        '\nrole r types { hal_graphics_allocator_default hal_graphics_composer_default };\n')
    compiler = ROOT / 'dist/aosp16/selinux-tools-host-4/source/checkpolicy/checkmodule'
    argv = [str(compiler), '-m', '-M', '-C', '-o', str(out / 'graphics_vendor.cil'),
            str(out / 'graphics_vendor.te')]
    result = subprocess.run(argv, capture_output=True, text=True)
    record = {'m4': command, 'inputs': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
              'argv': argv, 'compiler_sha256': hashlib.sha256(compiler.read_bytes()).hexdigest(),
              'exit': result.returncode, 'stdout': result.stdout, 'stderr': result.stderr}
    (out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
    result.check_returncode()
    lines = (out / 'graphics_vendor.cil').read_text().splitlines()
    # checkmodule's special linker requirement markers declare no AV rules.
    removed = [line for line in lines if 'cil_gen_require' in line]
    assert all(line.startswith(('(typeattributeset cil_gen_require ',
                                '(roleattributeset cil_gen_require ')) for line in removed)
    (out / 'module-require-metadata.json').write_text(json.dumps(removed, indent=2) + '\n')
    base = ROOT / 'dist/aosp16/factory-inputs-3/root/system/etc/selinux/plat_sepolicy.cil'
    merged = base.read_bytes() + b'\n' + ('\n'.join(line for line in lines if line not in removed) + '\n').encode()
    (out / 'platform-with-vendor.cil').write_bytes(merged)
    profile = json.loads((ROOT / 'reports/android16-hwmanager-cohort/profile.json').read_text())
    assert hashlib.sha256(base.read_bytes()).hexdigest() == profile['input_sha256']['aosp']
    profile['input_sha256']['aosp'] = hashlib.sha256(merged).hexdigest()
    profile['limitations'].append('Original graphics vendor TE added before universe composition; offline only, no runtime or MAC proof.')
    (out / 'profile.json').write_text(json.dumps(profile, indent=2) + '\n')
    print(out)


if __name__ == '__main__':
    main()
