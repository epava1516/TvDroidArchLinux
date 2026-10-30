#!/usr/bin/env python3
"""Verify original UI-thread traces and compare client frames to DRM scanout captures."""
import argparse
import hashlib
import json
from pathlib import Path
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('report', type=Path)
parser.add_argument('--resources-library', type=Path, required=True)
parser.add_argument('--library', type=Path, required=True)
args = parser.parse_args()
result_path = args.report/'result.json'
result = json.loads(result_path.read_text())
size = result['resolution']
assert size in ([1280, 720], [1920, 1080])
comparisons = {}
for phase, actions in [('first', ['create', 'activate', 'activate', 'quit']),
                       ('reopen', ['create', 'activate', 'quit'])]:
    directory = args.report/phase
    assert (directory/'art.stderr').read_text().count('APK_RESOURCES_AOSP_READY') == 1
    assert (directory/'art.stderr').read_text().count('APK_PUBLIC_RESOURCES_AOSP_READY') == 1
    assert (directory/'art.stderr').read_text().count('APK_HOST_PROFILE sdk=33 abi=x86_64') == 1
    observed = [line for line in (directory/'art.stderr').read_text().splitlines()
                if line.startswith('APK_UI_DISPATCH ')]
    assert observed == ['APK_UI_DISPATCH '+action+' thread=main' for action in actions]
    displays = [line for line in (directory/'compositor.log').read_text().splitlines() if line.startswith('APK_DISPLAY ')]
    assert displays == [f'APK_DISPLAY {size[0]}x{size[1]}'] * (len(actions)-1)
    frame = sorted((directory/'frames').glob('frame-*.png'))[-1]
    scanout = directory/'scanout.png'
    def rgb(path):
        return subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(path), '-f', 'rawvideo',
                                        '-pix_fmt', 'rgb24', '-'], timeout=20)
    actual, expected = rgb(scanout), rgb(frame)
    assert len(actual) == size[0]*size[1]*3 and actual == expected
    comparisons[phase] = {'client_frame': str(frame), 'scanout': str(scanout),
                           'size': size, 'max_channel_difference': 0, 'ui_dispatch': actions}
(args.report/'scanout-comparison.json').write_text(json.dumps(comparisons, indent=2)+'\n')
result.update(original_ui_looper_pass=True, original_resources_pass=True, original_public_resources_pass=True, scanout_rgb_match=True, initial_wayland_metrics_pass=True)
library = args.library.resolve(strict=True)
result['sha256'][str(library)] = hashlib.sha256(library.read_bytes()).hexdigest()
resources_library = args.resources_library.resolve(strict=True)
result['sha256'][str(resources_library)] = hashlib.sha256(resources_library.read_bytes()).hexdigest()
result_path.write_text(json.dumps(result, indent=2)+'\n')
print('PASS: original UI dispatch traces and exact RGB scanout match')
