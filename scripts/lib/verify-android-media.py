#!/usr/bin/env python3
"""Reject frozen captures and transient-only monitor audio in the H6 experiment."""
import argparse
import array
import cmath
import json
import math
from pathlib import Path
import sys
import wave
from PIL import Image, ImageChops, ImageStat

parser = argparse.ArgumentParser()
parser.add_argument('report', type=Path)
parser.add_argument('--output', type=Path)
args = parser.parse_args()
r = args.report
images = [Image.open(r / f'video-frame-{name}.png').convert('RGB') for name in ('a', 'b')]
assert images[0].size == images[1].size
width, height = images[0].size
# Exclude status/navigation and transient transport controls. Still inspect PNGs
# for overlays: image difference alone cannot distinguish video from a changed UI.
roi = (width // 5, height // 4, width * 4 // 5, height * 3 // 4)
difference = ImageStat.Stat(ImageChops.difference(*(im.crop(roi) for im in images))).mean
with wave.open(str(r / 'audio-monitor.wav')) as recording:
    rate = recording.getframerate()
    channels = recording.getnchannels()
    assert recording.getsampwidth() == 2, 'expected s16 monitor capture'
    samples = array.array('h', recording.readframes(recording.getnframes()))
    if sys.byteorder != 'little':
        samples.byteswap()
mono = samples[::channels]
window_size = rate // 10
windows = []
for start in range(0, len(mono) - window_size + 1, window_size):
    segment = mono[start:start + window_size]
    rms = math.sqrt(sum(value * value for value in segment) / window_size)
    # Coherent 440-Hz amplitude, well above zero for the generated sine. A startup
    # click can raise overall RMS but won't keep this tone across several seconds. Use 100-ms bins to reject long silent gaps.
    rotation = cmath.exp(-2j * math.pi * 440 / rate)
    phase = 1 + 0j
    correlation = 0j
    for value in segment:
        correlation += value * phase
        phase *= rotation
    amplitude = 2 * abs(correlation) / window_size
    windows.append({'second': start / rate, 'rms_s16': rms, 'tone_440_amplitude_s16': amplitude, 'active_fraction': sum(abs(v) > 3 for v in segment) / window_size})
longest = current = 0
for window in windows:
    current = current + 1 if window['rms_s16'] > 2 and window['tone_440_amplitude_s16'] > 2 and window['active_fraction'] >= 0.7 else 0
    longest = max(longest, current)
video_changed = max(difference) > 2
result = {'video_roi_channel_mae': difference, 'video_changed': video_changed,
          'audio_seconds': len(mono) / rate, 'audio_windows': windows,
          'longest_continuous_tone_seconds': longest * window_size / rate,
          'pass': video_changed and longest * window_size / rate >= 3,
          'scope': 'Digital monitor audio and changed Android video content; inspect PNGs for overlays. No HDMI/acoustic or performance claim.'}
(args.output or r / 'av-metrics.json').write_text(json.dumps(result, indent=2) + '\n')
print(json.dumps({'video_changed': video_changed, 'continuous_tone_seconds': result['longest_continuous_tone_seconds'], 'pass': result['pass']}))
raise SystemExit(0 if result['pass'] else 1)
