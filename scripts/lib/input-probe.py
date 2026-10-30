#!/usr/bin/env python3
"""Create a scoped uinput keyboard, send known evdev keys, then remove it.

Requires root for /dev/uinput. It does not type shell commands or change files.
Used only by the direct-session integration test, never installed in the session.
"""
import fcntl
import os
import struct
import time
import sys
from pathlib import Path

UI_SET_EVBIT = 0x40045564
UI_SET_KEYBIT = 0x40045565
UI_DEV_CREATE = 0x5501
UI_DEV_DESTROY = 0x5502
keys = [106, 28, 39, 29, 56, 59]  # Right, Enter, Spanish ñ, Ctrl, Alt, F1
fd = os.open('/dev/uinput', os.O_WRONLY | os.O_NONBLOCK)
created = False
try:
    fcntl.ioctl(fd, UI_SET_EVBIT, 1)  # EV_KEY
    for key in keys:
        fcntl.ioctl(fd, UI_SET_KEYBIT, key)
    description = struct.pack('80sHHHHI', b'ArchTV integration keyboard', 3, 0x1D6B, 0x5456, 1, 0)
    os.write(fd, description + bytes(1024))
    fcntl.ioctl(fd, UI_DEV_CREATE)
    created = True
    time.sleep(1.5)  # Let udev and libinput discover the device.

    def event(code, value):
        os.write(fd, struct.pack('@llHHi', 0, 0, 1, code, value))
        os.write(fd, struct.pack('@llHHi', 0, 0, 0, 0, 0))
        time.sleep(0.08)

    def wait_for(marker):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            if marker in Path(sys.argv[1]).read_text():
                return
            time.sleep(0.05)
        raise RuntimeError(f'Timed out waiting for {marker}')

    for key in keys[:2]:
        event(key, 1)
        event(key, 0)
    wait_for('CLIENT_FOCUS_ENTER popup=true')
    wait_for('POPUP_FRAME 1')
    event(39, 1)
    event(39, 0)
    wait_for('POPUP_CLOSED_BY_KEY')
    time.sleep(0.3)
    event(106, 1)
    event(106, 0)
    event(29, 1)
    event(56, 1)
    event(59, 1)
    event(59, 0)
    event(56, 0)
    event(29, 0)
    time.sleep(0.3)
finally:
    if created:
        fcntl.ioctl(fd, UI_DEV_DESTROY)
    os.close(fd)
