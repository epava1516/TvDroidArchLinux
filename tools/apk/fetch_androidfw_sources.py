#!/usr/bin/env python3
"""Fetch pinned AOSP native subtrees and verify each original file, not tar timestamps."""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('cache', type=Path)
parser.add_argument('--manifest', type=Path, help='Pinned native subtree manifest; defaults to androidfw')
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
manifest = json.loads((args.manifest or root/'runtime/aosp/androidfw-sources.json').read_text())
archive_budget = manifest.get('archive_budget_bytes', 24*1024*1024)
extraction_budget = manifest.get('extraction_budget_bytes', 100*1024*1024)
member_budget = manifest.get('member_budget', 10000)
if not (0 < archive_budget <= 256*1024*1024 and
        0 < extraction_budget <= 512*1024*1024 and 0 < member_budget <= 50000):
    raise SystemExit('Invalid native source manifest budgets')
args.cache.mkdir(parents=True, exist_ok=True)
for item in manifest['components']:
    archive = args.cache/(item['name']+'.tar.gz')
    if not archive.exists():
        temporary = archive.with_suffix('.download')
        with urllib.request.urlopen(item['archive_url'], timeout=60) as response, temporary.open('xb') as output:
            total = 0
            while block := response.read(1024*1024):
                total += len(block)
                if total > archive_budget:
                    raise SystemExit('Source archive exceeds budget')
                output.write(block)
        temporary.replace(archive)
    if archive.stat().st_size > archive_budget:
        raise SystemExit('Source archive exceeds budget')
    destination = args.cache/item['name']
    with tarfile.open(archive, 'r:gz') as bundle:
        members = bundle.getmembers()
        if len(members) > member_budget or sum(entry.size for entry in members) > extraction_budget:
            raise SystemExit('Source extraction budget exceeded')
        actual = {}
        normal = []
        for entry in members:
            path = PurePosixPath(entry.name)
            if path.is_absolute() or '..' in path.parts:
                raise SystemExit('Invalid archive path')
            if entry.isfile():
                if entry.name in actual:
                    raise SystemExit('Duplicate source entry')
                data = bundle.extractfile(entry).read()
                actual[entry.name] = {'bytes': len(data), 'sha256': hashlib.sha256(data).hexdigest()}
                normal.append(entry)
            elif entry.isdir():
                normal.append(entry)
            elif entry.name not in item['omitted_links']:
                raise SystemExit('Unexpected link or special entry')
        if actual != item['files']:
            raise SystemExit('Original source contents mismatch: '+item['name'])
        if not destination.exists():
            bundle.extractall(destination, members=normal, filter='data')
    for name, expected in item['files'].items():
        path = destination/name
        if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest() != expected['sha256']:
            raise SystemExit('Existing source modified or incomplete: '+str(path))
    print('Verified '+item['name'], flush=True)
