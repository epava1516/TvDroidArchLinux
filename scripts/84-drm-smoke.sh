#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
target="${CARGO_TARGET_DIR:-$root/target}"
if ! "$APPLY"; then
  echo 'Probará el compositor en tty2 con logind, DRM/Pixman, libinput y regreso a la VT inicial.'
  exit 0
fi
[[ -x "$target/debug/archtv-compositor" && -x "$target/debug/archtv-test-client" ]]
[[ -c /dev/dri/card0 && -c /dev/uinput ]]
if systemctl is-active --quiet getty@tty2.service; then
  echo 'tty2 tiene un getty activo; usar una TTY libre antes del ensayo.' >&2
  exit 1
fi
[[ -z $(loginctl list-sessions --no-legend) ]] || { echo 'La prueba requiere que no haya otra sesión local activa.' >&2; exit 1; }
report="$root/reports/h3"
mkdir -p "$report"
rm -f "$report/result.txt" "$report/compositor.log" "$report/screen.ppm"
initial_vt=$(sudo -n fgconsole)
unit="archtv-h3-$$"
cleanup() {
  local result=$?
  trap - EXIT
  sudo -n systemctl stop "$unit.service" 2>/dev/null || true
  sudo -n chvt "$initial_vt" || true
  if ((result)); then echo 'FAIL: sesión directa H3; consultar logs.' > "$report/result.txt"; fi
  exit "$result"
}
trap cleanup EXIT
sudo -n systemd-run --unit="$unit" --collect \
  --property="User=$(id -un)" --property=PAMName=login --property=TTYPath=/dev/tty2 \
  --property=StandardInput=tty --property=TTYReset=yes --property=TTYVHangup=yes \
  --property=KillMode=control-group --property=TimeoutStopSec=10 \
  --setenv="CARGO_TARGET_DIR=$target" --setenv=RUST_LOG=archtv_compositor=debug,smithay=warn \
  "$root/scripts/83-drm-session.sh"
sudo -n chvt 2
for ((attempt=0;attempt<150;attempt++)); do
  [[ -f "$report/compositor.log" ]] && rg -q 'CLIENT_FOCUS_ENTER' "$report/compositor.log" && break
  systemctl is-active --quiet "$unit.service" || { sudo -n journalctl -u "$unit.service" --no-pager -n 25; exit 1; }
  sleep 0.1
done
rg -q 'CLIENT_FOCUS_ENTER' "$report/compositor.log"
sudo -n python "$root/scripts/lib/input-probe.py" "$report/compositor.log"
rg -q 'CLIENT_KEY.*Right' "$report/compositor.log"
rg -q 'CLIENT_KEY.*Return' "$report/compositor.log"
rg -q 'CLIENT_KEY.*ntilde.*popup=true' "$report/compositor.log"
rg -q 'POPUP_GRABBED' "$report/compositor.log"
rg -q 'POPUP_CLOSED_BY_KEY' "$report/compositor.log"
for ((attempt=0;attempt<30;attempt++)); do
  [[ $(sudo -n fgconsole) == 1 ]] && break
  sleep 0.1
done
[[ $(sudo -n fgconsole) == 1 ]]
rg -q 'SESSION_PAUSED' "$report/compositor.log"
sudo -n chvt 2
for ((attempt=0;attempt<50;attempt++)); do
  rg -q 'SESSION_ACTIVE' "$report/compositor.log" && break
  sleep 0.1
done
rg -q 'SESSION_ACTIVE' "$report/compositor.log"
sudo -n python "$root/scripts/lib/session-input.py" letter
rg -Fq 'CLIENT_KEY XK_a popup=false text=Some("a")' "$report/compositor.log"
for ((attempt=0;attempt<80;attempt++)); do
  [[ -f "$report/screen.ppm" ]] && break
  sleep 0.1
done
[[ -s "$report/screen.ppm" ]]
python "$root/scripts/lib/ppm-to-png.py" "$report/screen.ppm" "$report/screen.png"
python - "$report/compositor.log" <<'CHECK'
from pathlib import Path
import sys
text = Path(sys.argv[1]).read_text()
assert 'DRM_PRESENTED' in text.split('SESSION_ACTIVE', 1)[1], 'No presentation after VT resume'
assert 'CLIENT_KEY XK_Right popup=false' in text.split('POPUP_CLOSED_BY_KEY', 1)[1], 'Popup focus not restored'
CHECK
# Read privileged KMS state; write the report as the regular user.
# shellcheck disable=SC2024
sudo -n cat /sys/kernel/debug/dri/0/state > "$report/kms-state.txt"
sudo -n systemctl kill --signal=SIGTERM --kill-whom=main "$unit.service"
for ((attempt=0;attempt<100;attempt++)); do
  systemctl is-active --quiet "$unit.service" || break
  sleep 0.1
done
rg -q 'TV_COMPOSITOR_STOPPED' "$report/compositor.log"
if rg -q 'DRM_.*FAILED|SESSION_RESUME_FAILED|panicked' "$report/compositor.log"; then exit 1; fi
{
  date -u '+Fecha UTC: %Y-%m-%dT%H:%M:%SZ'
  echo 'PASS: DRM/KMS directo, Pixman, cliente SHM, presentación y captura del buffer mostrado.'
  echo 'uinput → libinput → mapa español → cliente: Right, Return, ntilde.'
  echo 'Ctrl+Alt+F1, pausa y regreso a tty2 verificados; cierre SIGTERM y restauración de VT.'
  echo 'No acredita un mando físico ni Android.'
} > "$report/result.txt"
echo 'Prueba directa correcta; ver reports/h3/.'
