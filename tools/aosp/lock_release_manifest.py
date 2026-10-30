#!/usr/bin/env python3
"""Pin a uniform annotated AOSP release manifest using official Gitiles ref metadata.

Downloads refs only, never source checkouts or Android runtime images. Offline
mode reproduces a lock from checksummed metadata; missing refs fail explicitly.
"""
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import datetime
import hashlib
import json
from pathlib import Path
import re
import time
import urllib.error
import urllib.request
import xml.etree.ElementTree as ET


def sha(data):
    return hashlib.sha256(data).hexdigest()


def parse_ref(raw, revision):
    if len(raw) > 2*1024*1024 or not raw.startswith(b")]}'\n"):
        raise ValueError('Unsupported Gitiles envelope')
    entry = json.loads(raw[5:])[revision]
    for key in ['value', 'peeled']:
        if not isinstance(entry.get(key), str) or not re.fullmatch('[0-9a-f]{40}', entry[key]):
            raise ValueError('Release must resolve an annotated tag to a peeled commit')
    return entry['value'], entry['peeled']


def resolve_project(project, revision, cache, offline):
    name = project.get('name')
    path = project.get('path', name)
    if not name or not re.fullmatch(r'[A-Za-z0-9_./+-]+', name) or '..' in name.split('/'):
        raise ValueError('Unsupported repository name')
    if project.get('revision', revision) != revision or project.get('remote', 'aosp') != 'aosp':
        raise ValueError('This tool accepts one uniform official release tag only')
    url = 'https://android.googlesource.com/'+name+'/+refs/'+revision.removeprefix('refs/')+'?format=JSON'
    file = cache/(sha((name+'\0'+revision).encode())+'.json')
    error_text = 'Unresolved'
    for attempt in range(3):
        try:
            if file.exists():
                raw = file.read_bytes()
            elif offline:
                raise FileNotFoundError('Ref absent from offline cache')
            else:
                with urllib.request.urlopen(url, timeout=20) as response:
                    raw = response.read(2*1024*1024+1)
                parse_ref(raw, revision)
                temporary = file.with_suffix('.tmp')
                temporary.write_bytes(raw)
                temporary.replace(file)
            tag, commit = parse_ref(raw, revision)
            return {'path': path, 'name': name, 'requested_revision': revision,
                    'ref_object': tag, 'commit': commit, 'url': url,
                    'response_sha256': sha(raw), 'status': 'resolved'}
        except Exception as error:
            error_text = type(error).__name__+': '+str(error)
            if offline or isinstance(error, (KeyError, ValueError, FileNotFoundError)):
                break
            if isinstance(error, urllib.error.HTTPError) and error.code in [403, 404]:
                break
            if attempt < 2:
                time.sleep(2*(attempt+1))
    return {'path': path, 'name': name, 'url': url, 'status': 'unresolved', 'error': error_text}


def main():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--manifest', type=Path, required=True)
    p.add_argument('--expected-sha256', required=True)
    p.add_argument('--tag', required=True)
    p.add_argument('--cache', type=Path, required=True)
    p.add_argument('--output', type=Path, required=True)
    p.add_argument('--offline', action='store_true')
    p.add_argument('--workers', type=int, default=4, choices=range(1, 5))
    a = p.parse_args()
    source = a.manifest.read_bytes()
    if sha(source) != a.expected_sha256:
        raise SystemExit('Official manifest SHA256 mismatch')
    tree = ET.fromstring(source)
    revision = 'refs/tags/'+a.tag
    default = tree.find('default')
    remotes = tree.findall('remote')
    if (default is None or default.get('revision') != revision or default.get('remote') != 'aosp'
            or len(remotes) != 1 or remotes[0].get('name') != 'aosp'
            or remotes[0].get('fetch') not in ['..', 'https://android.googlesource.com/']
            or any(tree.findall(t) for t in ['include', 'extend-project', 'remove-project'])):
        raise SystemExit('Unsupported manifest topology/revision; no lock produced')
    projects = tree.findall('project')
    if (not projects or len({x.get('path', x.get('name')) for x in projects}) != len(projects)
            or len({x.get('name') for x in projects}) != len(projects)):
        raise SystemExit('No projects or duplicate checkout paths/repository names')
    a.output.mkdir(parents=True, exist_ok=False)
    a.cache.mkdir(parents=True, exist_ok=True)
    results = []
    with ThreadPoolExecutor(max_workers=a.workers) as pool:
        futures = [pool.submit(resolve_project, x, revision, a.cache, a.offline) for x in projects]
        for f in as_completed(futures):
            results.append(f.result())
    results.sort(key=lambda x: x['path'])
    complete = all(x['status'] == 'resolved' for x in results)
    report = {'tag': a.tag, 'source_manifest_sha256': sha(source),
              'checked_at': datetime.datetime.now(datetime.timezone.utc).isoformat(),
              'offline': a.offline, 'complete': complete, 'project_count': len(projects),
              'resolved_count': sum(x['status'] == 'resolved' for x in results),
              'projects': results,
              'scope': 'Gitiles annotated-tag/peeled commit identities; not tag-signature verification, object/source sync, build, artifacts, security or runtime acceptance.'}
    if complete:
        commits = {x['path']: x['commit'] for x in results}
        for project in projects:
            project.set('revision', commits[project.get('path', project.get('name'))])
        remotes[0].set('fetch', 'https://android.googlesource.com/')
        for element in tree.findall('superproject'):
            tree.remove(element)
        report['derived_changes'] = ['All project revisions replaced by exact peeled commits',
                                     'Official AOSP remote made absolute for portable repo init',
                                     'Optional superproject acceleration omitted; original manifest retained separately',
                                     'XML formatting/comments not retained in derived manifest']
        ET.indent(tree)
        destination = a.output/'manifest.lock.xml'
        ET.ElementTree(tree).write(destination, encoding='utf-8', xml_declaration=True)
        report['locked_manifest_sha256'] = sha(destination.read_bytes())
    (a.output/'manifest.lock.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'complete': complete, 'projects': len(projects), 'resolved': report['resolved_count']}))
    if not complete:
        raise SystemExit(2)


if __name__ == '__main__':
    main()
