#!/usr/bin/env python3
"""Static APK dependency inventory; does not execute or certify an APK."""
import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import struct
import zipfile


def dex_inventory(data):
    if len(data) < 112 or data[:8] not in [b'dex\n'+version+b'\0' for version in [b'035', b'037', b'038', b'039', b'040']]:
        raise ValueError('Unsupported or truncated DEX; container version 041 is not supported')
    def uint(offset):
        if offset < 0 or offset+4 > len(data):
            raise ValueError('DEX offset outside file')
        return struct.unpack_from('<I', data, offset)[0]
    if uint(32) != len(data) or uint(36) != 112 or uint(40) != 0x12345678:
        raise ValueError('Unsupported DEX header or endianness')
    def table(count_offset, width):
        count, offset = uint(count_offset), uint(count_offset+4)
        if count > 1_000_000 or offset > len(data) or count > (len(data)-offset)//width:
            raise ValueError('DEX table outside file')
        return range(offset, offset+count*width, width)
    strings = table(56, 4)
    def string(index):
        if index >= len(strings):
            raise ValueError('Invalid DEX string index')
        offset = uint(strings[index])
        for _ in range(5):
            if offset >= len(data):
                raise ValueError('Truncated string length')
            byte = data[offset]
            offset += 1
            if byte < 128:
                break
        else:
            raise ValueError('Invalid string length')
        end = data.find(b'\0', offset, min(len(data), offset+65536))
        if end < 0:
            raise ValueError('Unterminated or oversized descriptor')
        # Only ASCII platform descriptors are classified; other MUTF-8 is retained
        # as escaped bytes rather than treated as a valid decoded class name.
        return data[offset:end].decode('ascii', errors='backslashreplace')
    types = []
    descriptor_bytes = 0
    for offset in table(64, 4):
        descriptor = string(uint(offset))
        descriptor_bytes += len(descriptor)
        if len(descriptor) > 4096 or descriptor_bytes > 16*1024*1024:
            raise ValueError('Descriptor budget exceeded')
        types.append(descriptor)
    def type_name(index):
        if index >= len(types):
            raise ValueError('Invalid DEX type index')
        return types[index]
    defined = {type_name(uint(offset)) for offset in table(96, 32)}
    methods = Counter()
    for offset in table(88, 8):
        methods[type_name(struct.unpack_from('<H', data, offset)[0])] += 1
    return set(types), defined, methods


def inspect(path):
    with path.open('rb') as stream:
        digest = hashlib.file_digest(stream, 'sha256').hexdigest()
    types, defined, methods = set(), set(), Counter()
    dex_files, native = [], []
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)):
            raise ValueError('Duplicate ZIP entries')
        entries = [entry for entry in archive.infolist() if entry.filename.endswith('.dex')]
        if not entries or len(entries) > 32 or sum(entry.file_size for entry in entries) > 128*1024*1024:
            raise ValueError('No DEX or inventory size limit exceeded')
        for entry in entries:
            if entry.file_size > 64*1024*1024:
                raise ValueError('DEX exceeds size limit')
            refs, definitions, counts = dex_inventory(archive.read(entry))
            types.update(refs)
            defined.update(definitions)
            methods.update(counts)
            dex_files.append({'file': entry.filename, 'bytes': entry.file_size})
        native = sorted(name for name in names if name.startswith('lib/') and name.endswith('.so'))
        manifest = 'AndroidManifest.xml' in names
    external = types-defined
    platform = sorted(name for name in external if name.startswith(('Landroid/', 'Ljava/', 'Ljavax/', 'Ldalvik/', 'Llibcore/')))
    return {'apk': path.name, 'sha256': digest, 'has_manifest': manifest,
            'dex_files': dex_files, 'defined_class_count': len(defined),
            'platform_class_references': platform,
            'platform_method_reference_counts': {name: methods[name] for name in platform if methods[name]},
            'native_libraries': native,
            'scope': 'Static DEX type/method-owner references, subtracting classes defined across all DEX. Not reachability, API completeness, reflection/JNI resolution, signature validation or execution. Manifest/resources and ELF dependencies are not decoded. Descriptors outside ASCII are escaped; DEX 041 unsupported.'}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('apk', type=Path)
    parser.add_argument('output', type=Path)
    args = parser.parse_args()
    result = inspect(args.apk)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(result, indent=2)+'\n')
    print(json.dumps({'dex_files':len(result['dex_files']), 'platform_classes':len(result['platform_class_references']), 'native_libraries':len(result['native_libraries'])}))
