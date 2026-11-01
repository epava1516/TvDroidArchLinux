#!/usr/bin/env python3
"""Package the bounded graphics candidate offline; no policy load or startup."""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
CACHE = Path('/home/tv/.cache/archtv/graphics-candidates-1')
out = ROOT / 'dist/aosp16' / sys.argv[1]
assert (out / 'artifacts.json').is_file(), 'Build cohort first'
assert not (out / 'payload.json').exists(), 'Preserve existing artifacts'
vendor = out / ('vendor-inputs-' + (sys.argv[2] if len(sys.argv)>2 else '1'))
vendor.mkdir()
files = {}
surfaceflinger = '--surfaceflinger' in sys.argv[2:]


def add(logical, source, label, mode=0o644):
    assert logical not in files
    files[logical] = {'source': str(source), 'context': 'u:object_r:' + label + ':s0',
                      'mode': mode, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()}


if surfaceflinger:
    properties = vendor / 'build.prop'
    backend = 'skiagl' if '--renderengine-gl' in sys.argv[2:] else 'skiavk'
    properties.write_text('ro.hardware.egl=angle\nro.hardware.vulkan=pastel\ndebug.renderengine.backend=' + backend + '\n')
    add('/vendor/build.prop', properties, 'vendor_file')
    add('/vendor/lib64/hw/vulkan.pastel.so', ROOT / 'dist/aosp16/swiftshader-link-2/vulkan.pastel.so', 'same_process_hal_file')

if '--selected-display' in sys.argv[2:]:
    selected = ROOT / 'dist/aosp16/selected-display-8'
    add('/vendor/framework/archtv-selected-services.jar', selected / 'archtv-selected-services.jar', 'vendor_framework_file')
    add('/vendor/etc/init/archtv-selected-services.rc', selected / 'selected-services.rc', 'vendor_configs_file')

sp = 'same_process_hal_file'
mg = ROOT / 'dist/aosp16/minigbm-native-link-5'
hwc = ROOT / 'dist/aosp16/hwc3-wayland-1'
add('/vendor/bin/hw/android.hardware.graphics.allocator-service.minigbm',
    mg / 'android.hardware.graphics.allocator-service.minigbm', 'hal_graphics_allocator_default_exec', 0o755)
add('/vendor/bin/hw/android.hardware.graphics.composer3-service.ranchu',
    (ROOT / 'dist/aosp16/hwc3-client-diagnostic-1/android.hardware.graphics.composer3-service.archtv-trace' if '--composer-trace' in sys.argv[2:] else hwc / 'android.hardware.graphics.composer3-service.archtv-display-2'), 'hal_graphics_composer_default_exec', 0o755)
# Explicit harness in the original SF client domain, not the original SF binary.
add('/vendor/bin/hw/archtv-graphics-client', out / 'graphics-client', 'surfaceflinger_exec', 0o755)
for name in ['libminigbm_gralloc.so', 'libminigbm_gralloc4_utils.so', 'mapper.minigbm.so']:
    # SP-HAL mapper and its same-process implementation helpers.
    add('/vendor/lib64/' + ('hw/' if name.startswith('mapper.') else '') + name, mg / name, sp)

# Preserve the vendor and sphal isolation/link lists. Copy only non-shared
# native providers; do not turn the vendor namespace into the system namespace.
config = (ROOT / 'dist/aosp16/linux-selinux-handoff-2/linkerconfig-mc1/ld.config.txt').read_text()
section = config.split('[vendor]\n', 1)[1].split('\n[', 1)[0]
shared = set()
for line in section.splitlines():
    if re.match(r'namespace.default.link.[^.]+.shared_libs = ', line):
        shared.update(line.split(' = ', 1)[1].split(':'))
overrides = {p.name: p for p in (ROOT / 'dist/aosp16/vendor-native-link-2/vendor/lib64').glob('*.so')}
overrides['libui.so'] = ROOT / 'dist/aosp16/libui-link-2/libui.so'
overrides['android.hardware.graphics.composer@2.1-resources.so'] = ROOT / 'dist/aosp16/composer-link-1/android.hardware.graphics.composer@2.1-resources.so'
queue = [Path(v['source']) for v in files.values()]
seen = set()
providers = []
while queue:
    source = queue.pop(0)
    if source in seen:
        continue
    seen.add(source)
    if not source.read_bytes().startswith(b'\x7fELF'):
        continue
    needed = re.findall(r'\(NEEDED\).*?\[([^]]+)\]', subprocess.check_output(['readelf', '-d', str(source)], text=True))
    providers.append({'source': str(source), 'needed': needed, 'sha256': hashlib.sha256(source.read_bytes()).hexdigest()})
    for name in needed:
        if name in shared or any(Path(p).name == name for p in files):
            continue
        candidate = overrides.get(name)
        if candidate is None:
            for directory in [hwc.parent / 'hwc3-frontend-2/link-libs', mg / 'link-libs']:
                if (directory / name).is_file():
                    candidate = (directory / name).resolve()
                    break
        if candidate is None:
            original = ROOT / 'dist/aosp16/factory-inputs-3/root/system/lib64' / name
            if original.is_file():
                candidate = original.resolve()
        assert candidate is not None and candidate.is_file(), ('missing real provider', name)
        # This diagnostic candidate admits concrete original providers, with
        # their variant provenance retained. Runtime namespace/ABI tests remain
        # required; copying does not establish source-build equivalence.
        add('/vendor/lib64/' + name, candidate, sp)
        queue.append(candidate)

