#!/usr/bin/env python3
"""Stage a fresh UEFI Archiso laboratory profile from explicit inputs only."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

parser = argparse.ArgumentParser()
parser.add_argument('repository', type=Path)
parser.add_argument('output', type=Path)
args = parser.parse_args()
repository = args.repository.resolve()
output = args.output.resolve()
manifest = json.loads((repository / 'manifest.json').read_text())
expected = {'archtv-compositor', 'archtv-shell', 'archtv-session'}
if {item['name'] for item in manifest['packages']} != expected or len(manifest['packages']) != 3:
    raise SystemExit('Repository must contain exactly the three TV packages.')
subprocess.run(['sha256sum', '--check', 'SHA256SUMS'], cwd=repository, check=True)
version = subprocess.check_output(['pacman', '-Q', 'archiso'], text=True).strip()
if version != 'archiso 91-1':
    raise SystemExit('Profile currently reviewed against archiso 91-1 only.')
template = Path('/usr/share/archiso/configs/releng')
output.mkdir(parents=True, exist_ok=False)
(output / 'profiledef.sh').write_text('''#!/usr/bin/env bash
# shellcheck disable=SC2034
iso_name="archtv-lab"
iso_label="ARCHTV_LAB"
iso_publisher="Arch TV project"
iso_application="Arch TV development and installation laboratory"
iso_version="0.1.0"
install_dir="arch"
bootmodes=('uefi.systemd-boot')
pacman_conf="pacman.conf"
airootfs_image_type="squashfs"
airootfs_image_tool_options=('-comp' 'zstd' '-Xcompression-level' '6' '-processors' '1')
file_permissions=(["/etc/shadow"]="0:0:400")
''')
packages = '''base linux-lts mkinitcpio mkinitcpio-archiso arch-install-scripts dosfstools e2fsprogs efibootmgr gptfdisk networkmanager pipewire pipewire-alsa pipewire-pulse wireplumber sudo foot waydroid'''.split()
(output / 'packages.x86_64').write_text('\n'.join(sorted(set(packages) | expected)) + '\n')
config = (template / 'pacman.conf').read_text()
config += f'\n[archtv]\nSigLevel = Never\nServer = {repository.as_uri()}\n'
(output / 'pacman.conf').write_text(config)
files = {
    'efiboot/loader/loader.conf': 'timeout 5\ndefault 01-archtv.conf\n',
    'efiboot/loader/entries/01-archtv.conf': '''title Arch TV laboratory (UEFI, LTS)
linux /%INSTALL_DIR%/boot/%ARCH%/vmlinuz-linux-lts
initrd /%INSTALL_DIR%/boot/%ARCH%/initramfs-linux-lts.img
options archisobasedir=%INSTALL_DIR% archisosearchuuid=%ARCHISO_UUID%
''',
    'airootfs/etc/hostname': 'archtv-live\n',
    'airootfs/etc/locale.conf': 'LANG=C.UTF-8\n',
    'airootfs/etc/shadow': 'root::14871::::::\n',
    'airootfs/etc/mkinitcpio.conf.d/archiso.conf': '''HOOKS=(base udev microcode modconf kms archiso archiso_loop_mnt block filesystems keyboard)
COMPRESSION="zstd"
''',
    'airootfs/etc/motd': '''Arch TV laboratory. Local root console, no password; no SSH server enabled.
No automatic disk installation. Installed-user setup and Android initialization are pending.
This image is a development candidate, not a validated distribution release.
''',
}
for relative, content in files.items():
    path = output / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
# Keep the live system's pacman configuration free of build-host paths.
runtime_config = output / 'airootfs/etc/pacman.conf'
runtime_config.write_text((template / 'pacman.conf').read_text())
unit = output / 'airootfs/etc/systemd/system/multi-user.target.wants/NetworkManager.service'
unit.parent.mkdir(parents=True, exist_ok=True)
unit.symlink_to('/usr/lib/systemd/system/NetworkManager.service')
provenance = {'archiso': version, 'repository': manifest,
              'official_pacman_template_sha256': hashlib.sha256((template / 'pacman.conf').read_bytes()).hexdigest(),
              'scope': 'Staged laboratory profile only; no ISO build, boot or installation claim. No host home or Android data copied.'}
(output / 'profile-provenance.json').write_text(json.dumps(provenance, indent=2) + '\n')
subprocess.run(['bash', '-n', str(output / 'profiledef.sh')], check=True)
print(output)
