#!/usr/bin/env python3
"""Inventory Cargo normal/build dependency licenses without claiming legal review."""
import argparse
import hashlib
import json
import re
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('output', type=Path)
parser.add_argument('notices', type=Path)
parser.add_argument('--supplemental', type=Path)
args = parser.parse_args()
metadata = json.loads(subprocess.check_output([
    'cargo', 'metadata', '--format-version', '1', '--locked', '--offline',
    '--filter-platform', 'x86_64-unknown-linux-gnu'], text=True))
packages = {item['id']: item for item in metadata['packages']}
nodes = {item['id']: item for item in metadata['resolve']['nodes']}
roots = [item['id'] for item in metadata['packages']
         if item['name'] in ('archtv-compositor', 'archtv-shell') and item['id'] in metadata['workspace_members']]
if len(roots) != 2:
    raise SystemExit('Expected compositor and shell workspace roots.')
pending = roots[:]
selected = set()
while pending:
    identifier = pending.pop()
    if identifier in selected:
        continue
    selected.add(identifier)
    for dependency in nodes[identifier]['deps']:
        if any(kind['kind'] != 'dev' for kind in dependency['dep_kinds']):
            pending.append(dependency['pkg'])
# Cargo metadata can unify optional features across workspace members. Intersect
# with the concrete target/root build tree instead of inventing a cfg evaluator.
build_tree = subprocess.check_output([
    'cargo', 'tree', '--locked', '--offline', '--target', 'x86_64-unknown-linux-gnu',
    '--edges', 'normal,build', '--prefix', 'none', '--format', '{p}',
    '-p', 'archtv-compositor', '-p', 'archtv-shell'], text=True)
built = set()
for line in build_tree.splitlines():
    match = re.match(r'^(\S+) v(\S+)(?:\s|$)', line)
    if match:
        built.add(match.groups())
selected = {identifier for identifier in selected
            if (packages[identifier]['name'], packages[identifier]['version']) in built}
args.notices.mkdir(parents=True, exist_ok=True)
supplemental_root = args.supplemental or Path(metadata['workspace_root']) / 'licenses/cargo-supplemental'
provenance_path = supplemental_root / 'sources.json'
supplemental = {}
if provenance_path.exists():
    for item in json.loads(provenance_path.read_text())['packages']:
        supplemental[(item['name'], item['version'])] = item
records = []
for identifier in sorted(selected, key=lambda value: (packages[value]['name'], packages[value]['version'])):
    package = packages[identifier]
    directory = Path(package['manifest_path']).parent
    source = package['source'] or 'workspace'
    key = f"{package['name']}-{package['version']}-{hashlib.sha256(source.encode()).hexdigest()[:8]}"
    candidates = {path for path in directory.iterdir() if path.is_file()
                  and path.name.upper().startswith(('LICENSE', 'COPYING', 'NOTICE'))}
    if package['source'] is None:
        candidates.add(Path(metadata['workspace_root']) / 'LICENSE')
    if package.get('license_file'):
        path = Path(package['license_file'])
        candidates.add(path if path.is_absolute() else directory / path)
    provenance = supplemental.get((package['name'], package['version']))
    if provenance:
        for item in provenance['files']:
            path = supplemental_root / f"{package['name']}-{package['version']}" / item['file']
            if hashlib.sha256(path.read_bytes()).hexdigest() != item['sha256']:
                raise SystemExit(f'Supplemental notice checksum mismatch: {path}')
            candidates.add(path)
    notices = []
    for path in sorted(candidates):
        if not path.is_file() or path.stat().st_size > 2 * 1024 * 1024:
            continue
        destination = args.notices / key / path.name
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, destination)
        notices.append({'file': f'{key}/{path.name}', 'sha256': hashlib.sha256(destination.read_bytes()).hexdigest()})
    records.append({'name': package['name'], 'version': package['version'], 'source': source,
                    'declared_license': package.get('license'), 'published_authors': package.get('authors', []), 'repository': package.get('repository'),
                    'notices': notices, 'supplemental_provenance': provenance, 'missing_declaration_or_notice': not package.get('license') or not notices})
result = {'target': 'x86_64-unknown-linux-gnu', 'roots': ['archtv-compositor', 'archtv-shell'],
          'scope': 'Concrete Cargo target/root normal/build tree intersected with metadata; dev-only roots excluded. Metadata and copies of available license files; not a completed license compliance audit.',
          'packages': records, 'package_count': len(records),
          'packages_without_declared_license_or_notice': [item['name'] for item in records if item['missing_declaration_or_notice']]}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'packages': len(records), 'missing_notice_or_declaration': result['packages_without_declared_license_or_notice']}))
