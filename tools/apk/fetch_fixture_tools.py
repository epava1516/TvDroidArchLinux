#!/usr/bin/env python3
"""Fetch only the pinned fixture build artifacts; no Android platform checkout."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('cache', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
manifest = json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())
args.cache.mkdir(parents=True, exist_ok=True)
for item in manifest['artifacts']:
    destination = args.cache/item['file']
    if destination.exists():
        with destination.open('rb') as stream:
            actual = hashlib.file_digest(stream, 'sha256').hexdigest()
        if actual != item['sha256']:
            raise SystemExit('Existing tool has an unexpected checksum: '+item['file'])
    else:
        with urllib.request.urlopen(item['url'], timeout=90) as response:
            data = response.read(80*1024*1024+1)
        if len(data) > 80*1024*1024:
            raise SystemExit('Tool download exceeds limit')
        if item['base64']:
            data = base64.b64decode(data, validate=True)
        if hashlib.sha256(data).hexdigest() != item['sha256']:
            raise SystemExit('Downloaded tool checksum mismatch: '+item['file'])
        temporary = destination.with_suffix('.download')
        temporary.write_bytes(data)
        temporary.replace(destination)
    print('Verified '+item['file'])
