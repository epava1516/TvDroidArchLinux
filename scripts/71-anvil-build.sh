#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
lab="${ARCHTV_LAB_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/archtv}"
source_dir="$lab/smithay"
if ! "$APPLY"; then
  echo "Compilará $source_dir con Cargo.lock fijado, winit, jobs=1 y debug=0."
  exit 0
fi
[[ "$(git -C "$source_dir" rev-parse HEAD)" == "$(cat "$root/lab/anvil/revision.txt")" ]] || exit 1
cp "$root/lab/anvil/Cargo.lock" "$source_dir/Cargo.lock"
mkdir -p "$root/reports"
{
  date -u '+Fecha UTC: %Y-%m-%dT%H:%M:%SZ'
  rustc -Vv
  cargo -V
  git -C "$source_dir" rev-parse HEAD
  echo 'Cargo: --locked -p anvil --no-default-features --features winit --jobs 1'
  echo 'Entorno: CARGO_BUILD_JOBS=1 CARGO_PROFILE_DEV_DEBUG=0'
} > "$root/reports/anvil-build-environment.txt"
cd "$source_dir"
CARGO_BUILD_JOBS=1 CARGO_PROFILE_DEV_DEBUG=0 \
  cargo build --locked -p anvil --no-default-features --features winit --jobs 1 \
  2>&1 | tee "$root/reports/anvil-build.log"
