#!/usr/bin/env python3
"""Fetch the pinned official AIDL compiler, matching libc++ and NOTICE to a cache."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--cache',type=Path,required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
manifest = json.loads((root/'runtime/aosp/aidl-toolchain.json').read_text())
args.cache.mkdir(parents=True,exist_ok=True)
for item in manifest['artifacts']:
    target=args.cache/item['file']
    if target.exists(): data=target.read_bytes()
    else:
        with urllib.request.urlopen(item['url'],timeout=60) as response:
            encoded=response.read(16*1024*1024+1)
        if len(encoded)>16*1024*1024:raise SystemExit('AIDL tool download exceeds budget')
        data=base64.b64decode(encoded,validate=True)
    if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:
        raise SystemExit('AIDL tool checksum mismatch: '+item['file'])
    if not target.exists():target.write_bytes(data)
    target.chmod(0o700 if item['file']=='aidl' else 0o600)
print(args.cache/'aidl')
