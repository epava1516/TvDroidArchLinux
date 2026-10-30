#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
target="${CARGO_TARGET_DIR:-$root/target}"
if ! "$APPLY"; then echo 'Compilará y medirá el renderer del shell a 720p, 1080p y 4K.'; exit 0; fi
report="$root/reports/h5"
mkdir -p "$report"
echo 'RUNNING: renderer probe' > "$report/result.txt"
probe_result=0
trap 'probe_result=$?; if ((probe_result)); then echo "FAIL: renderer probe ($probe_result)" > "$report/result.txt"; fi' EXIT
rustc -vV > "$report/environment.txt"
date -u '+Fecha UTC: %Y-%m-%dT%H:%M:%SZ' >> "$report/environment.txt"
sha256sum "$root/Cargo.lock" "$root/crates/archtv-shell/src/"*.rs > "$report/source-sha256.txt"
CARGO_BUILD_JOBS=1 cargo build --locked --release -p archtv-shell --manifest-path "$root/Cargo.toml" --jobs 1
python "$root/scripts/lib/measure-process.py" "$root/reports/h5/process-metrics.json" \
  "$target/release/archtv-shell" --render-probe "$root/reports/h5"
echo 'PASS: CPU renderer only; no interactive shell or end-to-end performance claim.' > "$report/result.txt"
