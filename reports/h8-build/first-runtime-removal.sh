#!/usr/bin/env bash
set -euo pipefail
[[ $(systemd-detect-virt --container) == systemd-nspawn ]]
names=(archtv-compositor archtv-shell archtv-session)
pacman -Q "${names[@]}"
preferences=/home/archtv-removal-probe/.config/archtv/settings.json
install -d -m700 "${preferences%/*}"
printf '%s\n' '{"version":1,"favorites":["keep.desktop"],"reduced_motion":true}' > "$preferences"
chmod 600 "$preferences"
original=$(sha256sum "$preferences")
mapfile -t files < <(pacman -Qql "${names[@]}" | while IFS= read -r file; do
  if [[ -f "$file" || -L "$file" ]]; then printf '%s\n' "$file"; fi
done)
((${#files[@]} > 0))
pacman -R --noconfirm "${names[@]}"
for file in "${files[@]}"; do [[ ! -e "$file" && ! -L "$file" ]]; done
for name in "${names[@]}"; do
  if pacman -Q "$name" >/dev/null 2>&1; then exit 1; fi
done
[[ $(sha256sum "$preferences") == "$original" ]]
printf 'Removed package files checked: %s\n' "${#files[@]}"
printf '%s\n' "$original" 'PASS: first package removal leaves preference bytes intact; package files and registration removed.'
