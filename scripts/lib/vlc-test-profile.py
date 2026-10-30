#!/usr/bin/env python3
"""Configure only the installed VLC test APK while its container is stopped."""
import argparse
import os
from pathlib import Path
import stat
import subprocess
import tempfile
import xml.etree.ElementTree as ET

parser = argparse.ArgumentParser()
parser.add_argument('preferences', type=Path)
parser.add_argument('report', type=Path)
args = parser.parse_args()
if os.geteuid() != 0:
    raise SystemExit('Run with sudo; Android app preferences retain their original UID.')
state = subprocess.check_output(['lxc-info', '-P', '/var/lib/waydroid/lxc', '-n', 'waydroid', '-sH'], text=True).strip()
if state != 'STOPPED':
    raise SystemExit('Stop the Android container before changing test app preferences.')
path = args.preferences
if path.name != 'org.videolan.vlc_preferences.xml' or path.parent.name != 'shared_prefs':
    raise SystemExit('Expected VLC test APK shared preferences path.')
metadata = path.stat()
if metadata.st_size > 1024 * 1024:
    raise SystemExit('Unexpected preferences size.')
args.report.mkdir(parents=True, exist_ok=True)
backup = args.report / 'vlc-preferences-before.xml'
if backup.exists():
    raise SystemExit('Use a fresh report directory to preserve the previous backup.')
backup.write_bytes(path.read_bytes())
tree = ET.parse(path)
root = tree.getroot()
# Return from the experimental output backend to the APK default.
backend = root.find("*[@name='aout']")
if backend is not None:
    root.remove(backend)
for name, tag, value in [('tv_ui', 'boolean', 'true'),
                         ('video_player_tips_shown', 'boolean', 'true'),
                         ('VideoPaused', 'boolean', 'false'),
                         ('hardware_acceleration', 'string', '0')]:
    old = root.find(f"*[@name='{name}']")
    if old is not None:
        root.remove(old)
    node = ET.SubElement(root, tag, {'name': name})
    if tag == 'boolean':
        node.set('value', value)
    else:
        node.text = value
fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.archtv-test-')
try:
    with os.fdopen(fd, 'wb') as output:
        tree.write(output, encoding='utf-8', xml_declaration=True)
        output.flush()
        os.fsync(output.fileno())
    os.chown(temporary, metadata.st_uid, metadata.st_gid)
    os.chmod(temporary, stat.S_IMODE(metadata.st_mode))
    os.replace(temporary, path)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
(args.report / 'vlc-preferences-profile.xml').write_bytes(path.read_bytes())
print('Configured VLC TV/software test profile; preferences backup retained.')
