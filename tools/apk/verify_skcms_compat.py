#!/usr/bin/env python3
"""Verify every binary16 pattern through the compiler compatibility intrinsic."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
source = root/'runtime/aosp/native/skcms-clang-compat-probe.cpp'
header = source.with_name('skcms-clang-compat.h')
command = ['clang++', '-std=c++17', '-O1', str(source), '-o', str(out/'probe')]
with (out/'build.log').open('w') as log:
    subprocess.run(command, stdout=log, stderr=subprocess.STDOUT, check=True, timeout=60)
run = subprocess.run([str(out/'probe')], capture_output=True, text=True, timeout=30)
(out/'probe.stdout').write_text(run.stdout)
(out/'probe.stderr').write_text(run.stderr)
expected = 'SKCMS_F16C_COMPAT_OK half_patterns=65536 simd=1'
passed = run.returncode == 0 and expected in run.stdout
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
(out/'result.json').write_text(json.dumps({
    'all_binary16_patterns_pass': passed, 'exit_code': run.returncode,
    'scope': 'AVX2/F16C conversion compared bitwise with a scalar IEEE binary16 reference; no Skia/HWUI runtime claim',
    'command': command, 'compiler': subprocess.check_output(['clang++', '--version'], text=True),
    'source_sha256': sha(source), 'header_sha256': sha(header),
    'verifier_sha256': sha(Path(__file__)), 'executable_sha256': sha(out/'probe'),
}, indent=2)+'\n')
if not passed:
    raise SystemExit('F16C compatibility unverified; inspect probe.stderr and result.json')
print(expected)
