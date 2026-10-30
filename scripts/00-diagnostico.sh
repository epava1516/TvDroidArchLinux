#!/usr/bin/env bash
set -euo pipefail
(( $# == 0 )) || { echo "Uso: $0" >&2; exit 2; }
probe() {
  printf '\n'; printf '$'; printf ' %q' "$@"; printf '\n'
  "$@" || printf 'Comprobación no disponible o estado pendiente.\n'
}
probe uname -a
probe lsblk -o NAME,SIZE,FSTYPE,MOUNTPOINTS
probe findmnt --verify
probe free -h
probe swapon --show
probe timedatectl status
probe systemctl is-active NetworkManager systemd-timesyncd
probe nmcli general status
probe systemctl --failed --no-pager
probe lspci -k
probe sh -c 'grep -w binder /proc/filesystems'
probe modinfo binder_linux
probe modinfo binder_linux_rust
probe systemctl --user status pipewire.socket pipewire-pulse.socket wireplumber.service --no-pager
echo 'Diagnóstico terminado. Revisa los resultados; no certifica la instalación.'
