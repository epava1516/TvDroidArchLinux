#!/usr/bin/env python3
"""Verify original UI-thread traces and compare client frames to DRM scanout captures."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('report', type=Path)
parser.add_argument('--library', type=Path, required=True)
args = parser.parse_args()
comparisons = {}
for phase, actions in [('first', ['create', 'activate', 'activate', 'quit']),
                       ('reopen', ['create', 'activate', 'quit'])]:
    directory = args.report/phase
    observed = [line for line in (directory/'art.stderr').read_text().splitlines()
                if line.startswith('APK_UI_DISPATCH ')]
    assert observed == ['APK_UI_DISPATCH '+action+' thread=main' for action in actions]
    frame = sorted((directory/'frames').glob('frame-*.png'))[-1]
    scanout = directory/'scanout.png'
    def rgb(path):
        return subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'rawvideo',
                                        '-pix_fmt', 'rgb24', '-'], timeout=20)
    actual, expected = rgb(scanout), rgb(frame)
    assert len(actual) == 1280*720*3 and actual == expected
    comparisons[phase] = {'client_frame': str(frame), 'scanout': str(scanout),
                           'size': [1280, 720], 'max_channel_difference': 0, 'ui_dispatch': actions}
(args.report/'scanout-comparison.json').write_text(json.dumps(comparisons, indent=2)+'\n')
result_path = args.report/'result.json'
result = json.loads(result_path.read_text())
result.update(original_ui_looper_pass=True, scanout_rgb_match=True)
library = args.library.resolve(strict=True)
result['sha256'][str(library)] = hashlib.sha256(library.read_bytes()).hexdigest()
result_path.write_text(json.dumps(result, indent=2)+'\n')
print('PASS: original UI dispatch traces and exact RGB scanout match')
