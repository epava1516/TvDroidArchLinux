#!/usr/bin/env python3
"""Aplicar el perfil software oficial de Waydroid, conservando copia previa."""
import configparser
import os
from pathlib import Path
import shutil
import tempfile

path = Path('/var/lib/waydroid/waydroid.cfg')
if os.geteuid() != 0:
    raise SystemExit('Se requiere root para modificar la configuración Android.')
if not path.is_file() or not (path.parent / 'images/system.img').is_file():
    raise SystemExit('Inicializa antes Waydroid y completa la descarga de imágenes.')
cfg = configparser.ConfigParser(interpolation=None)
cfg.optionxform = str
cfg.read(path)
if not cfg.has_section('properties'):
    cfg.add_section('properties')
cfg.set('properties', 'ro.hardware.gralloc', 'default')
cfg.set('properties', 'ro.hardware.egl', 'swiftshader')
backup = path.with_suffix('.cfg.archtv-backup')
if not backup.exists():
    shutil.copy2(path, backup)
fd, temporary = tempfile.mkstemp(dir=path.parent, prefix='.archtv-')
try:
    with os.fdopen(fd, 'w') as output:
        cfg.write(output)
    os.chmod(temporary, 0o644)
    os.replace(temporary, path)
finally:
    if os.path.exists(temporary):
        os.unlink(temporary)
print(f'Perfil software guardado. Copia previa: {backup}')
