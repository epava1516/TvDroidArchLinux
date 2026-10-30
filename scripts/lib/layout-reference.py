#!/usr/bin/env python3
"""Normalize the selected reference for local analysis and report measured geometry.

The Amazon photo is only written beneath the user's cache. It is not copied
into the repository or the distributed TV asset directory.
"""
import argparse
import hashlib
import json
from pathlib import Path
from PIL import Image, ImageDraw

parser = argparse.ArgumentParser()
parser.add_argument('reference', type=Path)
parser.add_argument('shell', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
args.output.mkdir(parents=True, exist_ok=True)
photo = Image.open(args.reference).convert('RGB')
assert photo.size == (1600, 900), 'unexpected reference version'
reference = photo.crop((164, 80, 1436, 795)).resize((1920, 1080), Image.Resampling.LANCZOS)
screen = Image.open(args.shell).convert('RGB')
assert screen.width * 9 == screen.height * 16, 'comparison requires a 16:9 shell capture'
screen = screen.resize((1920, 1080), Image.Resampling.LANCZOS)
cache = Path.home() / '.cache/archtv/references/normalized'
cache.mkdir(parents=True, exist_ok=True)
reference.save(cache / 'fire-tv-home-1920x1080.png')

# Photo coordinates are manually read, ±3 source pixels. Targets are inner bounds.
landmarks = {
    'home_nav': {'photo': [348, 109, 43, 44], 'target': [277, 43, 66, 66]},
    'hero_button': {'photo': [232, 403, 138, 43], 'target': [104, 488, 210, 64]},
    'featured_card': {'photo': [232, 482, 214, 121], 'target': [104, 608, 324, 184]},
    'app_card': {'photo': [232, 620, 99, 55], 'target': [104, 816, 150, 84]},
    'bottom_banner': {'photo': [232, 690, 1134, 90], 'target': [104, 922, 1712, 135]},
}
for item in landmarks.values():
    x, y, width, height = item['photo']
    item['normalized_reference'] = [(x - 164) * 1920 / 1272, (y - 80) * 1080 / 715,
                                    width * 1920 / 1272, height * 1080 / 715]
    item['target_minus_reference'] = [a - b for a, b in zip(item['target'], item['normalized_reference'])]


def white_button_bounds(image):
    pixels = image.load()
    points = [(x, y) for y in range(475, 565) for x in range(80, 350)
              if min(pixels[x, y]) > 220 and max(pixels[x, y]) - min(pixels[x, y]) < 30]
    assert points, 'hero CTA not detected in expected area'
    x0, y0 = min(x for x, _ in points), min(y for _, y in points)
    x1, y1 = max(x for x, _ in points), max(y for _, y in points)
    return [x0, y0, x1 - x0 + 1, y1 - y0 + 1]


observed = {'reference_cta': white_button_bounds(reference), 'shell_cta': white_button_bounds(screen)}
report = {'reference_url': 'https://assets.aboutamazon.com/1d/49/e027bbeb4eec97f0248687ed3ac1/aa-jan2026-firetv-inline-v2b-ui-home-1600x900.jpg',
          'reference_sha256': hashlib.sha256(args.reference.read_bytes()).hexdigest(),
          'reference_ui_crop': [164, 80, 1272, 715],
          'method': 'manual photo landmarks ±3 source px; normalized to 1920x1080; actual CTA detected by neutral white pixels',
          'landmarks': landmarks, 'observed': observed,
          'scope': 'layout only; artwork, labels and application content intentionally differ; not pixel equality'}
(args.output / 'layout-metrics.json').write_text(json.dumps(report, indent=2) + '\n')
overlay = screen.copy()
draw = ImageDraw.Draw(overlay)
for name, item in landmarks.items():
    x, y, w, h = item['normalized_reference']
    draw.rectangle((x, y, x + w, y + h), outline='#ff8855', width=3)
    draw.text((x + 4, y + 4), name, fill='#ffbb88')
    x, y, w, h = item['target']
    draw.rectangle((x, y, x + w, y + h), outline='#55ddee', width=2)
overlay.save(args.output / 'layout-overlay.png')
print(json.dumps(observed))
