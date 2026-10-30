#!/usr/bin/env python3
"""Extract only research jars/classpath metadata from the pinned GPT/LP image.

Read-only debugfs, no loop mounts, privileges or Android processes. This is a
bounded extractor for the pinned single-device LP v10.0 layout, not lpunpack.
"""
import argparse
import hashlib
import json
import re
import struct
import subprocess
import zipfile
from pathlib import Path
from extract_platform_image import digest


def checked_hash(data, start, end):
    return hashlib.sha256(data[:start] + bytes(end-start) + data[end:]).digest() == data[start:end]


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--image', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    args = p.parse_args()
    image, out = args.image.resolve(), args.output.resolve()
    if any(c in str(out) for c in ['"', '\n', '\\']):
        raise SystemExit('Unsupported output path')
    manifest = Path(__file__).resolve().parents[2]/'runtime/aosp/platform-image.json'
    pinned = json.loads(manifest.read_text())
    if digest(image) != pinned['system_image_sha256']:
        raise SystemExit('Image SHA256 mismatch')
    out.mkdir(parents=True, exist_ok=False)
    commands = []

    def command(argv):
        commands.append(list(map(str, argv)))
        r = subprocess.run(argv, capture_output=True, text=True, timeout=60, check=True)
        if r.stderr:
            with (out/'extraction.stderr').open('a') as log:
                log.write(r.stderr)
        return r.stdout

    gpt = json.loads(command(['sfdisk', '--json', str(image)]))['partitiontable']
    assert gpt['label'] == 'gpt' and gpt['sectorsize'] == 512
    part = next(x for x in gpt['partitions'] if x['name'] == 'super')
    base = part['start']*512
    with image.open('rb') as f:
        f.seek(base+4096)
        geometry = f.read(52)
        assert struct.unpack_from('<II', geometry) == (0x616c4467, 52)
        assert checked_hash(geometry, 8, 40)
        f.seek(base+12288)
        header = f.read(128)
        assert struct.unpack_from('<IHHI', header) == (0x414c5030, 10, 0, 128)
        assert checked_hash(header, 12, 44)
        size = struct.unpack_from('<I', header, 44)[0]
        assert size <= 1024*1024
        tables = f.read(size)
        assert hashlib.sha256(tables).digest() == header[48:80]
        po, pn, ps = struct.unpack_from('<III', header, 80)
        eo, en, es = struct.unpack_from('<III', header, 92)
        bo, bn, bs = struct.unpack_from('<III', header, 116)
        assert ps == 52 and es == 24 and bn == 1 and bs == 64
        assert all(o+n*s <= len(tables) for o,n,s in [(po,pn,ps),(eo,en,es),(bo,bn,bs)])
        logical = out/'logical-system.img'
        found = False
        for i in range(pn):
            name, attr, first, count, group = struct.unpack_from('<36sIIII', tables, po+i*ps)
            if name.rstrip(b'\0') != b'system':
                continue
            assert not found and first+count <= en
            found = True
            with logical.open('xb') as dst:
                for e in range(first, first+count):
                    sectors, kind, start, device = struct.unpack_from('<QIQI', tables, eo+e*es)
                    assert kind == 0 and device == 0 and start+sectors <= part['size']
                    f.seek(base+start*512)
                    remaining = sectors*512
                    while remaining:
                        block = f.read(min(remaining, 1024*1024))
                        assert block
                        dst.write(block)
                        remaining -= len(block)
        assert found

    def dump(fs, original, destination):
        destination.parent.mkdir(parents=True, exist_ok=True)
        assert re.fullmatch(r'/[A-Za-z0-9_./-]+', original)
        command(['debugfs', '-R', f'dump {original} "{destination}"', str(fs)])
        if not destination.is_file():
            raise ValueError('debugfs did not extract '+original)

    def entries(fs, directory):
        result = []
        for line in command(['debugfs', '-R', 'ls -p '+directory, str(fs)]).splitlines():
            fields = line.split('/')
            if len(fields)>6 and fields[2].startswith('10'):
                assert re.fullmatch(r'[A-Za-z0-9_.-]+', fields[5])
                result.append((fields[5], int(fields[6])))
        return result

    for name in ['framework.jar', 'framework-graphics.jar', 'ext.jar', 'telephony-common.jar', 'voip-common.jar', 'ims-common.jar', 'framework-res.apk']:
        dump(logical, '/system/framework/'+name, out/'system/framework'/name)
    dump(logical, '/system/etc/classpaths/bootclasspath.pb', out/'system/classpaths/bootclasspath.pb')
    for name, size in entries(logical, '/system/apex'):
        if not name.endswith(('.apex', '.capex')):
            continue
        archive = out/'archives'/name
        dump(logical, '/system/apex/'+name, archive)
        assert archive.stat().st_size == size
        actual = archive
        with zipfile.ZipFile(archive) as z:
            if 'original_apex' in z.namelist():
                actual = archive.with_suffix('.original.apex')
                actual.write_bytes(z.read('original_apex'))
        module = out/'modules'/archive.stem
        module.mkdir(parents=True)
        with zipfile.ZipFile(actual) as z:
            payload = module/'payload.img'
            payload.write_bytes(z.read('apex_payload.img'))
        for directory in ['/javalib', '/etc/classpaths']:
            for name, size in entries(payload, directory):
                if name.endswith(('.jar', '.pb')):
                    dest = module/directory.removeprefix('/')/name
                    dump(payload, directory+'/'+name, dest)
                    assert dest.stat().st_size == size
    files = {str(x.relative_to(out)): {'bytes': x.stat().st_size, 'sha256': digest(x)}
             for x in out.rglob('*') if x.is_file()}
    (out/'provenance.json').write_text(json.dumps({
        'input_image_sha256': pinned['system_image_sha256'],
        'extractor_sha256': digest(Path(__file__)), 'commands': commands, 'files': files,
        'scope': 'Pinned static image only; GPT via sfdisk, LP geometry/header/table SHA256 verified, linear single-device system extents only; debugfs read-only dumps, ZIP CRC for read APEX members. No AVB/APEX signature verification, mount, Android boot or execution. Ownership is intentionally not restored.'}, indent=2)+'\n')
    print('Extracted original research components:', out)


if __name__ == '__main__':
    main()
