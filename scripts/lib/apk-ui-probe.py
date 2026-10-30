#!/usr/bin/env python3
"""Drive the owned APK through uinput, libinput and the Rust Wayland client."""
import fcntl
import os
from pathlib import Path
import struct
import sys
import time

report = Path(sys.argv[1])
initial = int(sys.argv[2])
log = report/'compositor.log'


def wait(marker, seconds=60):
    deadline = time.monotonic()+seconds
    while time.monotonic() < deadline:
        if log.exists() and marker in log.read_text():
            return
        time.sleep(0.05)
    raise RuntimeError('Timed out waiting for '+marker)


wait('APK_FOCUS_ENTER')
wait('APK_FRAME 1 ')
wait('text: Some("Contador: '+str(initial)+'")')
fd = os.open('/dev/uinput', os.O_WRONLY | os.O_NONBLOCK)
created = False
try:
    fcntl.ioctl(fd, 0x40045564, 1)
    for key in (1, 28, 57):
        fcntl.ioctl(fd, 0x40045565, key)
    os.write(fd, struct.pack('80sHHHHI', b'ArchTV APK test keyboard', 3, 0x1D6B, 0x5459, 1, 0)+bytes(1024))
    fcntl.ioctl(fd, 0x5501)
    created = True
    time.sleep(1.5)

    def key(code):
        for value in (1, 0):
            os.write(fd, struct.pack('@llHHi', 0, 0, 1, code, value))
            os.write(fd, struct.pack('@llHHi', 0, 0, 0, 0, 0))
            time.sleep(0.08)

    key(28)
    wait('text: Some("Contador: '+str(initial+1)+'")')
    wait('APK_FRAME 2 ')
    if initial == 0:
        key(57)
        wait('text: Some("Contador: 2")')
        wait('APK_FRAME 3 ')
    deadline = time.monotonic()+30
    while not (report/'scanout.ppm').exists() and time.monotonic() < deadline:
        time.sleep(0.1)
    if not (report/'scanout.ppm').exists():
        raise RuntimeError('No DRM scanout capture')
    key(1)
    wait('APK_HOST_STOPPED')
finally:
    if created:
        fcntl.ioctl(fd, 0x5502)
    os.close(fd)
