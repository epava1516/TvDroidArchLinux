#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
mkdir -p "$root/reports"
pacman -Q | LC_ALL=C sort > "$root/reports/paquetes-instalados.txt"
pacman -Qqe | LC_ALL=C sort > "$root/reports/paquetes-explicitos.txt"
{
  date -u '+Fecha UTC: %Y-%m-%dT%H:%M:%SZ'
  uname -srmo
  printf '\nBinder:\n'
  grep -w binder /proc/filesystems || true
  printf '\nMemoria:\n'
  free -h
  printf '\nZram:\n'
  zramctl
} > "$root/reports/sistema.txt"
echo "Inventario actualizado en $root/reports"
