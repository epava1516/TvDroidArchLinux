#!/usr/bin/env python3
"""Check every pixel in the actual DRM PPM; retain a lossless PNG preview."""
from pathlib import Path
import hashlib
import json
import struct
import sys
import zlib

source = Path(sys.argv[1]).resolve()
out = Path(__file__).resolve().parent
data = source.read_bytes()
magic, dims, maximum, raw = data.split(b'\n', 3)
width, height = map(int, dims.split())
assert magic == b'P6' and maximum == b'255'
assert (width, height) == (1280, 800) and len(raw) == width * height * 3
mismatches = 0
for y in range(height):
    for x in range(width):
        expected = ((255, 255, 255) if x >= width//2 else (0, 0, 255)) if y >= height//2 else (
            (0, 255, 0) if x >= width//2 else (255, 0, 0))
        offset = (y * width + x) * 3
        mismatches += raw[offset:offset+3] != bytes(expected)
result = {'width': width, 'height': height, 'pixels_checked': width * height,
          'mismatches': mismatches, 'ppm': str(source),
          'ppm_sha256': hashlib.sha256(data).hexdigest(),
          'expected': 'GraphicBuffer RGBA red/green/blue/white quadrants, all actual captured RGB bytes.',
          'scope': 'Original allocator/mapper + HWC3 CPU/Wayland through Rust/Smithay DRM; not fence timing or APK compatibility.'}
(out / 'pixel-validation.json').write_text(json.dumps(result, indent=2) + '\n')
assert mismatches == 0, result


def chunk(kind, body):
    return struct.pack('!I', len(body)) + kind + body + struct.pack('!I', zlib.crc32(kind + body))


# Lossless container conversion, no color changes, replacements or new pixels.
scanlines = b''.join(b'\0' + raw[y*width*3:(y+1)*width*3] for y in range(height))
png = b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('!2I5B', width, height, 8, 2, 0, 0, 0))
png += chunk(b'IDAT', zlib.compress(scanlines)) + chunk(b'IEND', b'')
(out / 'screen.png').write_bytes(png)
print(json.dumps(result))
