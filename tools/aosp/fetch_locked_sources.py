#!/usr/bin/env python3
"""Fetch a bounded subtree or Git-verified file from the committed AOSP lock.

Build-time acquisition only. Preserves an archive hash and provenance; neither
source/binary equivalence nor signature verification is implied by HTTPS/hash.
"""
import argparse
import base64
import copy
import hashlib
import json
from pathlib import Path, PurePosixPath
import tarfile
import urllib.request


def fetch_file(lock, project, filename, output, max_bytes):
    """Acquire one regular upstream file and verify its exact Git blob identity."""
    if output.exists():
        raise ValueError('output exists; do not overwrite prior evidence')
    if not filename or filename.startswith('/') or any(p in ('..', '.', '') for p in filename.split('/')):
        raise ValueError('file must be an explicit relative path without traversal')
    raw_lock = lock.read_bytes()
    manifest = json.loads(raw_lock)
    matches = [p for p in manifest['projects'] if p['path'] == project]
    if len(matches) != 1 or not manifest['complete']:
        raise ValueError('project absent/ambiguous or source lock incomplete')
    entry = matches[0]
    commit = entry['commit']
    if len(commit) != 40 or any(c not in '0123456789abcdef' for c in commit):
        raise ValueError('not an exact commit')
    path = PurePosixPath(filename)
    base = f"https://android.googlesource.com/{entry['name']}/+/{commit}/"
    with urllib.request.urlopen(base+str(path.parent)+'/?format=JSON', timeout=60) as response:
        tree = json.loads(response.read(4*1024*1024)[4:])
    candidates = [e for e in tree['entries'] if e['name'] == path.name]
    if len(candidates) != 1 or candidates[0]['mode'] not in (0o100644, 0o100755):
        raise ValueError('not one regular upstream file; symlinks require explicit target acquisition')
    expected = candidates[0]
    output.mkdir(parents=True)
    artifact = output/path.name
    url = base+filename+'?format=TEXT'
    provenance = {'project': project, 'file': filename, 'commit': commit, 'url': url,
                  'lock_sha256': hashlib.sha256(raw_lock).hexdigest(), 'status': 'incomplete',
                  'expected_git_blob': expected['id'], 'signature_verified': False}
    try:
        pending = b''
        size = 0
        with urllib.request.urlopen(url, timeout=60) as response, artifact.open('xb') as stream:
            while chunk := response.read(1024*1024):
                size += len(chunk)
                if size > ((max_bytes+2)//3)*4:
                    raise ValueError('encoded upstream file exceeds explicit budget')
                pending += chunk
                length = len(pending)//4*4
                stream.write(base64.b64decode(pending[:length], validate=True))
                pending = pending[length:]
        if pending or artifact.stat().st_size > max_bytes:
            raise ValueError('incomplete encoding or decoded upstream file exceeds explicit budget')
        git_blob = hashlib.sha1(b'blob '+str(artifact.stat().st_size).encode()+b'\0')
        digest = hashlib.sha256()
        with artifact.open('rb') as stream:
            while chunk := stream.read(1024*1024):
                git_blob.update(chunk)
                digest.update(chunk)
        if git_blob.hexdigest() != expected['id']:
            raise ValueError('upstream bytes do not match exact Git tree blob')
        artifact.chmod(expected['mode'] & 0o777)
        provenance.update(status='complete', git_blob_verified=git_blob.hexdigest(),
                          sha256=digest.hexdigest(), bytes=artifact.stat().st_size,
                          artifact=str(artifact), original_file_modified=False)
    except Exception as error:
        provenance['error'] = str(error)
        raise
    finally:
        (output/'provenance.json').write_text(json.dumps(provenance, indent=2)+'\n')
    return provenance


def fetch(lock, project, subtree, output, max_bytes):
    if output.exists():
        raise ValueError('output exists; do not overwrite prior evidence')
    if not subtree or subtree.startswith('/') or (subtree != '.' and any(p in ('..', '.') for p in subtree.split('/'))):
        raise ValueError('subtree must be an explicit relative path without traversal')
    raw_lock = lock.read_bytes()
    manifest = json.loads(raw_lock)
    matches = [p for p in manifest['projects'] if p['path'] == project]
    if len(matches) != 1 or not manifest['complete']:
        raise ValueError('project absent/ambiguous or source lock incomplete')
    entry = matches[0]
    commit = entry['commit']
    if len(commit) != 40 or any(c not in '0123456789abcdef' for c in commit):
        raise ValueError('not an exact commit')
    suffix = '' if subtree == '.' else '/'+subtree
    url = f"https://android.googlesource.com/{entry['name']}/+archive/{commit}{suffix}.tar.gz"
    output.mkdir(parents=True)
    provenance = {'project': project, 'subtree': subtree, 'commit': commit, 'url': url,
                  'lock_sha256': hashlib.sha256(raw_lock).hexdigest(), 'status': 'incomplete',
                  'signature_verified': False, 'original_source_modified': False}
    record = output/'provenance.json'
    try:
        archive = output/'source.tar.gz'
        size = 0
        with urllib.request.urlopen(url, timeout=60) as response, archive.open('xb') as stream:
            while chunk := response.read(1024 * 1024):
                size += len(chunk)
                if size > max_bytes:
                    raise ValueError('compressed source archive exceeds explicit budget')
                stream.write(chunk)
        provenance.update(archive_bytes=size, archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
        tree = output/'source'
        tree.mkdir()
        prefix = PurePosixPath(project)/subtree
        source = tree/str(prefix)
        with tarfile.open(archive) as tar:
            members = tar.getmembers()
            if len(members) > 100000 or sum(m.size for m in members) > max_bytes * 8:
                raise ValueError('expanded archive exceeds file/byte budget')
            for member in members:
                path = PurePosixPath(member.name)
                if path.is_absolute() or '..' in path.parts or not (member.isfile() or member.isdir() or member.issym() or member.islnk()):
                    raise ValueError('unsupported or unsafe archive member')
            # Preserve original cross-directory links in the locked source-tree
            # layout, bounded by the private output tree rather than the subtree.
            # Missing linked sibling projects are dependencies, not invented files.
            relocated = []
            for member in members:
                item = copy.copy(member)
                item.name = str(prefix/member.name)
                if item.islnk():
                    item.linkname = str(prefix/member.linkname)
                relocated.append(item)
            tar.extractall(tree, members=relocated, filter='data')
        provenance.update(status='complete', regular_files=sum(p.is_file() and not p.is_symlink() for p in source.rglob('*')))
        provenance.update(relative_source_root=str(source.relative_to(output)),
                          unresolved_symlinks=[str(p.relative_to(tree)) for p in source.rglob('*') if p.is_symlink() and not p.exists()],
                          completeness='Original subtree only; sibling sources/generated inputs must be supplied before build')
    except Exception as error:
        provenance['error'] = str(error)
        raise
    finally:
        record.write_text(json.dumps(provenance, indent=2)+'\n')
    return provenance


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--lock', type=Path, default=Path(__file__).resolve().parents[2]/'runtime/aosp/android16-qpr2/manifest.lock.json')
    parser.add_argument('--project', required=True)
    selection = parser.add_mutually_exclusive_group(required=True)
    selection.add_argument('--subtree')
    selection.add_argument('--file')
    parser.add_argument('--output', required=True, type=Path)
    parser.add_argument('--max-mib', type=int, default=128)
    args = parser.parse_args()
    if not 1 <= args.max_mib <= 1024:
        parser.error('compressed budget must be 1..1024 MiB')
    result = (fetch_file(args.lock, args.project, args.file, args.output, args.max_mib*1024*1024)
              if args.file else fetch(args.lock, args.project, args.subtree, args.output, args.max_mib*1024*1024))
    print(json.dumps(result))


if __name__ == '__main__':
    main()
