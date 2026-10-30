#!/usr/bin/env python3
"""Fetch and verify the pinned R8 ART host laboratory bundle, outside the repo."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('cache', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
manifest = json.loads((root/'tools/apk/art-host.json').read_text())
cache = args.cache.resolve()
cache.mkdir(parents=True, exist_ok=True)
archive = cache/manifest['archive']
if not archive.exists():
    temporary = archive.with_suffix('.download')
    with urllib.request.urlopen(manifest['url'], timeout=90) as response, temporary.open('xb') as stream:
        total = 0
        while chunk := response.read(1024*1024):
            total += len(chunk)
            if total > manifest['compressed_bytes']:
                raise SystemExit('ART download exceeds pinned size')
            stream.write(chunk)
    temporary.replace(archive)
if archive.stat().st_size != manifest['compressed_bytes']:
    raise SystemExit('ART archive size mismatch')
for algorithm in ('sha1', 'sha256'):
    with archive.open('rb') as stream:
        actual = hashlib.file_digest(stream, algorithm).hexdigest()
    if actual != manifest[algorithm]:
        raise SystemExit('ART archive checksum mismatch: '+algorithm)
destination = cache/'host'
runtime = destination/manifest['directory']
if runtime.exists():
    raise SystemExit('Runtime destination already exists; refusing to overwrite: '+str(runtime))
destination.mkdir(exist_ok=True)
with tarfile.open(archive, 'r:gz') as bundle:
    members = []
    expanded = 0
    for member in bundle:
        parts = PurePosixPath(member.name).parts
        if (not parts or parts[0] != manifest['directory'] or '..' in parts
                or not (member.isfile() or member.isdir())):
            raise SystemExit('Unsupported archive entry: '+member.name)
        expanded += member.size
        members.append(member)
        if expanded > 8*1024**3 or len(members) > 100000:
            raise SystemExit('ART archive exceeds extraction budget')
    bundle.extractall(destination, members=members, filter='data')
print(runtime)
