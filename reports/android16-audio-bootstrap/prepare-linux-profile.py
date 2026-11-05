#!/usr/bin/env python3
"""Add verified original audio artifacts and a PCM-only Linux device profile.

Configuration is a candidate, not service inventory or hardware acceptance.
Does not touch the host's devices, mixer, policy or running processes.
"""
from pathlib import Path
import hashlib
import json
import os
import re
import subprocess
import sys
import xml.etree.ElementTree as ET

repo = Path(__file__).resolve().parents[2]
out = (repo / sys.argv[1]).resolve()
path = out / 'vendor-inputs.json'
vendor = json.loads(path.read_text())
study = Path('/home/tv/.cache/archtv/aosp16-qpr2/audio-original-study-1')
root = repo / 'dist/aosp16/factory-inputs-3/root'
write_diagnostic = '--audio-write-diagnostic' in sys.argv[2:]
synchronous_pcm = '--audio-synchronous-pcm' in sys.argv[2:]
production_dynamics = '--audio-production-dynamics' in sys.argv[2:]
assert not (write_diagnostic and synchronous_pcm), 'Choose one audio backend candidate'
core = repo / ('dist/aosp16/audio-linux-core-link-8' if synchronous_pcm else
               'dist/aosp16/audio-linux-core-link-5' if write_diagnostic else
               'dist/aosp16/audio-linux-core-link-3')
effect = repo / 'dist/aosp16/audio-effect-link-2'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
record = {'scope': 'Private original audio deployment candidate, not service or PCM acceptance',
          'files': {}, 'adaptations': []}
record['write_diagnostic'] = write_diagnostic
record['synchronous_pcm'] = synchronous_pcm
record['production_dynamics'] = production_dynamics
if synchronous_pcm:
    record['adaptations'].append('Candidate attached single-device blocking PCM removes reference lossy MonoPipe, counts actual TinyALSA writes and propagates errors. Real drain/flush, pause explicitly unsupported. No runtime/continuity/clock/acoustic acceptance.')
if write_diagnostic:
    record['adaptations'].append('Original StreamAlsa logs opened config and failure errno/pcm_get_error only; transfer/return/retry behavior unchanged. This is not an audio correction or PCM acceptance.')
for parent, executable in [(core, 'android.hardware.audio.service-aidl.example'),
                           (effect, 'android.hardware.audio.effect.service-aidl.example')]:
    link = json.loads((parent / 'link.json').read_text())
    assert sha(parent / executable) == link['binary_sha256']
    for src, expected in link['inputs'].items():
        assert sha(Path(src)) == expected, src

def add(target, source, context='vendor_configs_file', mode=0o444):
    assert target not in vendor['files'], target
    vendor['files'][target] = {'source': str(source), 'context': 'u:object_r:' + context + ':s0', 'mode': mode}
    record['files'][target] = {'source': str(source), 'sha256': sha(source)}

# The HAL's vendor namespace uses its own libcutils. Keep the vendor build,
# source-selected LLNDK boundary and SP-HAL file type; never substitute platform.
memory = repo / 'dist/aosp16/vendor-libcutils-memory-3'
memory_build = json.loads((memory / 'build.json').read_text())
assert memory_build['terminal'] and not memory_build['export_comparison']['missing']
assert sha(memory / 'libcutils.so') == memory_build['sha256']
for source, expected in memory_build['inputs'].items():
    assert sha(Path(source)) == expected, source
vendor_memory = vendor['files']['/vendor/lib64/libcutils.so']
record['vendor_memory_previous'] = dict(vendor_memory)
vendor_memory['source'] = str(memory / 'libcutils.so')
record['files']['/vendor/lib64/libcutils.so'] = {'source': vendor_memory['source'], 'sha256': memory_build['sha256']}
record['adaptations'].append('Original vendor libcutils retained with explicit original memfd-label backport; 130 export identities unchanged. Runtime FMQ transfer, policy access and graphics regression remain unproved.')

