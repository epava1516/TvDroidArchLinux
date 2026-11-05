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
with_memory = '--memory' in sys.argv[2:]
if with_memory:
    inputs.append(repo / 'runtime/aosp/android16-qpr2/policy/experiments/audio-tmpfs.te')
    argv.append(str(inputs[-1]))
expanded = subprocess.check_output(argv)
te = out / 'audio_vendor.te'
te.write_bytes(require.encode() + expanded + b'\nrole r types hal_audio_default;\n')
compiler = repo / 'dist/aosp16/selinux-tools-host-4/source/checkpolicy/checkmodule'
command = [str(compiler), '-m', '-M', '-C', '-o', str(out / 'audio_vendor.cil'), str(te)]
x = subprocess.run(command, capture_output=True, text=True)
record = {'scope': ('Whole original vendor audio policy plus explicit Linux private-memory adaptation via original tmpfs_domain macro' if with_memory else 'Whole original vendor audio policy, offline only; no invented allows'),
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
if with_memory:
    profile['modules'] += ['runtime/aosp/android16-qpr2/policy/experiments/audio-nnp.cil',
                           'runtime/aosp/android16-qpr2/policy/experiments/audio-tmpfs.cil']
    profile['limitations'].append('Explicit Linux private-memory file_type and original tmpfs_domain macro; projected transition requires real memfd/output testing. Original vendor audio TE itself lacks this private type. No generic Linux tmpfs write or app/execute access granted.')
for name, digest in verified['modules'].items():
    assert hashlib.sha256((repo / name).read_bytes()).hexdigest() == digest
if '--vold-private-bind' in sys.argv[2:]:
    assert with_memory, 'Retain verified audio63 base for the private-bind candidate'
    profile['modules'].append('runtime/aosp/android16-qpr2/policy/experiments/vold-private-bind-unmount.cil')
    profile['limitations'].append('Exact original vold UnmountTree need on Linux-backed private bind. Filesystem SID is GLOBAL; detached private root/mount/PID namespaces remain mandatory. No new file/proc/namespace/capability or mount/remount access. Offline only, R1 remains open.')
if '--artd-subprocess-nnp' in sys.argv[2:]:
    assert with_memory and '--vold-private-bind' in sys.argv[2:], 'Preserve the complete verified policy64 base'
    profile['modules'].append('runtime/aosp/android16-qpr2/policy/experiments/artd-subprocess-nnp.cil')
    profile['limitations'].append('Only the extra inherited NNP admission for the closed original artd_subprocess_type set. Original domain_auto_trans/entrypoints/credentials remain mandatory and execute_no_trans remains denied. Offline only; actual compiler identities, operation and R1/APK acceptance require real execution.')
if '--original-art-boot-nnp' in sys.argv[2:]:
    assert '--artd-subprocess-nnp' in sys.argv[2:], 'Preserve the complete policy65 base'
    profile['modules'].append('runtime/aosp/android16-qpr2/policy/experiments/art-boot-nnp.cil')
    profile['limitations'].append('Only inherited NNP admission on original init->art_boot, init->odsign, odsign->odrefresh and odrefresh->dex2oat transitions. No new transition/entrypoint/execute_no_trans permission; actual signature/cache/image/R1 tests remain mandatory.')
if '--original-art-sign-nosuid' in sys.argv[2:]:
    assert '--original-art-boot-nnp' in sys.argv[2:], 'Preserve the complete policy66 base'
    profile['modules'].append('runtime/aosp/android16-qpr2/policy/experiments/art-sign-nosuid.cil')
    profile['limitations'].append('Only init->odsign nosuid label-transition admission for the explicitly private nosuid executable bind. Nosuid mount/NNP1 and original entrypoint/UID/capabilities retained; no execute_no_trans or file/device/Binder/capability grant. Actual cryptography/cache/image/R1 remains unproven.')
if '--original-aconfig-identity-read' in sys.argv[2:]:
    assert '--original-art-sign-nosuid' in sys.argv[2:], 'Preserve the complete policy67 base'
    profile['modules'].append('runtime/aosp/android16-qpr2/policy/experiments/aconfig-identity-read.cil')
    profile['limitations'].append('Only original init process:getattr for the two short-lived aconfig domains missing kernel SID witnesses in344. No Linux observer, ptrace, signal, transition or file-write widening. Offline compilation is not an actual identity observation or R1 acceptance.')
profile['input_sha256']['aosp'] = hashlib.sha256(merged).hexdigest()
profile['limitations'].append('Original complete vendor/hal_audio_default.te added; no runtime/domain transition/device/isolation acceptance.')
(out / 'profile.json').write_text(json.dumps(profile, indent=2) + '\n')
