#!/usr/bin/env bash
# Run only inside a disposable systemd-nspawn runtime root, never on the host.
set -euo pipefail
[[ $EUID == 0 && $(systemd-detect-virt --container) == systemd-nspawn ]] || {
  echo 'Requires a disposable systemd-nspawn container as root.' >&2; exit 2;
}
(($# == 2)) || { echo 'Usage: package-lifecycle.sh OLD_PACKAGE_DIR NEW_PACKAGE_DIR' >&2; exit 2; }
old_dir=$(realpath "$1")
new_dir=$(realpath "$2")
names=(archtv-compositor archtv-shell archtv-session)
for name in "${names[@]}"; do
  if pacman -Q "$name" >/dev/null 2>&1; then echo "Already installed: $name" >&2; exit 1; fi
done
for compiler in rustc cargo gcc; do
  if command -v "$compiler" >/dev/null; then echo "Runtime root contains compiler: $compiler" >&2; exit 1; fi
done
shopt -s nullglob
old_packages=("$old_dir"/archtv-{compositor,shell,session}-*.pkg.tar.zst)
new_packages=("$new_dir"/archtv-{compositor,shell,session}-*.pkg.tar.zst)
((${#old_packages[@]} == 3 && ${#new_packages[@]} == 3))
old_version=$(pacman -Qp "${old_packages[0]}" | cut -d ' ' -f2)
new_version=$(pacman -Qp "${new_packages[0]}" | cut -d ' ' -f2)
[[ $(vercmp "$new_version" "$old_version") -gt 0 ]]
pacman -Syu --noconfirm
# Resolve dependencies from the actual package metadata, without build packages.
mapfile -t dependencies < <(for package in "${old_packages[@]}" "${new_packages[@]}"; do
  bsdtar -xOf "$package" .PKGINFO | sed -n 's/^depend = //p'
done | sort -u | sed '/^archtv-/d')
pacman -S --needed --noconfirm "${dependencies[@]}"
useradd -m archtv-probe
preferences=/home/archtv-probe/.config/archtv/settings.json
install -d -o archtv-probe -g archtv-probe "${preferences%/*}"
printf '%s\n' '{"version":1,"favorites":["keep.desktop"],"recent":[],"hidden":[],"reduced_motion":true}' > "$preferences"
chown archtv-probe:archtv-probe "$preferences"
chmod 600 "$preferences"
original_hash=$(sha256sum "$preferences")
inspect() {
  pacman -Qkk "${names[@]}"
  [[ -f /usr/share/wayland-sessions/archtv.desktop ]]
  for binary in /usr/bin/archtv-compositor /usr/bin/archtv-shell; do
    dependencies_output=$(ldd "$binary")
    printf '%s\n' "$dependencies_output"
    [[ "$dependencies_output" != *"not found"* ]]
    "$binary" --help
  done
  /usr/bin/archtv-session --help
  [[ $(sha256sum "$preferences") == "$original_hash" ]]
  for compiler in rustc cargo gcc; do
    if command -v "$compiler" >/dev/null; then echo "Unexpected compiler: $compiler" >&2; return 1; fi
  done
}
pacman -U --noconfirm "${old_packages[@]}"
inspect
pacman -U --noconfirm "${new_packages[@]}"
inspect
# Exercise explicit rollback as well as the forward update.
pacman -U --noconfirm "${old_packages[@]}"
inspect
mapfile -t installed_files < <(pacman -Qql "${names[@]}" | while IFS= read -r file; do
  if [[ -f "$file" || -L "$file" ]]; then printf '%s\n' "$file"; fi
done)
pacman -R --noconfirm "${names[@]}"
for file in "${installed_files[@]}"; do [[ ! -e "$file" && ! -L "$file" ]]; done
[[ $(sha256sum "$preferences") == "$original_hash" ]]
echo 'PASS: package install/update/rollback/remove and unchanged preference bytes in runtime container.'
echo 'Graphical session, schema migration and Android functionality require separate tests.'
