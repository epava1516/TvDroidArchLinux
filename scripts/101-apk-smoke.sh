#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
target="${CARGO_TARGET_DIR:-$root/target}"
if ! "$APPLY"; then
  echo 'Probará la APK propia en DRM/Pixman, entrada uinput, cierre y reapertura con estado.'
  exit 0
fi
[[ -x "$target/debug/archtv-compositor" && -x "$target/debug/archtv-apk-host" ]]
[[ -c /dev/dri/card0 && -c /dev/uinput ]]
[[ -f ${ARCHTV_APK_RUNTIME_DEX:?runtime DEX required} ]]
[[ -z $(loginctl list-sessions --no-legend) ]] || { echo 'Se requiere una sesión local libre.' >&2; exit 1; }
if systemctl is-active --quiet getty@tty2.service; then
  echo 'tty2 tiene un getty activo.' >&2; exit 1
fi
report="${ARCHTV_APK_SMOKE_REPORT:-$root/reports/a2-wayland}"
[[ ! -e $report ]] || { echo 'El informe debe ser nuevo.' >&2; exit 1; }
mkdir -p "$report"
report=$(realpath "$report")
data=$(mktemp -d "$HOME/.cache/archtv/apk-ui-XXXXXX")
initial_vt=$(sudo -n fgconsole)
unit="archtv-apk-$$"
cleanup() {
  local status=$?
  trap - EXIT
  sudo -n systemctl stop "$unit.service" 2>/dev/null || true
  sudo -n chvt "$initial_vt" || true
  exit "$status"
}
trap cleanup EXIT
for phase in first reopen; do
  mkdir -p "$report/$phase"
  sudo -n systemd-run --unit="$unit" --collect \
    --property="User=$(id -un)" --property=PAMName=login --property=TTYPath=/dev/tty2 \
    --property=StandardInput=tty --property=TTYReset=yes --property=TTYVHangup=yes \
    --property=KillMode=control-group --property=TimeoutStopSec=10 \
    --setenv="CARGO_TARGET_DIR=$target" --setenv=RUST_LOG=archtv_compositor=debug,smithay=warn \
    --setenv="ARCHTV_APK_REPORT=$report/$phase" --setenv="ARCHTV_APK_DATA=$data" \
    --setenv="ARCHTV_APK_RUNTIME_DEX=$(realpath "$ARCHTV_APK_RUNTIME_DEX")" \
    "$root/scripts/100-apk-session.sh"
  sudo -n chvt 2
  count=0
  [[ $phase == first ]] || count=2
  sudo -n python "$root/scripts/lib/apk-ui-probe.py" "$report/$phase" "$count"
  sudo -n systemctl kill --signal=SIGTERM --kill-whom=main "$unit.service"
  for ((attempt=0;attempt<100;attempt++)); do
    systemctl is-active --quiet "$unit.service" || break
    sleep 0.1
  done
  rg -q TV_COMPOSITOR_STOPPED "$report/$phase/compositor.log"
  if rg -q 'APK_HOST_ERROR|panicked|DRM_.*FAILED' "$report/$phase/compositor.log"; then exit 1; fi
  python "$root/scripts/lib/ppm-to-png.py" "$report/$phase/scanout.ppm" "$report/$phase/scanout.png"
  sudo -n chvt "$initial_vt"
  unit="archtv-apk-reopen-$$"
done
cp "$data/app-data/counter.properties" "$report/persisted-counter.properties"
python - "$root" "$report" "$target" "$ARCHTV_APK_RUNTIME_DEX" <<'CHECK'
import hashlib,json,sys
from pathlib import Path
root,report,target,dex=map(Path,sys.argv[1:])
assert 'count=3' in (report/'persisted-counter.properties').read_text().splitlines()
proof={'fixture_wayland_pass':True,'resolution':[1280,720],
 'input':'uinput → libinput → compositor → Wayland keyboard → Rust → ART → APK listener',
 'scope':'Owned APK only, close/reopen persistence, no physical remote, no stability/performance/general APK compatibility claim.',
 'sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in
 [root/'fixtures/apk/counter/golden/counter.apk',dex,target/'debug/archtv-apk-host',target/'debug/archtv-compositor']}}
(report/'result.json').write_text(json.dumps(proof,indent=2)+'\n')
CHECK
echo "PASS: APK propia en Wayland, 0→1→2, reapertura 2→3; $report"
