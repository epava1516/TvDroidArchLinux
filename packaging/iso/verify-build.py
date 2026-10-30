#!/usr/bin/env python3
"""Reject known build failures before accepting an ISO as a boot-test candidate."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

parser = argparse.ArgumentParser()
parser.add_argument('log', type=Path)
parser.add_argument('image', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
log = args.log.read_text(errors='replace')
errors = [line.strip() for line in log.splitlines() if re.search(
    r'==> ERROR:|\[mkarchiso\] ERROR:|errors were encountered during the build|^error:|^FATAL ERROR:', line)]
if 'ISO image produced:' not in log or 'completed successfully.' not in log:
    errors.append('Missing ISO creation completion in build log.')
image_hash = None
boot_report = ''
if not args.image.is_file():
    errors.append('ISO artifact missing.')
else:
    with args.image.open('rb') as stream:
        image_hash = hashlib.file_digest(stream, 'sha256').hexdigest()
    result = subprocess.run(['xorriso', '-indev', str(args.image), '-report_el_torito', 'plain'],
                            text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    boot_report = result.stdout
    if result.returncode or not re.search(r'El Torito boot img\s*:.*\bUEFI\s+y\b', boot_report):
        errors.append('Missing enabled UEFI El Torito boot image.')
record = {'status': 'FAIL' if errors else 'CANDIDATE', 'image': args.image.name,
          'sha256': image_hash, 'errors': errors, 'el_torito_report': boot_report,
          'scope': 'Known build-error scan, ISO SHA-256 and UEFI catalog only. Does not prove initramfs correctness, boot, installation, reproducibility or Android functionality.'}
args.output.parent.mkdir(parents=True, exist_ok=True)
args.output.write_text(json.dumps(record, indent=2) + '\n')
print(json.dumps({key: record[key] for key in ('status', 'image', 'sha256', 'errors')}))
sys.exit(bool(errors))
