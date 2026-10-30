#!/usr/bin/env bash
# Build into fresh directories and reject known initramfs errors in the log.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if ! "$APPLY"; then
  echo 'Construirá ARCHTV_ISO_PROFILE en directorios nuevos y verificará log, SHA-256 y catálogo UEFI.'
  exit 0
fi
: "${ARCHTV_ISO_PROFILE:?Indica el perfil generado por packaging/iso/prepare-profile.py}"
profile=$(realpath "$ARCHTV_ISO_PROFILE")
[[ -f "$profile/profiledef.sh" && -f "$profile/profile-provenance.json" ]]
base="${ARCHTV_ISO_BUILD_ROOT:-$HOME/.cache/archtv/iso-builds}"
mkdir -p "$base"
build=$(mktemp -d "$base/build.XXXXXX")
report="${ARCHTV_ISO_REPORT:-$root/reports/h9-build-$(date -u +%Y%m%dT%H%M%SZ)}"
mkdir "$report"
report=$(realpath "$report")
mkdir "$build/work" "$build/images"
printf '%s\n' "$build" > "$report/build-directory.txt"
cp "$profile/profile-provenance.json" "$profile/profiledef.sh" "$profile/packages.x86_64" "$report/"
echo 'RUNNING: ISO laboratory build; not boot-validated.' > "$report/result.txt"
trap 'echo "FAIL: build or candidate verification failed; inspect logs." > "$report/result.txt"' ERR
sudo -n mkarchiso -v -w "$build/work" -o "$build/images" "$profile" 2>&1 | tee "$report/build.log"
shopt -s nullglob
images=("$build/images/"*.iso)
((${#images[@]} == 1))
python "$root/packaging/iso/verify-build.py" "$report/build.log" "${images[0]}" "$report/verification.json"
echo 'CANDIDATE: known-error scan and UEFI catalog checked; boot, installation and Android remain unverified.' > "$report/result.txt"
printf 'ISO candidate: %s\n' "${images[0]}"
