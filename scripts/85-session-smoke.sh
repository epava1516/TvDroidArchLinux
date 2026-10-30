#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
target="${CARGO_TARGET_DIR:-$root/target}"
if ! "$APPLY"; then echo 'Probará Inicio, control privado, recuperación del shell y límite de reinicios en tty2.'; exit 0; fi
[[ -z $(loginctl list-sessions --no-legend) ]]
if systemctl is-active --quiet getty@tty2.service; then echo 'tty2 tiene un getty activo.' >&2; exit 1; fi
report="$root/reports/h4"
mkdir -p "$report"
rm -f "$report/result.txt" "$report/compositor.log"
initial_vt=$(sudo -n fgconsole)
unit="archtv-h4-$$"
app_pid=''
cleanup() {
  local result=$?
  trap - EXIT
  [[ -z "$app_pid" ]] || { kill "$app_pid" 2>/dev/null || true; wait "$app_pid" 2>/dev/null || true; }
  sudo -n systemctl stop "$unit.service" 2>/dev/null || true
  sudo -n chvt "$initial_vt" || true
  if ((result)); then echo 'FAIL: política de sesión H4; consultar logs.' > "$report/result.txt"; fi
  exit "$result"
}
trap cleanup EXIT
sudo -n systemd-run --unit="$unit" --collect \
  --property="User=$(id -un)" --property=PAMName=login --property=TTYPath=/dev/tty2 \
  --property=StandardInput=tty --property=TTYReset=yes --property=TTYVHangup=yes \
  --property=KillMode=control-group --property=TimeoutStopSec=10 \
  --setenv="CARGO_TARGET_DIR=$target" --setenv=RUST_LOG=archtv_compositor=debug,smithay=warn \
  --setenv=ARCHTV_PROBE_SESSION=1 "$root/scripts/83-drm-session.sh"
sudo -n chvt 2
for ((attempt=0;attempt<200;attempt++)); do
  [[ -f "$report/compositor.log" ]] && rg -q 'SHELL_SURFACE_READY' "$report/compositor.log" && break
  sleep 0.1
done
rg -q 'SHELL_SURFACE_READY' "$report/compositor.log"
socket=$(sed -n 's/.*TV_COMPOSITOR_READY socket="\([^"]*\)".*/\1/p' "$report/compositor.log" | head -1)
XDG_RUNTIME_DIR="/run/user/$(id -u)" WAYLAND_DISPLAY="$socket" \
  "$target/debug/archtv-test-client" 0 --control-on-enter > "$report/app.log" 2>&1 &
app_pid=$!
for ((attempt=0;attempt<100;attempt++)); do
  [[ -f "$report/app.log" ]] && rg -q 'CLIENT_FOCUS_ENTER' "$report/app.log" && break
  sleep 0.1
done
rg -q 'CLIENT_FOCUS_ENTER' "$report/app.log"
# A public client with the same app_id must not be promoted to shell.
[[ $(rg -c SHELL_SURFACE_READY "$report/compositor.log") == 1 ]]
sudo -n python "$root/scripts/lib/session-input.py" home-resume
rg -q 'TV_HOME' "$report/compositor.log"
rg -q 'CLIENT_CONTROL_RESUME' "$report/compositor.log"
rg -q 'TV_RESUME' "$report/compositor.log"
[[ $(rg -c CLIENT_FOCUS_ENTER "$report/app.log") -ge 2 ]]
kill "$app_pid"
wait "$app_pid" 2>/dev/null || true
app_pid=''
for ((attempt=0;attempt<50;attempt++)); do
  rg -q TV_APP_CLOSED_HOME "$report/compositor.log" && break
  sleep 0.1
done
rg -q TV_APP_CLOSED_HOME "$report/compositor.log"
cp "$report/app.log" "$report/app-cycle1.log"
XDG_RUNTIME_DIR="/run/user/$(id -u)" WAYLAND_DISPLAY="$socket" \
  "$target/debug/archtv-test-client" 0 > "$report/app.log" 2>&1 &
app_pid=$!
for ((attempt=0;attempt<100;attempt++)); do
  [[ -f "$report/app.log" ]] && rg -q CLIENT_FOCUS_ENTER "$report/app.log" && break
  sleep 0.1
done
rg -q CLIENT_FOCUS_ENTER "$report/app.log"
for expected in 2 3 4; do
  shell_pid=$(sed -n 's/.*SESSION_CHILD_STARTED pid=\([0-9]*\) shell=true.*/\1/p' "$report/compositor.log" | tail -1)
  kill "$shell_pid"
  for ((attempt=0;attempt<100;attempt++)); do
    [[ $(rg -c SHELL_SURFACE_READY "$report/compositor.log") -ge $expected ]] && break
    sleep 0.1
  done
  [[ $(rg -c SHELL_SURFACE_READY "$report/compositor.log") -ge $expected ]]
  kill -0 "$app_pid"
done
shell_pid=$(sed -n 's/.*SESSION_CHILD_STARTED pid=\([0-9]*\) shell=true.*/\1/p' "$report/compositor.log" | tail -1)
kill "$shell_pid"
for ((attempt=0;attempt<100;attempt++)); do
  rg -q SHELL_RESTART_LIMIT "$report/compositor.log" && break
  sleep 0.1
done
rg -q SHELL_RESTART_LIMIT "$report/compositor.log"
kill -0 "$app_pid"
sudo -n python "$root/scripts/lib/session-input.py" quit
for ((attempt=0;attempt<100;attempt++)); do
  rg -q TV_COMPOSITOR_STOPPED "$report/compositor.log" && break
  sleep 0.1
done
rg -q TV_COMPOSITOR_STOPPED "$report/compositor.log"
for ((attempt=0;attempt<50;attempt++)); do
  systemctl is-active --quiet "$unit.service" || break
  sleep 0.1
done
rg -q DRM_STOPPED "$report/compositor.log"
{
  date -u '+Fecha UTC: %Y-%m-%dT%H:%M:%SZ'
  echo 'PASS: shell identificado por conexión privada; app_id idéntico no concede el rol.'
  echo 'Inicio global y RESUME por canal privado restauran el foco de la app.'
  echo 'Tres reinicios, límite de fallos y app superviviente; salida de emergencia por teclado.'
} > "$report/result.txt"
echo 'Prueba de sesión correcta; ver reports/h4/.'
