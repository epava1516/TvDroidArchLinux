#!/usr/bin/env python3
"""Verify real client dimensions and screen content, including orientation."""
import json
from pathlib import Path
import sys
from PIL import Image, ImageChops, ImageStat

report = Path(sys.argv[1])
results = []
for width, height in [(1280, 720), (1920, 1080), (3840, 2160)]:
    directory = report / f'{width}x{height}'
    client = Image.open(directory / 'states/home.png').convert('RGB')
    presented = Image.open(directory / 'presented.png').convert('RGB')
    assert client.size == presented.size == (width, height), directory
    errors = ImageStat.Stat(ImageChops.difference(client, presented)).mean
    # Allow a focus-pulse frame difference, but reject blank, flipped or scaled output.
    assert max(errors) < 2.0, (directory, errors)
    assert max(ImageStat.Stat(client).stddev) > 25, 'blank client image'
    results.append({'resolution': [width, height], 'presented_channel_mae': errors})
(report / 'presentation-metrics.json').write_text(json.dumps(results, indent=2) + '\n')
print('PASS: client and presented content dimensions/orientation agree at every resolution.')
