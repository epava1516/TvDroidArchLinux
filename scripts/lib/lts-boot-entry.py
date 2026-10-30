#!/usr/bin/env python3
"""Add a separate LTS entry derived from an existing systemd-boot entry."""
import argparse
import os
from pathlib import Path
import tempfile

parser = argparse.ArgumentParser()
parser.add_argument('source', type=Path)
parser.add_argument('destination', type=Path)
args = parser.parse_args()
if os.geteuid() != 0:
    raise SystemExit('Run with sudo after installing linux-lts.')
source = args.source
if source == args.destination:
    raise SystemExit('Use a separate diagnostic entry; preserve the existing entry.')
lines = source.read_text().splitlines()
linux = [line for line in lines if line.startswith('linux ')]
if linux != ['linux /vmlinuz-linux']:
    raise SystemExit('Expected an Arch Linux Type #1 entry using /vmlinuz-linux.')
if 'initrd /initramfs-linux.img' not in lines:
    raise SystemExit('Expected the standard Arch initramfs entry.')
new = []
for line in lines:
    if line.startswith('title '):
        line = 'title Arch TV diagnostic - Linux LTS'
    elif line == 'linux /vmlinuz-linux':
        line = 'linux /vmlinuz-linux-lts'
    elif line == 'initrd /initramfs-linux.img':
        line = 'initrd /initramfs-linux-lts.img'
    new.append(line)
for line in new:
    if line.startswith(('linux ', 'initrd ')):
        target = Path('/boot') / line.split(maxsplit=1)[1].lstrip('/')
        if not target.is_file() or target.stat().st_size == 0:
            raise SystemExit(f'Missing boot artifact: {target}')
content = '\n'.join(new) + '\n'
if args.destination.exists():
    if args.destination.read_text() != content:
        raise SystemExit('Diagnostic entry differs; preserve it for manual review.')
    print('LTS entry already matches. Default entry unchanged.')
    raise SystemExit(0)
fd, temporary = tempfile.mkstemp(dir=args.destination.parent, prefix='.archtv-lts-')
try:
    with os.fdopen(fd, 'w') as output:
        output.write(content)
        output.flush()
        os.fsync(output.fileno())
    os.chmod(temporary, 0o644)
    os.replace(temporary, args.destination)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
print(content, end='')
print('Separate entry created. Default selection unchanged; no reboot requested.')
