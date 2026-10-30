#!/usr/bin/env python3
"""Fetch a pinned compile-only Android internal API reference, outside the repository."""
import argparse
import hashlib
import json
from pathlib import Path
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('cache', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
manifest = json.loads((root/'runtime/aosp/compile-reference.json').read_text())
args.cache.mkdir(parents=True, exist_ok=True)
destination = args.cache/manifest['file']
if not destination.exists():
    temporary = destination.with_suffix('.download')
    with urllib.request.urlopen(manifest['url'], timeout=90) as response, temporary.open('xb') as stream:
        total = 0
        while block := response.read(1024*1024):
            total += len(block)
            if total > manifest['bytes']:
                raise SystemExit('Compile reference exceeds pinned size')
            stream.write(block)
    temporary.replace(destination)
if destination.stat().st_size != manifest['bytes']:
    raise SystemExit('Compile reference size mismatch')
with destination.open('rb') as stream:
    if hashlib.file_digest(stream, 'sha256').hexdigest() != manifest['sha256']:
        raise SystemExit('Compile reference checksum mismatch')
print(destination)
