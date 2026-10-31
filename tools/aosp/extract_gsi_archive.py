#!/usr/bin/env python3
"""Verify and extract the three-member official GSI research archive, without booting it.

This deliberately rejects other archive layouts rather than guessing an Android
version. Published archive identity and internal build ID must both agree.
"""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import zipfile


def digest(path):
    h = hashlib.sha256()
    with path.open('rb') as f:
        for block in iter(lambda: f.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--archive', type=Path, required=True)
    p.add_argument('--archive-sha256', required=True)
    p.add_argument('--build-id', required=True)
    p.add_argument('--output', type=Path, required=True)
    a = p.parse_args()
    archive = a.archive.resolve()
    if digest(archive) != a.archive_sha256:
        raise SystemExit('Archive SHA256 mismatch; nothing extracted')
    with zipfile.ZipFile(archive) as z:
        members = z.infolist()
        names = [x.filename for x in members]
        if len(names) != 3 or set(names) != {'system.img', 'vbmeta.img', 'build.prop'}:
            raise SystemExit('Unsupported GSI archive layout; nothing extracted')
        if (z.getinfo('build.prop').file_size > 1024*1024
                or z.getinfo('vbmeta.img').file_size > 1024*1024
                or z.getinfo('system.img').file_size > 8*1024**3):
            raise SystemExit('Archive member exceeds research size limit')
        properties = {}
        for line in z.read('build.prop').decode('utf-8').splitlines():
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                if key in properties:
                    raise SystemExit('Duplicate build property: '+key)
                properties[key] = value
        if properties.get('ro.build.id') != a.build_id:
            raise SystemExit('Internal build ID mismatch; nothing extracted')
        a.output.mkdir(parents=True, exist_ok=False)
        files = {}
        for member in members:
            dest = a.output/member.filename
            with z.open(member) as src, dest.open('xb') as dst:
                shutil.copyfileobj(src, dst, 1024*1024)
            if dest.stat().st_size != member.file_size:
                raise SystemExit('Extracted size mismatch')
            files[member.filename] = {'bytes': member.file_size, 'sha256': digest(dest),
                                     'zip_crc32': format(member.CRC, '08x')}
    result = {'archive': str(archive), 'archive_sha256': a.archive_sha256,
              'build_id': a.build_id, 'extractor_sha256': digest(Path(__file__)),
              'files': files, 'properties': properties,
              'scope': 'Published archive digest, internal build ID and ZIP CRC; not AVB/APEX signature verification, source equivalence, licensing acceptance, boot or execution. Partial failed outputs retained.'}
    (a.output/'provenance.json').write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'build_id': a.build_id, 'files': len(files), 'output': str(a.output)}))


if __name__ == '__main__':
    main()
