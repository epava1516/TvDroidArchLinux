#!/usr/bin/env bash
# Build an explicitly selected, verified source bundle in a clean Arch chroot.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if ! "$APPLY"; then
  echo 'Compilará ARCHTV_PACKAGE_SOURCE en un chroot Arch limpio; no instala el producto en el anfitrión.'
  exit 0
fi
: "${ARCHTV_PACKAGE_SOURCE:?Indica el directorio generado por 97-package-source.sh}"
source_dir=$(realpath "$ARCHTV_PACKAGE_SOURCE")
[[ -f "$source_dir/PKGBUILD" && -f "$source_dir/SHA256SUMS" ]]
chroot_dir="${ARCHTV_PACKAGE_CHROOT:-$HOME/.cache/archtv/clean-build}"
report="${ARCHTV_PACKAGE_REPORT:-$root/reports/h8-build/$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir -p "$chroot_dir" "$report"
chroot_dir=$(realpath "$chroot_dir")
report=$(realpath "$report")
exec 9>"$chroot_dir/archtv-build.lock"
flock -n 9 || { echo 'Hay otra compilación Arch TV activa en este chroot.' >&2; exit 1; }
for command in mkarchroot makechrootpkg; do command -v "$command" >/dev/null; done
(cd "$source_dir" && sha256sum --check SHA256SUMS) | tee "$report/source-verification.txt"
cp "$source_dir/PKGBUILD" "$source_dir/SHA256SUMS" "$source_dir/source-commit.txt" "$report/"
uname -a > "$report/host-kernel.txt"
pacman -Q devtools > "$report/devtools.txt"
echo 'RUNNING: clean package build; not an installation or license clearance.' > "$report/result.txt"
trap 'echo "FAIL: inspect build logs; packaging gates remain open." > "$report/result.txt"' ERR
if [[ ! -d "$chroot_dir/root" ]]; then
  sudo -n mkarchroot "$chroot_dir/root" base-devel 2>&1 | tee "$report/chroot-create.log"
fi
(cd "$source_dir" && makechrootpkg -c -r "$chroot_dir") 2>&1 | tee "$report/build.log"
shopt -s nullglob
packages=("$source_dir"/archtv-{compositor,shell,session}-*.pkg.tar.zst)
((${#packages[@]} == 3)) || { echo 'Se esperaban exactamente tres paquetes.' >&2; false; }
(cd "$source_dir" && sha256sum archtv-{compositor,shell,session}-*.pkg.tar.zst) > "$report/package-sha256.txt"
for package in "${packages[@]}"; do
  pacman -Qip "$package"
  pacman -Qlp "$package"
done > "$report/package-inspection.txt"
echo 'PASS: clean build and package inspection. Installation, update, removal and license review remain separate gates.' > "$report/result.txt"
