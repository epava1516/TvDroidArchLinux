#!/usr/bin/env bash
set -euo pipefail
APPLY=false
case "${1:-}" in
  '') ;;
  --apply) APPLY=true ;;
  *) printf 'Uso: %s [--apply]\n' "$0" >&2; exit 2 ;;
esac
(( $# <= 1 )) || { echo 'Demasiados argumentos' >&2; exit 2; }
source /etc/os-release
[[ "$ID" == arch ]] || { echo 'Se requiere Arch Linux.' >&2; exit 1; }
run() {
  printf '+'; printf ' %q' "$@"; printf '\n'
  if "$APPLY"; then "$@"; fi
}
packages() { run sudo pacman -Syu --needed "$@"; }
manifest_packages() {
  local file=$1
  local -a names=()
  mapfile -t names < <(sed '/^[[:space:]]*#/d; /^[[:space:]]*$/d' "$file")
  ((${#names[@]} > 0)) || { echo "Manifiesto vacío: $file" >&2; exit 1; }
  packages "${names[@]}"
}
user_only() {
  (( EUID != 0 )) || { echo 'Ejecuta esta fase como usuario habitual, sin sudo.' >&2; exit 1; }
}