binaries = ['android.hardware.audio.service-aidl.example', 'android.hardware.audio.effect.service-aidl.example']
for parent, name in zip([core, effect], binaries):
    add('/vendor/bin/hw/' + name, parent / name, 'hal_audio_default_exec', 0o755)
original_rc = study / 'hardware-audio/aidl/default/android.hardware.audio.service-aidl.example.rc'
rc = out / 'audio-original-linux.rc'
text = original_rc.read_text()
assert text.count('/apex/com.android.hardware.audio/bin/hw/') == 2
rc.write_text(text.replace('/apex/com.android.hardware.audio/bin/hw/', '/vendor/bin/hw/') + '\n')
add('/vendor/etc/init/archtv-audio.rc', rc)
# The original AIDL factory searches this exact filename; legacy GSI
# audio_effects.xml is a different deployment input. Keep original declarations
# and actual failed dlopen behavior: no effects are fabricated when libraries
# are absent, and reference/no-op plugins are not installed as working DSP.
add('/vendor/etc/audio_effects_config.xml', study / 'hardware-audio/aidl/default/audio_effects_config.xml')
production_plugin = None
if production_dynamics:
    dynamics = repo / 'dist/aosp16/audio-production-dynamics-link-1'
    link = json.loads((dynamics / 'link.json').read_text())
    production_plugin = dynamics / 'libdynamicsprocessingaidl.so'
    assert link['exit'] == 0 and sha(production_plugin) == link['binary_sha256']
    for source, expected in link['inputs'].items():
        assert sha(Path(source)) == expected, source
    add('/vendor/lib64/soundfx/libdynamicsprocessingaidl.so', production_plugin,
        'vendor_file', 0o644)
    add('/vendor/etc/archtv/licenses/dynamicsprocessing-NOTICE',
        study / 'framework-dynamicsproc/NOTICE')
    for name in ['COPYING.APACHE', 'COPYING.BSD', 'COPYING.MINPACK', 'COPYING.MPL2', 'NOTICE']:
        add('/vendor/etc/archtv/licenses/eigen-' + name, study / 'eigen' / name)
    record['production_dynamics_link'] = {'path': str(dynamics / 'link.json'),
                                          'sha256': sha(dynamics / 'link.json')}
    record['adaptations'].append('Original production DynamicsProcessing engine/AIDL/common worker/ranges deployed with original config and notices. Original factory must actually dlopen/query/process it; no inventory/readiness or DSP availability fabricated. Other missing plugins remain missing.')
record['adaptations'].append('Original AIDL audio_effects_config.xml unchanged. EffectFactory inserts identities only after actual dlopen succeeds; absent plugins remain unavailable, not accepted effects.')
record['original_rc_sha256'] = sha(original_rc)
record['adaptations'].append('Only the executable directory in original RC changes from audio APEX to private vendor; user/groups/caps/rtprio/ioprio/task_profiles/onrestart retained.')
# Original schema/configuration and volume tables, restricted to the hardware
# being evaluated. Do not advertise stub input/telephony/Bluetooth/MMAP/offload.
gold = Path('/home/tv/.cache/archtv/aosp16-qpr2/goldfish-audio-original-1/source/policy')
policy = ET.parse(gold / 'audio_policy_configuration.xml')
primary = ET.parse(gold / 'primary_audio_policy_configuration.xml').getroot()
attached = primary.find('attachedDevices')
for child in list(attached):
    if child.text != 'Speaker': attached.remove(child)
for name, attribute, keep in [('mixPorts', 'name', 'primary output'), ('devicePorts', 'tagName', 'Speaker'), ('routes', 'sink', 'Speaker')]:
    section = primary.find(name)
    for child in list(section):
        if child.get(attribute) != keep: section.remove(child)
for profile in primary.findall('mixPorts/mixPort/profile'):
    profile.set('samplingRates', '48000')
    profile.set('channelMasks', 'AUDIO_CHANNEL_OUT_STEREO')
