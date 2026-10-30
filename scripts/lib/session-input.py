#!/usr/bin/env python3
"""Inject only the TV session shortcuts needed by the integration test."""
import fcntl
import os
import struct
import sys
import time

mode = sys.argv[1]
assert mode in ('home-resume', 'quit', 'letter')
fd = os.open('/dev/uinput', os.O_WRONLY | os.O_NONBLOCK)
created = False
try:
    fcntl.ioctl(fd, 0x40045564, 1)
    for key in (102, 28, 29, 56, 14, 30):
        fcntl.ioctl(fd, 0x40045565, key)
    os.write(fd, struct.pack('80sHHHHI', b'ArchTV session keyboard', 3, 0x1D6B, 0x5457, 1, 0) + bytes(1024))
    fcntl.ioctl(fd, 0x5501)
    created = True
    time.sleep(1.5)

    def event(code, value):
        os.write(fd, struct.pack('@llHHi', 0, 0, 1, code, value))
        os.write(fd, struct.pack('@llHHi', 0, 0, 0, 0, 0))
        time.sleep(0.08)

    if mode == 'home-resume':
        event(102, 1)
        event(102, 0)
        time.sleep(0.5)
        event(28, 1)
        event(28, 0)
    elif mode == 'letter':
        event(30, 1)
        event(30, 0)
    else:
        for key in (29, 56, 14):
            event(key, 1)
        for key in (14, 56, 29):
            event(key, 0)
    time.sleep(0.3)
finally:
    if created:
        fcntl.ioctl(fd, 0x5502)
    os.close(fd)
