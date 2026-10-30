#!/usr/bin/env python3
"""Fetch and verify pinned original AIDL inputs (window manifest by default)."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import urllib.request

parser=argparse.ArgumentParser()
parser.add_argument('--cache',type=Path,required=True)
parser.add_argument('--fetch',action='store_true')
parser.add_argument('--manifest',type=Path,default=Path('runtime/aosp/window-aidl-sources.json'))
args=parser.parse_args()
root=Path(__file__).resolve().parents[2]
manifest=json.loads((root/args.manifest).read_text())
for item in manifest['files']:
    relative=Path(item['cache_path'])
    if relative.is_absolute() or '..' in relative.parts:raise SystemExit('Unsafe AIDL cache path')
    path=args.cache/relative
    if path.exists():data=path.read_bytes()
    else:
        if not args.fetch:raise SystemExit('Missing AIDL source; use --fetch: '+str(path))
        url=item['repository']+'+/'+item['revision']+'/'+item['path']+'?format=TEXT'
        with urllib.request.urlopen(url,timeout=45) as response:encoded=response.read(4*1024*1024+1)
        if len(encoded)>4*1024*1024:raise SystemExit('AIDL source exceeds budget')
        data=base64.b64decode(encoded,validate=True)
    if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:
        raise SystemExit('AIDL source checksum mismatch: '+item['cache_path'])
    if not path.exists():path.parent.mkdir(parents=True,exist_ok=True);path.write_bytes(data)
print('Verified original AIDL inputs:',len(manifest['files']))
