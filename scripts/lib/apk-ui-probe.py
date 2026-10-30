#!/usr/bin/env python3
"""Drive the owned APK through uinput, libinput and the Rust Wayland client."""
import fcntl
import os
import hashlib
import json
import re
import subprocess
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


def wait_frame_after(marker):
    deadline = time.monotonic()+60
    while time.monotonic() < deadline:
        text = log.read_text()
        position = text.find(marker)
        if position >= 0:
            frame = re.search(r'^APK_FRAME (\d+) ', text[position:], re.MULTILINE)
            if frame:
                return report/'frames'/('frame-'+frame.group(1).zfill(4)+'.png')
        time.sleep(0.05)
    raise RuntimeError('No committed client frame after '+marker)


def capture_matching(frame):
    expected = subprocess.check_output(['ffmpeg', '-v', 'error', '-i', str(frame),
        '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-'], timeout=20)
    attempts = []
    deadline = time.monotonic()+30
    while time.monotonic() < deadline:
        request = report/'capture.request'
        request.write_text('capture\n')
        while request.exists() and time.monotonic() < deadline:
            time.sleep(0.05)
        if request.exists():
            raise RuntimeError('DRM capture request timed out')
        ppm = (report/'scanout.ppm').read_bytes()
        header, dimensions, maximum, pixels = ppm.split(b'\n', 3)
        assert header == b'P6' and maximum == b'255'
        width, height = map(int, dimensions.split())
        assert len(pixels) == width*height*3 == len(expected)
        differences = sum(a != b for a, b in zip(pixels, expected))
        attempts.append({'client_frame':frame.name, 'different_channels':differences,
            'scanout_rgb_sha256':hashlib.sha256(pixels).hexdigest()})
        (report/'capture-attempts.json').write_text(json.dumps(attempts,indent=2)+'\n')
        if differences == 0:
            return
        (report/('scanout-attempt-'+str(len(attempts))+'.ppm')).write_bytes(ppm)
    raise RuntimeError('DRM scanout never matched the final client frame')


wait('APK_FOCUS_ENTER')
wait('APK_FRAME 1 ')
wait('text: Some("Contador: '+str(initial)+'")')
device_name = "ArchTV APK test keyboard "+str(os.getpid())
fd = os.open('/dev/uinput', os.O_WRONLY | os.O_NONBLOCK)
created = False
try:
    fcntl.ioctl(fd, 0x40045564, 1)
    for key in (1, 28, 57):
        fcntl.ioctl(fd, 0x40045565, key)
    os.write(fd, struct.pack('80sHHHHI', device_name.encode(), 3, 0x1D6B, 0x5459, 1, 0)+bytes(1024))
    fcntl.ioctl(fd, 0x5501)
    created = True
    wait('INPUT_ADDED name="'+device_name+'"')

    def key(code):
        for value in (1, 0):
            os.write(fd, struct.pack('@llHHi', 0, 0, 1, code, value))
            os.write(fd, struct.pack('@llHHi', 0, 0, 0, 0, 0))
            time.sleep(0.08)

    key(28)
    final_frame = wait_frame_after('text: Some("Contador: '+str(initial+1)+'")')
    if initial == 0:
        key(57)
        final_frame = wait_frame_after('text: Some("Contador: 2")')
    capture_matching(final_frame)
    key(1)
    wait('APK_HOST_STOPPED')
finally:
    if created:
        fcntl.ioctl(fd, 0x5502)
    os.close(fd)
