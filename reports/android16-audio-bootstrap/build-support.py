#!/usr/bin/env python3
"""Compile original ALSA, FIFO and effect-config libraries for the audio HAL.

Uses the actual generated audio contracts from build.py. Archives are build
inputs, not proof of service availability, hardware I/O or APK compatibility.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

repo = Path(__file__).resolve().parents[2]
core = (repo / sys.argv[1]).resolve()
out = (repo / sys.argv[2]).resolve()
out.mkdir()
study = Path('/home/tv/.cache/archtv/aosp16-qpr2/audio-original-study-1')
base = json.loads((core / 'build.json').read_text())
first = next(c for c in base['commands'] if Path(c['log']).name.startswith('compile-'))['argv']
flags = first[:first.index('-MMD')]
# Original current libhardware headers take precedence over inherited graphics
# headers; no host/glibc headers or library stubs are introduced.
flags = flags[:1] + ['-I' + str(study / 'libhardware-headers'),
                     '-I' + str(study / 'tinyxml2'),
                     '-I' + str(study / 'flatbuffers/include'),
                     '-I/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/system-apex/source/system/apex/libs/libapexsupport/include'] + flags[1:]
groups = {
    'libflatbuffers_cpp': [study / 'flatbuffers/src' / n for n in [
        'code_generators.cpp', 'idl_gen_fbs.cpp', 'idl_gen_text.cpp', 'idl_parser.cpp',
        'reflection.cpp', 'util.cpp']],
    'libtinyalsav2': [study / 'tinyalsa/src' / n for n in
                     ['mixer.c', 'mixer_hw.c', 'mixer_plugin.c', 'pcm.c',
                      'pcm_hw.c', 'pcm_plugin.c', 'snd_card_plugin.c']],
    'libalsautilsv2': [study / 'alsa-utils-current' / n for n in
                      ['alsa_device_profile.c', 'alsa_device_proxy.c', 'alsa_format.c', 'alsa_logging.c']],
    'libnbaio_mono': [study / 'nbaio' / n for n in ['MonoPipe.cpp', 'MonoPipeReader.cpp', 'NBAIO.cpp']],
    'libeffectconfig': [study / 'hardware-audio/aidl/default/EffectConfig.cpp'],
    'libbluetooth_audio_v5_ndk': sorted((core / 'aidl/src/android/hardware/bluetooth/audio').rglob('*.cpp')),
    'audio_policy_xml': sorted((core / 'xml').glob('*.cpp')),
    'audio_effect_service': [study / 'hardware-audio/aidl/default' / n for n in ['EffectFactory.cpp', 'EffectMain.cpp']],
    # Complete original Android.bp groups, not replacements for missing symbols.
    # These are linked by the original core factory even when no Bluetooth route
    # is configured. Compiling them does not establish Bluetooth availability.
    'libbluetooth_audio_session_aidl': [study / 'bluetooth-audio-utils/aidl_session' / n for n in [
        'BluetoothAudioCodecs.cpp', 'BluetoothAudioSession.cpp', 'HidlToAidlMiddleware.cpp',
        'BluetoothLeAudioCodecsProvider.cpp', 'BluetoothHfpCodecsProvider.cpp',
        'BluetoothLeAudioAseConfigurationSettingProvider.cpp']],
    'android_hardware_bluetooth_audio_impl': [study / 'bluetooth-audio-aidl/default' / n for n in [
        'BluetoothAudioProvider.cpp', 'BluetoothAudioProviderFactory.cpp',
        'A2dpOffloadAudioProvider.cpp', 'A2dpOffloadCodecAac.cpp', 'A2dpOffloadCodecFactory.cpp',
        'A2dpOffloadCodecSbc.cpp', 'A2dpSoftwareAudioProvider.cpp', 'HearingAidAudioProvider.cpp',
        'HfpOffloadAudioProvider.cpp', 'HfpSoftwareAudioProvider.cpp',
        'LeAudioOffloadAudioProvider.cpp', 'LeAudioSoftwareAudioProvider.cpp', 'service.cpp']],
}
record = {'scope': 'Original support library compilation and static archives, not runtime acceptance',
          'core_contract_header_sha256': hashlib.sha256((core / 'aidl/include/aidl/android/hardware/audio/core/IModule.h').read_bytes()).hexdigest(),
          'source_acquisition': json.loads((study / 'complete-source-inputs.json').read_text()),
          'commands': [], 'sources': [], 'archives': {}}


def run(argv, name):
    argv = list(map(str, argv))
    result = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    log = out / (name + '.log')
    log.write_text(result.stdout + result.stderr)
    record['commands'].append({'argv': argv, 'exit': result.returncode, 'log': str(log)})
    (out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
    print(name, result.returncode, result.stderr[-1800:] if result.returncode else '', flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)


selected = set(sys.argv[3:])
assert selected <= groups.keys(), selected - groups.keys()
bluetooth_groups = {'libbluetooth_audio_session_aidl', 'android_hardware_bluetooth_audio_impl'}
if not selected:
    # Preserve the existing non-Bluetooth support build invocation.
    selected = set(groups) - bluetooth_groups
if selected & bluetooth_groups:
    generated = out / 'bluetooth-generated'
    generated.mkdir()
    # Original middleware consumes frozen HIDL types as well as NDK AIDL.
    hal_root = generated / 'hal-inputs'
    (hal_root / 'bluetooth').mkdir(parents=True)
    (hal_root / 'audio').symlink_to(study / 'hardware-audio', target_is_directory=True)
    (hal_root / 'bluetooth/audio').symlink_to(study / 'bluetooth-audio-hidl', target_is_directory=True)
    hidl_out = generated / 'hidl'
    hidl = repo / 'dist/aosp16/hidl-host-build-8/hidl-gen'
    roots = ['-randroid.hardware:' + str(hal_root),
             '-randroid.hidl:/home/tv/.cache/archtv/graphics-candidates-1/libhidl/transport']
    for package in ['android.hidl.safe_union@1.0', 'android.hardware.audio.common@5.0', 'android.hardware.bluetooth.audio@2.0',
                    'android.hardware.bluetooth.audio@2.1']:
        for lang in ['hash', 'c++-headers', 'c++-sources']:
            run([hidl, '-L' + lang, *roots, *([] if lang == 'hash' else ['-o', hidl_out]), package],
                'hidl-' + package + '-' + lang)
    flags += ['-I' + str(hidl_out)]
    groups['bluetooth_hidl'] = sorted(hidl_out.rglob('*.cpp'))
    selected.add('bluetooth_hidl')
    xsdc = json.loads((repo / 'dist/aosp16/xsdc-host-1/generation.json').read_text())['argv'][:4]
    for schema, package, root_name in [
        ('le_audio_codec_capabilities/le_audio_codec_capabilities.xsd',
         'aidl.android.hardware.bluetooth.audio.setting', 'leAudioOffloadSetting'),
        ('hfp_codec_capabilities/hfp_codec_capabilities.xsd',
         'aidl.android.hardware.bluetooth.audio.hfp.setting', 'hfpOffloadSetting')]:
        source = study / 'bluetooth-audio-utils' / schema
        record.setdefault('schema_inputs', {})[str(source)] = hashlib.file_digest(source.open('rb'), 'sha256').hexdigest()
        run(xsdc + [str(source), '-p', package, '-o', str(generated), '-c', '-r', root_name],
            'xsdc-' + package)
    host = json.loads((repo / 'dist/aosp16/flatc-host-audio-1/build.json').read_text())
    flatc = Path(host['executable'])
    assert host['terminal'] and hashlib.file_digest(flatc.open('rb'), 'sha256').hexdigest() == host['sha256']
    schemas = [study / 'bluetooth-audio-utils/le_audio_configuration_set' / n for n in
               ['audio_set_configurations.fbs', 'audio_set_scenarios.fbs']]
    for source in schemas:
        record['schema_inputs'][str(source)] = hashlib.file_digest(source.open('rb'), 'sha256').hexdigest()
    run([flatc, '-I', study / 'bluetooth-audio-utils', '-o', generated, '--cpp', *schemas], 'flatc-bluetooth')
    record['host_flatc'] = {'path': str(flatc), 'sha256': host['sha256'], 'scope': host['scope']}
    aconfig = Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/aconfig-host/aconfig')
    provenance = json.loads(aconfig.with_name('provenance.json').read_text())
    assert hashlib.file_digest(aconfig.open('rb'), 'sha256').hexdigest() == provenance['sha256']
    declaration = study / 'bluetooth-audio-flags/btaudiohal.aconfig'
    flag_cache = generated / 'btaudiohal.pb'
    run([aconfig, 'create-cache', '--package', 'com.android.btaudio.hal.flags',
         '--container', 'system', '--declarations', declaration, '--cache', flag_cache], 'aconfig-cache')
    run([aconfig, 'create-cpp-lib', '--cache', flag_cache, '--out', generated / 'flags',
         '--mode', 'production'], 'aconfig-cpp')
    record['aconfig'] = {'tool_sha256': provenance['sha256'], 'declaration_sha256':
                        hashlib.file_digest(declaration.open('rb'), 'sha256').hexdigest(),
                        'scope': 'Original production generator/default disabled flag; not Bluetooth/offload availability'}
    flags += ['-I' + str(generated / 'include'), '-I' + str(generated),
              '-I' + str(generated / 'flags/include'),
              '-I/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/aconfig-source/source/build/make/tools/aconfig/aconfig_storage_read_api/include',
              '-I' + str(study / 'flatbuffers/include'), '-I' + str(study / 'liblc3/include'),
              '-I' + str(study / 'opus-experimental/include'),
              '-I' + str(study / 'bluetooth-offload/leaudio/audio/include'),
              '-Wno-error=macro-redefined']
    groups['bluetooth_xml'] = sorted(generated.glob('*.cpp'))
    groups['bluetooth_flags'] = sorted((generated / 'flags').glob('*.cc'))
    selected.add('bluetooth_xml')
    selected.add('bluetooth_flags')
for group, sources in groups.items():
    if selected and group not in selected:
        continue
    objects = []
    for i, source in enumerate(sources):
        unit_flags = flags
        if source.name == 'EffectMain.cpp':
            # The upstream target is APEX-only. For a Linux-owned Bionic
            # process include the real API declarations without asserting
            # an APEX identity; AApexInfo_create retains its actual failure
            # and upstream fallback to a readable configuration file.
            unit_flags = flags + ['-include', 'android/apexsupport.h']
        if source.suffix == '.c':
            unit_flags = [f for f in flags if not f.startswith('-std=') and f not in
                          ['-fno-rtti', '-frtti', '-fvisibility-inlines-hidden', '-nostdinc++']]
            # The inherited graphics recipe is C++; keep the intentional
            # upstream C fall-through diagnostic without making it fatal.
            unit_flags += ['-x', 'c', '-std=gnu11', '-Wno-error=implicit-fallthrough']
        obj = out / (group + '-' + str(i) + '.o')
        run(unit_flags + ['-MMD', '-MF', out / (obj.name + '.d'), '-c', source, '-o', obj],
            group + '-' + str(i))
        record['sources'].append({'path': str(source),
                                  'sha256': hashlib.file_digest(source.open('rb'), 'sha256').hexdigest(),
                                  'object': str(obj),
                                  'object_sha256': hashlib.file_digest(obj.open('rb'), 'sha256').hexdigest()})
        objects.append(obj)
    archive = out / (group + '.a')
    run(['ar', 'rcs', archive] + objects, group + '-archive')
    record['archives'][group] = {'path': str(archive),
                                 'sha256': hashlib.file_digest(archive.open('rb'), 'sha256').hexdigest()}
record['terminal'] = True
(out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')
