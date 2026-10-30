#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
if ! grep -qw binder /proc/filesystems && ! modinfo binder_linux >/dev/null 2>&1 && ! modinfo binder_linux_rust >/dev/null 2>&1; then
  echo 'No se detecta binderfs ni un módulo Binder para el kernel actual.' >&2
  echo 'Revisa docs/INSTALACION.md antes de continuar.' >&2
  exit 1
fi
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
manifest_packages "$root/manifests/android.txt"
run sudo waydroid init -s VANILLA
run sudo systemctl enable --now waydroid-container.service
echo 'Cuando dispongas de una sesión Wayland compatible, como usuario: waydroid session start'
echo 'En otra terminal: waydroid show-full-ui'
echo 'Detectar Binder no garantiza compatibilidad: valida logs, vídeo, audio y red.'
