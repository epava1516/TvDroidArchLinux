#!/usr/bin/env python3
"""Drive the native UI through a real uinput keyboard and inspect persisted results."""
import fcntl
import json
import os
import pwd
import re
import subprocess
from pathlib import Path
import struct
import sys
import time

report = Path(sys.argv[1])
config = Path(sys.argv[2]) / 'archtv/settings.json'
log = report / 'compositor.log'


def text():
    return log.read_text(errors='replace') if log.exists() else ''


def wait_for(predicate, message, timeout=8):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        if predicate():
            return
        time.sleep(0.04)
    raise RuntimeError(message)


def settings():
    try:
        return json.loads(config.read_text())
    except (OSError, ValueError):
        return {}


wait_for(lambda: 'SHELL_CATALOG applications=3' in text() and 'SHELL_FOCUS_ENTER' in text(), 'shell not ready')
fd = os.open('/dev/uinput', os.O_WRONLY | os.O_NONBLOCK)
created = False
original_volume = None
original_mute = None
original_wifi = None
owner = pwd.getpwuid(config.parents[1].stat().st_uid)

def audio(*args):
    command = ['runuser', '-u', owner.pw_name, '--', 'env',
               f'XDG_RUNTIME_DIR=/run/user/{owner.pw_uid}',
               f'DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{owner.pw_uid}/bus', 'LC_ALL=C',
               'wpctl', *args]
    return subprocess.run(command, check=True, capture_output=True, text=True, timeout=3).stdout

def volume():
    value = audio('get-volume', '@DEFAULT_AUDIO_SINK@')
    return float(re.search(r'([0-9]+\.[0-9]+)', value).group(1)), '[MUTED]' in value

def radio():
    return subprocess.run(['nmcli', 'radio', 'wifi'], check=True, capture_output=True, text=True, timeout=3).stdout.strip()

