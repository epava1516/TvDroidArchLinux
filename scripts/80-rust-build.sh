#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
run env CARGO_BUILD_JOBS=1 cargo build --locked --workspace --manifest-path "$root/Cargo.toml" --jobs 1
