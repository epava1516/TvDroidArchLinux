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
                     '-I/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/system-apex/source/system/apex/libs/libapexsupport/include'] + flags[1:]
groups = {
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
