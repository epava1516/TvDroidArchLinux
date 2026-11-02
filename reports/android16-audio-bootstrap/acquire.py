#!/usr/bin/env python3
"""Acquire pinned original audio subsystem sources, without executing Android."""
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import hashlib
import io
import json
import tarfile
import urllib.request
import xml.etree.ElementTree as ET

base = Path('/home/tv/.cache/archtv/aosp16-qpr2/audio-original-study-1')
base.mkdir(exist_ok=True)
pins = {p.get('path'): p.get('revision') for p in ET.parse(
    '/home/tv/.cache/archtv/aosp16-qpr2/manifest.lock.xml').findall('project')}
inputs = [
    ('hardware/interfaces', 'audio', 'hardware-audio'),
    ('hardware/interfaces', 'bluetooth/audio/aidl', 'bluetooth-audio-aidl'),
    ('hardware/interfaces', 'common/aidl', 'common-aidl'),
    ('hardware/interfaces', 'common/fmq/aidl', 'fmq-aidl'),
    ('external/tinyalsa_new', '', 'tinyalsa'),
    ('hardware/libhardware', 'modules/usbaudio', 'alsa-utils'),
    ('hardware/libhardware', 'include_all', 'libhardware-headers'),
    ('external/tinyxml2', '', 'tinyxml2'),
    ('system/media', 'audio', 'audio-system'),
    ('system/media', 'audio_utils', 'audio-utils'),
    ('system/media', 'audio_effects', 'audio-effects'),
    ('system/media', 'audio_route', 'audio-route'),
    ('system/libfmq', '', 'libfmq'),
    ('hardware/interfaces', 'bluetooth/audio/utils', 'bluetooth-audio-utils'),
    ('system/hardware/interfaces', 'media', 'media-audio-aidl'),
    ('system/media', 'alsa_utils', 'alsa-utils-current'),
    ('frameworks/av', 'media/libaudioclient', 'audioclient'),
    ('frameworks/av', 'media/libaudiofoundation', 'audiofoundation'),
    ('frameworks/av', 'media/audioaidlconversion', 'audio-conversion'),
    ('frameworks/av', 'media/liberror', 'error-utils'),
    ('frameworks/av', 'media/libaudiohal', 'audiohal'),
    ('frameworks/av', 'media/libmediahelper', 'mediahelper'),
    ('frameworks/av', 'media/libnbaio', 'nbaio'),
    ('frameworks/av', 'media/module/foundation/include', 'stagefright-headers'),
    ('frameworks/av', 'media/utils/include', 'mediautils-headers'),
]


def acquire(item):
    project, sub, name = item
    pin = pins[project]
    suffix = '/' + sub if sub else ''
    url = f'https://android.googlesource.com/platform/{project}/+archive/{pin}{suffix}.tar.gz'
    archive_path = base / (name + '.tar.gz')
    record_path = base / (name + '.acquisition.json')
    if archive_path.exists() and record_path.exists():
        old = json.loads(record_path.read_text())
        if old['url'] == url and hashlib.file_digest(archive_path.open('rb'), 'sha256').hexdigest() == old['sha256']:
            return old
    blob = urllib.request.urlopen(url, timeout=40).read(20_000_001)
    if len(blob) > 20_000_000:
        raise ValueError(f'Unexpected source archive size: {name}')
    dest = base / name
    dest.mkdir(exist_ok=True)
    with tarfile.open(fileobj=io.BytesIO(blob), mode='r:gz') as archive:
        regular = [m for m in archive.getmembers() if m.isfile() or m.isdir()]
        skipped = [m.name for m in archive.getmembers() if not (m.isfile() or m.isdir())]
        archive.extractall(dest, members=regular, filter='data')
    archive_path.write_bytes(blob)
    record = dict(project=project, pin=pin, url=url, path=str(dest),
                  sha256=hashlib.sha256(blob).hexdigest(), skipped_nonregular=skipped)
    record_path.write_text(json.dumps(record, indent=2) + '\n')
    return record


if __name__ == '__main__':
    with ThreadPoolExecutor(max_workers=4) as pool:
        records = list(pool.map(acquire, inputs))
    (base / 'complete-source-inputs.json').write_text(json.dumps(records, indent=2) + '\n')
    print(f'{len(records)} original audio source archives verified; no execution claim')
