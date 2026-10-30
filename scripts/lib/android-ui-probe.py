#!/usr/bin/env python3
"""Exercise Android entry points through actual libinput/Wayland shell input."""
import fcntl
import os
from pathlib import Path
import struct
import sys
import time

report = Path(sys.argv[1])
mode = sys.argv[2]
assert mode in ('start', 'vlc', 'home', 'resume', 'android')
log = report / 'compositor.log'
def text():
    return log.read_text(errors='replace')
def wait_for(predicate, message, timeout=12):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(0.05)
    raise RuntimeError(message)
wait_for(lambda: 'SHELL_FOCUS_ENTER' in text(), 'shell missing')
fd = os.open('/dev/uinput', os.O_WRONLY | os.O_NONBLOCK)
created = False
try:
    fcntl.ioctl(fd, 0x40045564, 1)
    for code in (1, 28, 38, 46, 47, 102, 103, 105, 106, 108):
        fcntl.ioctl(fd, 0x40045565, code)
    os.write(fd, struct.pack('80sHHHHI', b'ArchTV Android test remote', 3, 0x1D6B, 0x5459, 1, 0) + bytes(1024))
    offset = len(text())
    fcntl.ioctl(fd, 0x5501)
    created = True
    wait_for(lambda: 'INPUT_ADDED name="ArchTV Android test remote"' in text()[offset:], 'remote missing')
    def key(code, shell=True):
        before = len(text())
        for value in (1, 0):
            os.write(fd, struct.pack('@llHHi', 0, 0, 1, code, value))
            os.write(fd, struct.pack('@llHHi', 0, 0, 0, 0, 0))
            time.sleep(0.08)
        if shell:
            wait_for(lambda: 'SHELL_KEY' in text()[before:], f'key {code} missing')
        time.sleep(0.15)
    if mode == 'start':
        key(1)
        for _ in range(5):
            key(106)
        key(108)
        for _ in range(7):
            key(108)
        assert 'page=Settings band=1 index=7' in text().split('SHELL_KEY')[-1]
        before = len(text())
        key(28)
        wait_for(lambda: 'SHELL_NOTICE Arrancando Android' in text()[before:], 'Android start action missing')
    elif mode == 'vlc':
        for code in (47, 38, 46):
            key(code)
        for _ in range(10):
            key(106)
        before = len(text())
        key(28)
        wait_for(lambda: 'SHELL_APP_STARTED' in text()[before:] and 'org.videolan.vlc' in text()[before:], 'VLC launch missing')
    elif mode == 'home':
        before = len(text())
        key(102, shell=False)
        wait_for(lambda: 'TV_HOME' in text()[before:] and text().rfind('SHELL_FOCUS_ENTER') > text().rfind('SHELL_FOCUS_LEAVE'), 'Home did not focus shell')
    elif mode == 'android':
        codes = {'up': 103, 'down': 108, 'left': 105, 'right': 106, 'select': 28, 'back': 1}
        for name in sys.argv[3:]:
            key(codes[name], shell=False)
    else:
        key(1)
        before = len(text())
        key(1)
        wait_for(lambda: 'SESSION_CONTROL RESUME' in text()[before:] or 'SHELL_FOCUS_LEAVE' in text()[before:], 'Resume missing')
    with (report / 'ui-sequence.txt').open('a') as output:
        output.write(f'PASS: {mode} through uinput -> libinput -> compositor -> shell.\n')
finally:
    if created:
        fcntl.ioctl(fd, 0x5502)
    os.close(fd)
