#!/usr/bin/env python3
"""Fetch and verify the GN binary pinned by the original Skia source tree."""
import argparse
import hashlib
import io
import json
from pathlib import Path
import urllib.request
import zipfile

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('cache', type=Path)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
manifest = json.loads((root/'runtime/aosp/skia-gn-tool.json').read_text())
args.cache.mkdir(parents=True, exist_ok=True)
binary = args.cache/'gn'
if not binary.exists():
    with urllib.request.urlopen(manifest['url'], timeout=60) as response:
        archive = response.read(8*1024*1024+1)
    if len(archive) > 8*1024*1024 or hashlib.sha256(archive).hexdigest() != manifest['archive_sha256']:
        raise SystemExit('Pinned GN archive mismatch')
    with zipfile.ZipFile(io.BytesIO(archive)) as bundle:
        member = bundle.getinfo('gn')
        if member.file_size > 8*1024*1024:
            raise SystemExit('GN extraction exceeds budget')
        data = bundle.read(member)
    if hashlib.sha256(data).hexdigest() != manifest['gn_sha256']:
        raise SystemExit('Pinned GN binary mismatch')
    temporary = binary.with_suffix('.download')
    with temporary.open('xb') as output:
        output.write(data)
    temporary.chmod(0o755)
    temporary.replace(binary)
if hashlib.sha256(binary.read_bytes()).hexdigest() != manifest['gn_sha256']:
    raise SystemExit('Existing GN binary modified')
print('Verified pinned Skia GN: '+str(binary))