try:
    fcntl.ioctl(fd, 0x40045564, 1)
    codes = (1, 28, 14, 30, 46, 38, 23, 18, 49, 20, 57, 103, 108, 105, 106, 102, 68, 139)
    for code in codes:
        fcntl.ioctl(fd, 0x40045565, code)
    os.write(fd, struct.pack('80sHHHHI', b'ArchTV UI test remote', 3, 0x1D6B, 0x5458, 1, 0) + bytes(1024))
    fcntl.ioctl(fd, 0x5501)
    created = True
    wait_for(lambda: 'INPUT_ADDED name="ArchTV UI test remote"' in text(), 'uinput remote missing')

    def event(code, value):
        os.write(fd, struct.pack('@llHHi', 0, 0, 1, code, value))
        os.write(fd, struct.pack('@llHHi', 0, 0, 0, 0, 0))

    def key(code, hold=0.07, shell=True):
        before = len(text())
        event(code, 1)
        time.sleep(hold)
        event(code, 0)
        if shell:
            wait_for(lambda: 'SHELL_KEY' in text()[before:], f'key {code} not processed')
        time.sleep(0.07)

    def state(page, band, index):
        wait_for(lambda: f'page={page} band={band} index={index}' in text().split('SHELL_KEY')[-1], f'focus {page}/{band}/{index}')

    # Long Select opens context without launching the app.
    before = len(text())
    key(28, hold=0.9, shell=False)
    wait_for(lambda: 'SHELL_CONTEXT_OPEN' in text()[before:], 'long Select did not open context')
    assert 'SHELL_APP_LAUNCHED' not in text()[before:]
    key(28)
    wait_for(lambda: settings().get('favorites') == ['01-archtv-probe.desktop'], 'favorite A not saved')

    # Pin B, reorder it, hide it, and keep A available.
    key(108)
    key(106)
    state('Home', 3, 1)
    key(139)  # Native KEY_MENU, mapped to XF86MenuKB.
    key(28)
    wait_for(lambda: settings().get('favorites') == ['01-archtv-probe.desktop', '02-archtv-second.desktop'], 'favorite B not saved')
    key(103)
    key(106)
    key(68)
    key(108)
    key(28)
    wait_for(lambda: settings().get('favorites') == ['02-archtv-second.desktop', '01-archtv-probe.desktop'], 'favorite order not saved')
    key(68)
    for _ in range(3):
        key(108)
    key(28)
    wait_for(lambda: settings().get('hidden') == ['02-archtv-second.desktop'], 'hidden app not saved')

    # Physical search, then clear it and use the on-screen keyboard to enter A.
    for code in (46, 38, 23, 18, 49, 20, 18, 57, 30):
        key(code)
    state('Search', 1, 0)
    for _ in range(9):
        key(14)
    key(108)
    key(28)  # A in the second keyboard row.
    key(108)
    key(108)
    key(106)
    key(106)
    key(28)  # Tick: switch to search results.
    state('Search', 2, 0)
    before = len(text())
    key(28)
    wait_for(lambda: 'SHELL_APP_LAUNCHED id=01-archtv-probe.desktop' in text()[before:] and 'SHELL_FOCUS_LEAVE' in text()[before:], 'app launch or focus failed')
    wait_for(lambda: settings().get('recent', [None])[0] == '01-archtv-probe.desktop', 'recent launch not saved')

    terminal_receipt = config.parents[2] / 'terminal-typed.txt'
    wait_for(lambda: terminal_receipt.with_name('terminal-ready.txt').exists(), 'Foot terminal program not ready')
    key(30, shell=False)  # Type into the real Foot terminal, not the shell.
    wait_for(lambda: terminal_receipt.exists() and terminal_receipt.read_text() == 'a', 'Foot did not receive keyboard input')

    # Global Home returns to the previous row and search result.
    before = len(text())
    key(102, shell=False)
    wait_for(lambda: 'SHELL_FOCUS_ENTER page=Search band=2 index=0' in text()[before:], 'Home did not restore row focus')
    key(1)
    for _ in range(5):
        key(106)
    key(108)
    state('Settings', 1, 0)
    original_volume, original_mute = volume()
    key(28)  # Volume -5 through the shell worker.
    wait_for(lambda: abs(volume()[0] - max(0, original_volume - 0.05)) < 0.015, 'volume down failed')
    key(108)
    key(28)
    wait_for(lambda: abs(volume()[0] - original_volume) < 0.015, 'volume up failed')
    key(108)
    key(28)
    wait_for(lambda: volume()[1] is not original_mute, 'mute toggle failed')
    key(28)
    wait_for(lambda: volume()[1] is original_mute, 'mute restore failed')
    key(108)
    devices = subprocess.run(['nmcli', '-t', '-f', 'TYPE,STATE', 'device'], check=True, capture_output=True, text=True, timeout=3).stdout
    assert 'wifi:connected' not in devices, 'Wi-Fi radio test requires a wired development connection'
    original_wifi = radio()
    key(28)
    wait_for(lambda: radio() != original_wifi, 'Wi-Fi radio toggle failed')
    key(28)
    wait_for(lambda: radio() == original_wifi, 'Wi-Fi radio restore failed')
    for _ in range(2):
        key(108)
    key(28)
    wait_for(lambda: settings().get('hidden') == [], 'restore hidden failed')
    key(108)
    key(28)
    wait_for(lambda: settings().get('reduced_motion') is False, 'motion preference not saved')
    key(28)
    wait_for(lambda: settings().get('reduced_motion') is True, 'reduced motion not restored')
    key(1)
    key(1)  # Back from Home navigation resumes the background app.
    before = len(text())
    key(1, shell=False)  # The test app closes on Escape.
    wait_for(lambda: 'TV_APP_CLOSED_HOME' in text()[before:] and 'SHELL_FOCUS_ENTER' in text()[before:], 'closing app did not restore shell')
    (report / 'ui-sequence.txt').write_text('PASS: long Select, favorites/order/hide/restore, physical and on-screen search, real Foot launch/input, recents, Home, resume, close, reduced motion, real PipeWire volume/mute and Wi-Fi radio toggle/restore.\n')
finally:
    if original_volume is not None:
        audio('set-volume', '@DEFAULT_AUDIO_SINK@', str(original_volume))
        audio('set-mute', '@DEFAULT_AUDIO_SINK@', '1' if original_mute else '0')
    if original_wifi is not None and radio() != original_wifi:
        subprocess.run(['nmcli', 'radio', 'wifi', 'on' if original_wifi == 'enabled' else 'off'], check=True, timeout=3)
    if created:
        fcntl.ioctl(fd, 0x5502)
    os.close(fd)
