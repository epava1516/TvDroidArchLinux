#!/usr/bin/env python3
"""Compose the entire original audio HAL vendor TE into the verified policy base.

Offline only: no kernel policy load, relabel or enforcing change.
"""
from pathlib import Path
import hashlib
import json
import runpy
import subprocess
import sys

repo = Path(__file__).resolve().parents[2]
out = (repo / sys.argv[1]).resolve()
out.mkdir()
old = runpy.run_path(str(repo / 'reports/android16-hwc3-wayland/prepare-vendor-policy.py'))
source = old['SOURCE']
require = old['REQUIRE'].replace('module graphics_vendor', 'module audio_vendor')
require = require.replace(' role r;', ''' attribute hal_audio; attribute hal_audio_server; attribute halclientdomain;
 attribute hal_allocator; attribute hal_allocator_client; attribute hal_bluetooth; attribute hal_bluetooth_client;
 type hal_bluetooth_service; type fwk_sensor_service; type audioserver;
 class service_manager find; class fifo_file write;
 role r;''')
inputs = [source / p for p in ['public/global_macros', 'public/ioctl_defines', 'public/ioctl_macros',
                              'public/te_macros', 'flagging/flagging_macros', 'vendor/hal_audio_default.te']]
argv = ['m4', '-Dtarget_full_treble=true', '-Dtarget_build_variant=user', '-Dtarget_board_api_level=202504', *map(str, inputs)]
expanded = subprocess.check_output(argv)
te = out / 'audio_vendor.te'
te.write_bytes(require.encode() + expanded + b'\nrole r types hal_audio_default;\n')
compiler = repo / 'dist/aosp16/selinux-tools-host-4/source/checkpolicy/checkmodule'
command = [str(compiler), '-m', '-M', '-C', '-o', str(out / 'audio_vendor.cil'), str(te)]
x = subprocess.run(command, capture_output=True, text=True)
record = {'scope': 'Whole original vendor audio policy, offline only; no invented allows',
          'm4': argv, 'inputs': {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs},
          'argv': command, 'exit': x.returncode, 'stderr': x.stderr}
(out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
print(x.returncode, x.stderr)
x.check_returncode()
lines = (out / 'audio_vendor.cil').read_text().splitlines()
removed = [l for l in lines if 'cil_gen_require' in l]
assert all(l.startswith(('(typeattributeset cil_gen_require ', '(roleattributeset cil_gen_require ')) for l in removed)
base = repo / 'dist/aosp16/gatekeeper-policy-inputs-4/platform-with-vendor.cil'
verified = json.loads((repo / 'dist/aosp16/selected-platform-policy-60/artifact.json').read_text())
assert hashlib.sha256(base.read_bytes()).hexdigest() == verified['input_sha256']['aosp']
merged = base.read_bytes() + b'\n' + ('\n'.join(l for l in lines if l not in removed) + '\n').encode()
(out / 'platform-with-vendor.cil').write_bytes(merged)
profile = json.loads((repo / 'dist/aosp16/gatekeeper-policy-inputs-4/profile.json').read_text())
profile['modules'] = list(verified['modules'])
for name, digest in verified['modules'].items():
    assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest
profile['input_sha256']['aosp'] = hashlib.sha256(merged).hexdigest()
profile['limitations'].append('Original complete vendor/hal_audio_default.te added; no runtime/domain transition/device/isolation acceptance.')
(out / 'profile.json').write_text(json.dumps(profile, indent=2) + '\n')