primary.find('devicePorts/devicePort').set('address', 'CARD_0_DEV_0')
modules = policy.getroot().find('modules')
modules.clear()
modules.append(primary)
configuration = out / 'audio_policy_configuration.xml'
ET.register_namespace('xi', 'http://www.w3.org/2001/XInclude')
policy.write(configuration, encoding='utf-8', xml_declaration=True)
add('/vendor/etc/audio_policy_configuration.xml', configuration)
for name in ['audio_policy_volumes.xml', 'default_volume_tables.xml']:
    add('/vendor/etc/' + name, study / 'audio-policy-defaults' / name)
record['adaptations'].append('Original Goldfish schema/profile adapted to only Speaker/primary PCM16 stereo48k/card0dev0, original AOSP volume tables unchanged. Advertised format is a candidate pending real PCM negotiation.')
# Original release compiler emits core3 (unfrozen source4 released as3).
header = (repo / 'dist/aosp16/audio-original-build-12/aidl/include/aidl/android/hardware/audio/core/IModule.h').read_text()
assert re.search(r'version\s*=\s*true\s*\?\s*3\s*:\s*4\s*;', header), 'Check effective original AIDL release version'
manifest = ET.Element('manifest', {'version': '1.0', 'type': 'device'})
for package, version, instance in [('core', '3', 'IModule/default'), ('core', '3', 'IConfig/default'), ('effect', '3', 'IFactory/default')]:
    hal = ET.SubElement(manifest, 'hal', {'format': 'aidl'})
    ET.SubElement(hal, 'name').text = 'android.hardware.audio.' + package
    ET.SubElement(hal, 'version').text = version
    ET.SubElement(hal, 'fqname').text = instance
vintf = out / 'audio-linux-vintf.xml'
ET.ElementTree(manifest).write(vintf, encoding='utf-8', xml_declaration=True)
add('/vendor/etc/vintf/manifest/audio-linux.xml', vintf)
record['adaptations'].append('VINTF core3 matches original generated released contract, not unfrozen4; only configured default module/IConfig and original effect factory declared. Declaration never establishes availability.')
# Complete actual DT_NEEDED closure, keeping original Bionic/core namespace.
custom = {p.name: p for p in core.glob('*.so')}
pending = [core / binaries[0], effect / binaries[1]]
if production_plugin is not None:
    pending.append(production_plugin)
seen = set()
while pending:
    binary = pending.pop()
    needed = re.findall(r'NEEDED.*\[(.*?)\]', subprocess.check_output(['readelf', '-d', str(binary)], text=True))
    for name in needed:
        if name in seen or name in {'libc.so', 'libm.so', 'libdl.so', 'libc++.so', 'libdl_android.so'}: continue
        seen.add(name)
        target = '/vendor/lib64/' + name
        if target in vendor['files']: continue
        source = custom.get(name, root / 'system/lib64' / name)
        for _ in range(20):
            if not source.is_symlink(): break
            dest = source.readlink()
            source = root / str(dest).lstrip('/') if dest.is_absolute() else source.parent / dest
            source = Path(os.path.normpath(source))
        if not source.is_file():
            matches = [p for p in (root / 'apex').glob('*/lib64/' + name) if p.is_file()]
            assert len(matches) == 1, ('Missing/ambiguous original APEX dependency', name, matches)
            source = matches[0]
        assert source.is_file(), ('Missing original dependency', name, source)
        add(target, source, 'vendor_file', 0o644)
        pending.append(source)
    assert len(seen) < 96, 'Unexpected audio dependency expansion'
path.write_text(json.dumps(vendor, indent=2) + '\n')
(out / 'native-audio-input.json').write_text(json.dumps(record, indent=2) + '\n')
print('Private original audio profile prepared; NOT_RUNTIME_ACCEPTANCE', len(record['files']))
