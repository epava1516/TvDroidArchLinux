#!/usr/bin/env python3
"""Inventory a pinned AOSP source set; this is not a complete Java dependency resolver."""
import argparse
import base64
import hashlib
import json
from pathlib import Path
import re
import urllib.request

parser = argparse.ArgumentParser()
parser.add_argument('--cache', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--fetch', action='store_true', help='Download only the manifest source files')
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
manifest = json.loads((root/'runtime/aosp/framework-study.json').read_text())
args.output.mkdir(parents=True, exist_ok=False)
sources = {}
for item in manifest['files']:
    path = args.cache/item['path']
    url = manifest['repository']+'+/'+manifest['revision']+'/'+item['path']+'?format=TEXT'
    if not path.exists():
        if not args.fetch:
            raise SystemExit('Missing source; use --fetch: '+str(path))
        with urllib.request.urlopen(url, timeout=60) as response:
            encoded = response.read(4*1024*1024+1)
        if len(encoded) > 4*1024*1024:
            raise SystemExit('Source exceeds budget')
        payload = base64.b64decode(encoded, validate=True)
        if len(payload) != item['bytes'] or hashlib.sha256(payload).hexdigest() != item['sha256']:
            raise SystemExit('Downloaded source checksum mismatch: '+item['path'])
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(payload)
    data = path.read_bytes()
    if len(data) != item['bytes'] or hashlib.sha256(data).hexdigest() != item['sha256']:
        raise SystemExit('Cached source checksum mismatch: '+item['path'])
    sources[item['path']] = data.decode('utf-8')

entries = []
for path, source in sources.items():
    # Imports and native declarations only. Comment removal is lexical, not a Java parser.
    clean = re.sub(r'/\*.*?\*/|//[^\n]*', '', source, flags=re.S)
    imports = re.findall(r'^import\s+([^;]+);', clean, flags=re.M)
    java_tokens = re.sub(r'"(?:\\.|[^"\\])*"|\'(?:\\.|[^\'\\])*\'', '""', clean)
    natives = [' '.join(match.split()) for match in re.findall(r'\bnative\s+[^;{}]+;', java_tokens)] if path.endswith('.java') else []
    includes = re.findall(r'^#include\s+[<"]([^>"]+)[>"]', clean, flags=re.M)
    package = re.search(r'^package\s+([^;]+);', clean, flags=re.M)
    local_refs = []
    if package:
        prefix = package.group(1).replace('.', '/')+'/'
        local_refs = [other for other in sources if other != path and '/'+prefix in other
                      and re.search(r'\b'+re.escape(Path(other).stem)+r'\b', clean)]
    entries.append({'path': path, 'sha256': hashlib.sha256(source.encode()).hexdigest(),
                    'url': manifest['repository']+'+/'+manifest['revision']+'/'+path,
                    'imports': imports, 'native_declarations': natives, 'native_includes': includes,
                    'same_package_lexical_references': local_refs})
report = {'revision': manifest['revision'], 'files': entries,
          'scope': 'Pinned source imports, native declarations/includes and same-package lexical references. Not a transitive closure, compiler/linker verification, reachability analysis, runtime port or APK compatibility proof.'}
(args.output/'dependencies.json').write_text(json.dumps(report, indent=2)+'\n')
print(json.dumps({'files': len(entries), 'bytes': sum(item['bytes'] for item in manifest['files']),
                  'native_declarations': sum(len(entry['native_declarations']) for entry in entries)}))
