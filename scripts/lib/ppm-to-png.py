#!/usr/bin/env python3
"""Losslessly encode the RGB P6 screenshots produced by the DRM probe as PNG."""
from pathlib import Path
import struct
import sys
import zlib

magic, dimensions, maximum, rgb = Path(sys.argv[1]).read_bytes().split(b'\n', 3)
assert magic == b'P6' and maximum == b'255'
width, height = map(int, dimensions.split())
assert 0 < width <= 7680 and 0 < height <= 4320
assert len(rgb) == width * height * 3


def chunk(kind, data):
    return (struct.pack('>I', len(data)) + kind + data
            + struct.pack('>I', zlib.crc32(kind + data)))


rows = b''.join(b'\x00' + rgb[y * width * 3:(y + 1) * width * 3] for y in range(height))
Path(sys.argv[2]).write_bytes(
    b'\x89PNG\r\n\x1a\n'
    + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
    + chunk(b'IDAT', zlib.compress(rows)) + chunk(b'IEND', b''))
