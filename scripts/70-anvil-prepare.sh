#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
lab="${ARCHTV_LAB_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/archtv}"
source_dir="$lab/smithay"
revision=$(cat "$root/lab/anvil/revision.txt")
[[ "$revision" =~ ^[0-9a-f]{40}$ ]] || exit 1
if [[ ! -d "$source_dir/.git" ]]; then
  run mkdir -p "$lab"
  run git init --initial-branch=lab "$source_dir"
  run git -C "$source_dir" remote add origin https://github.com/Smithay/smithay.git
elif [[ -n "$(git -C "$source_dir" status --porcelain)" ]]; then
  echo 'El checkout de laboratorio tiene cambios: revísalos antes de continuar.' >&2
  exit 1
fi
if [[ -d "$source_dir/.git" && "$(git -C "$source_dir" remote get-url origin)" != https://github.com/Smithay/smithay.git ]]; then
  echo 'El remoto del checkout de laboratorio no es Smithay.' >&2
  exit 1
fi
run git -C "$source_dir" fetch --depth=1 origin "$revision"
run git -C "$source_dir" checkout --detach "$revision"
run cp "$root/lab/anvil/Cargo.lock" "$source_dir/Cargo.lock"
echo "Fuentes de laboratorio: $source_dir"
