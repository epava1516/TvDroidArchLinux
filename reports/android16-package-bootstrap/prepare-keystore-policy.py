#!/usr/bin/env python3
"""Add the entire pinned original KeyMint vendor TE to the existing vendor set.

Offline composition only. Does not load policy or change enforcing.
"""
from pathlib import Path
import hashlib
import json
import runpy
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
out = (ROOT / sys.argv[1]).resolve()
out.mkdir()
old = runpy.run_path(str(ROOT / 'reports/android16-hwc3-wayland/prepare-vendor-policy.py'))
source = old['SOURCE']
require = old['REQUIRE'].replace('module graphics_vendor', 'module vendor')
require = require.replace(' attribute halserverdomain;',
    ' attribute bpfdomain; attribute hal_health; attribute hal_health_server;'
    ' attribute hal_keymint; attribute hal_keymint_server; attribute hal_keymint_client; attribute halserverdomain;')
require = require.replace(' type init;',
    ' type charger_vendor; type hal_health_server_tmpfs; type hal_secureclock_service;'
    ' type hal_sharedsecret_service; type vendor_security_patch_level_prop; type atrace; type dumpstate; type shell; type system_app; type traceur_app; type init;')
require = require.replace(' class dir search;', ' class dir search; class service_manager { add find };')
inputs = [source / name for name in (
    'public/global_macros', 'public/ioctl_defines', 'public/ioctl_macros',
    'public/te_macros', 'flagging/flagging_macros',
    'vendor/hal_graphics_allocator_default.te', 'vendor/hal_graphics_composer_default.te',
    'vendor/hal_health_default.te', 'vendor/hal_keymint_default.te')]
# Explicit Linux policy compatibility profile for the pinned public 202504 API.
# This is not a hardware/firmware certification or a claimed vendor patch date.
argv = ['m4', '-Dtarget_full_treble=true', '-Dtarget_build_variant=user',
        '-Dtarget_board_api_level=202504', *map(str, inputs)]
expanded = subprocess.check_output(argv, text=True)
te = out / 'vendor.te'
te.write_text(require + expanded + '\nrole r types { hal_keymint_default hal_health_default '
              'hal_graphics_allocator_default hal_graphics_composer_default };\n')
compiler = ROOT / 'dist/aosp16/selinux-tools-host-4/source/checkpolicy/checkmodule'
cmd = [str(compiler), '-m', '-M', '-C', '-o', str(out / 'vendor.cil'), str(te)]
result = subprocess.run(cmd, capture_output=True, text=True)
record = {'m4': argv, 'inputs': {str(f): hashlib.sha256(f.read_bytes()).hexdigest() for f in inputs},
          'argv': cmd, 'exit': result.returncode, 'stderr': result.stderr,
          'scope': 'Entire original vendor TE, no invented allows. Offline, not MAC or service acceptance.'}
(out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
result.check_returncode()
lines = (out / 'vendor.cil').read_text().splitlines()
removed = [line for line in lines if 'cil_gen_require' in line]
assert all(line.startswith(('(typeattributeset cil_gen_require ', '(roleattributeset cil_gen_require ')) for line in removed)
base = ROOT / 'dist/aosp16/factory-inputs-3/root/system/etc/selinux/plat_sepolicy.cil'
merged = base.read_bytes() + b'\n' + ('\n'.join(line for line in lines if line not in removed) + '\n').encode()
(out / 'platform-with-vendor.cil').write_bytes(merged)
profile = json.loads((ROOT / 'reports/android16-hwmanager-cohort/profile.json').read_text())
assert hashlib.sha256(base.read_bytes()).hexdigest() == profile['input_sha256']['aosp']
profile['input_sha256']['aosp'] = hashlib.sha256(merged).hexdigest()
profile['limitations'].append('Original KeyMint vendor TE composed offline; no policy load, service or MAC acceptance.')
(out / 'profile.json').write_text(json.dumps(profile, indent=2) + '\n')
