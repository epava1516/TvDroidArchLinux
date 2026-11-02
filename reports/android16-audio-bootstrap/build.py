#!/usr/bin/env python3
"""Generate original frozen audio contracts and compile the original HAL units.

This is a build experiment, never an audio/service compatibility result.
"""
from pathlib import Path
import hashlib
import json
import re
import subprocess
import sys

repo = Path(__file__).resolve().parents[2]
out = (repo / sys.argv[1]).resolve()
out.mkdir()
debug = '--debug' in sys.argv[2:]
study = Path('/home/tv/.cache/archtv/aosp16-qpr2/audio-original-study-1')
hw = study / 'hardware-audio/aidl'
default = hw / 'default'
record = {'scope': 'Original audio HAL source build only; no availability or playback acceptance',
          'optimization': 'debug-O0' if debug else 'O2',
          'source_acquisition': json.loads((study / 'complete-source-inputs.json').read_text()),
          'commands': [], 'sources': []}


def save():
    (out / 'build.json').write_text(json.dumps(record, indent=2) + '\n')


def run(argv, stage):
    argv = list(map(str, argv))
    result = subprocess.run(argv, capture_output=True, text=True, timeout=120)
    log = out / (stage.replace('/', '_') + '.log')
    log.write_text(result.stdout + result.stderr)
    record['commands'].append({'argv': argv, 'exit': result.returncode, 'log': str(log)})
    save()
    print(stage, result.returncode, result.stderr[-1800:] if result.returncode else '', flush=True)
    if result.returncode:
        raise SystemExit(result.returncode)


apis = [
    (study / 'media-audio-aidl', 'android.media.audio.common.types', 4),
    (study / 'media-audio-aidl', 'android.media.audio.eraser.types', 1),
    (study / 'common-aidl', 'android.hardware.common', 2),
    (study / 'fmq-aidl', 'android.hardware.common.fmq', 1),
    (hw, 'android.hardware.audio.common', 4),
    (hw, 'android.hardware.audio.core', 4),
    (hw, 'android.hardware.audio.core.sounddose', 3),
    (hw, 'android.hardware.audio.effect', 3),
    (study / 'bluetooth-audio-aidl', 'android.hardware.bluetooth.audio', 5),
]
roots = [p / 'aidl_api' / name / (str(version) if (p / 'aidl_api' / name / str(version)).exists() else 'current') for p, name, version in apis]
for (project, name, version), api in zip(apis, roots):
    frozen_hash = api / '.hash'
    digest = frozen_hash.read_text().splitlines()[-1] if frozen_hash.exists() else 'notfrozen'
    release = []
    if not frozen_hash.exists():
        # Original Soong release_aidl_use_unfrozen=false generation contract.
        # The GSI V4 SONAME actually implements getInterfaceVersion=3.
        assert name == 'android.hardware.audio.core' and version == 4
        previous = project / 'aidl_api' / name / str(version - 1)
        release = ['-N' + str(api), '--previous_api_dir=' + str(previous), '--previous_hash=' + (previous / '.hash').read_text().splitlines()[-1]]
    record.setdefault('interface_contracts', []).append({'name': name, 'build_version': version, 'source': str(api), 'frozen': frozen_hash.exists(), 'release_flags': release})
    run([repo / 'dist/aosp16/aidl-host-build-4/aidl', '--lang=ndk', '--structured',
         '--stability=vintf', '--version=' + str(version), '--hash=' + digest,
         '--min_sdk_version=31', '--omit_invocation', '--out=' + str(out / 'aidl/src'),
         '--header_out=' + str(out / 'aidl/include')] + ['-I' + str(p) for p in roots if p != api or frozen_hash.exists()] + release
        + sorted(api.rglob('*.aidl')), 'aidl-' + name)

xsdc = json.loads((repo / 'dist/aosp16/xsdc-host-1/generation.json').read_text())['argv'][:4]
for schema, package, root in [
    ('config/audioPolicy/audio_policy_configuration.xsd', 'android.audio.policy.configuration', None),
    ('config/audioPolicy/engine/audio_policy_engine_configuration.xsd', 'android.audio.policy.engine.configuration', None),
    ('config/audioPolicy/capengine/PolicyConfigurableDomains.xsd', 'android.audio.policy.capengine.configuration', 'ConfigurableDomains'),
]:
    args = xsdc + [str(default / schema), '-p', package, '-o', str(out / 'xml'), '-c']
    if root:
        args += ['-r', root]
    run(args, 'xsdc-' + package)

flags = json.loads((repo / 'reports/android16-hwc3-frontend/build.json').read_text())['results'][0]['argv']
flags = flags[:flags.index('-MMD')]
if debug:
    flags = [f for f in flags if not f.startswith('-O')] + ['-O0']
includes = [default, hw / 'common/include', study / 'audio-conversion/include', study / 'audio-effects/include', study / 'audio-route/include', study / 'bluetooth-audio-utils/aidl_session', study / 'libfmq/include', study / 'media-audio-aidl/utils', study / 'error-utils/include', out / 'aidl/include', out / 'xml/include', default / 'include',
            study / 'media-audio-aidl/include', hw / 'include', study / 'audio-system/include',
            study / 'audio-utils/include', study / 'audioclient/include',
            study / 'audiofoundation/include', study / 'audiohal/include',
            study / 'mediahelper/include', study / 'nbaio/include', study / 'nbaio/include_mono',
            study / 'stagefright-headers', study / 'mediautils-headers',
            study / 'tinyalsa/include', study / 'alsa-utils-current/include',
            study / 'bluetooth-audio-aidl/default',
            Path('/home/tv/.cache/archtv/graphics-candidates-1/libfmq/include'),
            Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/xsdc/source/system/tools/xsdc/utils/include'),
            Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/libxml2-target/source/external/libxml2/include')]
flags += ['-DBACKEND_NDK', '-D_GNU_SOURCE'] + ['-I' + str(p) for p in includes]
bp = (default / 'Android.bp').read_text()
section = bp[bp.index('name: "libaudioserviceexampleimpl"'):]
units = re.search(r'srcs:\s*\[(.*?)\]', section, re.S).group(1)
sources = [default / s for s in re.findall(r'"([^"]+\.(?:cpp|c))"', units)]
sources += [default / name for name in ['main.cpp']]
sources += sorted((out / 'xml').glob('*.cpp'))
for i, source in enumerate(sources):
    obj = out / (str(i) + '.o')
    run(flags + ['-MMD', '-MF', str(out / (str(i) + '.d')), '-c', source, '-o', obj],
        'compile-' + str(i) + '-' + source.name)
    record['sources'].append({'path': str(source),
                              'sha256': hashlib.file_digest(source.open('rb'), 'sha256').hexdigest(),
                              'object': str(obj)})
    save()
record['original_units_compiled'] = True
record['limitations'] = ['Linking and original dependent libraries still required',
                         'No runtime, HAL inventory, hardware I/O or APK acceptance']
save()