needed_by_name = {Path(p['source']).name: p['needed'] for p in providers}
mapper_closure = set()
pending = ['mapper.minigbm.so'] + (['vulkan.pastel.so'] if surfaceflinger else [])
while pending:
    name = pending.pop()
    if name in mapper_closure or name in shared:
        continue
    mapper_closure.add(name)
    pending.extend(needed_by_name.get(name, []))
for logical, entry in files.items():
    if logical.startswith('/vendor/lib64/'):
        entry['context'] = 'u:object_r:' + (sp if Path(logical).name in mapper_closure else 'vendor_file') + ':s0'

for logical, source in [
    ('/vendor/etc/selinux/plat_sepolicy_vers.txt', ROOT / 'dist/aosp16/linux-failure-sink-worker-1/vendor/etc/selinux/plat_sepolicy_vers.txt'),
    ('/vendor/etc/init/allocator.rc', CACHE / 'minigbm/cros_gralloc/aidl/allocator.rc'),
    ('/vendor/etc/init/hwcomposer3.rc', CACHE / 'goldfish-hwc3/hwc3.rc'),
    ('/vendor/etc/vintf/manifest/allocator.xml', CACHE / 'minigbm/cros_gralloc/aidl/allocator.xml'),
    ('/vendor/etc/vintf/manifest/composer.xml', CACHE / 'goldfish-hwc3/hwc3.xml'),
    ('/vendor/etc/vintf/manifest/mapper.xml', CACHE / 'minigbm/cros_gralloc/mapper_stablec/mapper.minigbm.xml'),
    ('/vendor/etc/vintf/manifest.xml', ROOT / 'reports/android16-hwmanager-cohort/diagnostic-vintf-profile/manifest.xml'),
    ('/vendor/etc/vintf/compatibility_matrix.xml', ROOT / 'reports/android16-hwmanager-cohort/diagnostic-vintf-profile/compatibility_matrix.xml'),
]:
    add(logical, source, 'vendor_configs_file')
# Concrete path adaptations required by these original RCs. No AV rules here.
contexts = vendor / 'vendor_file_contexts'
contexts.write_text('\n'.join(re.escape(p) + ' ' + v['context'] for p,v in files.items()) + '\n')
add('/vendor/etc/selinux/vendor_file_contexts', contexts, 'file_contexts_file')
(out / 'vendor-inputs.json').write_text(json.dumps({'files': files, 'providers': providers,
    'shared_names': sorted(shared), 'linkerconfig_sha256': hashlib.sha256(config.encode()).hexdigest(),
    'limitations': ['Experimental provider selection, not full Soong/vendor product equivalence.',
                    'SP-HAL labels limited to ELF mapper/selected Vulkan driver dependency closure; loader/runtime and enforcing access still untested.',
                    'Harness surfaceflinger_exec explicitly does not identify an original SurfaceFlinger binary.',
                    'No namespace, driver, GPU isolation, registration, buffer or timing acceptance by packaging.']}, indent=2) + '\n')

# Reuse the existing image/EA/hash/e2fsck implementation, materializing the
# expanded exact recipe rather than maintaining another image platform.
base = (ROOT / 'reports/android16-hwmanager-cohort/build-payload-descriptor.py').read_text()
base = base.replace("out=r/'dist/aosp16/hwmanager-cohort-4'", 'out=Path(' + repr(str(out)) + ')')
base = base.replace("out/'cargo/debug/examples/native_supervisor'", "r/'dist/aosp16/hwmanager-cohort-4/cargo/debug/examples/native_supervisor'")
injection = '''
vendor_files=json.loads((out/'vendor-inputs.json').read_text())['files']
for path, entry in vendor_files.items():
 for parent in reversed((tree/path.lstrip('/')).parents):
  if parent==tree or tree not in parent.parents:continue
  if not parent.exists():
   parent.mkdir(mode=0o755)
   record('/'+str(parent.relative_to(tree)),None,'u:object_r:vendor_file:s0',0o755)
 record(path,Path(entry['source']),entry['context'],entry['mode'])
'''
assert base.count("image=out/'payload-2.ext4'") == 1
base = base.replace("image=out/'payload-2.ext4'", injection + "\nimage=out/'payload-2.ext4'")
base = base.replace("str(image),'32M'", "str(image),'128M'")
base = base.replace("(d/'payload-descriptor.json')", "(out/'payload.json')")
# Original recorder assumes every directory is 0700; use each recorded mode.
base = base.replace("'040700' if not entry['source']", "('0'+format(0o040000|int(entry['mode'],8),'o')) if not entry['source']")
recipe = out / 'build-payload-expanded.py'
recipe.write_text(base)
subprocess.run([sys.executable, str(recipe)], check=True)
print(out / 'payload.json')
