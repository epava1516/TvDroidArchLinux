#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
target="${CARGO_TARGET_DIR:-$root/target}"
if ! "$APPLY"; then
  echo "Probará $target/debug/archtv-compositor, cliente Rust y cliente SHM externo."
  exit 0
fi
compositor="$target/debug/archtv-compositor"
client="$target/debug/archtv-test-client"
[[ -x "$compositor" && -x "$client" ]] || { echo 'Compila el workspace primero.' >&2; exit 1; }
report="$root/reports/h2"
mkdir -p "$report"
rm -f "$report/result.txt" "$report/screen.png"
runtime=$(mktemp -d)
host_pid=''
compositor_pid=''
client_pid=''
foreign_pid=''
cleanup() {
  local result=$?
  trap - EXIT
  for pid in "$foreign_pid" "$client_pid" "$compositor_pid" "$host_pid"; do
    if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; fi
  done
  for pid in "$foreign_pid" "$client_pid" "$compositor_pid" "$host_pid"; do
    if [[ -n "$pid" ]]; then wait "$pid" 2>/dev/null || true; fi
  done
  rm -rf -- "$runtime"
  if ((result)); then echo 'FAIL: ciclo gráfico H2; revisar logs.' > "$report/result.txt"; fi
  exit "$result"
}
trap cleanup EXIT
export XDG_RUNTIME_DIR="$runtime" LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe EGL_PLATFORM=wayland
unset DISPLAY
setpriv --inh-caps=-all --ambient-caps=-all weston --backend=headless --renderer=pixman \
  --fake-seat --width=1280 --height=720 --socket=archtv-host --no-config --idle-time=0 --debug \
  --log="$report/host.log" > "$report/host-stderr.log" 2>&1 &
host_pid=$!
for ((attempt=0;attempt<200;attempt++)); do
  [[ -S "$runtime/archtv-host" ]] && break
  kill -0 "$host_pid" || exit 1
  sleep 0.1
done
WAYLAND_DISPLAY=archtv-host RUST_LOG=archtv_compositor=info,smithay=info \
  setpriv --inh-caps=-all --ambient-caps=-all "$compositor" --winit --test-resize 8 800x450 --exit-after 60 > "$report/compositor.log" 2>&1 &
compositor_pid=$!
for ((attempt=0;attempt<200;attempt++)); do
  rg -q 'TV_COMPOSITOR_READY' "$report/compositor.log" && break
  kill -0 "$compositor_pid" || exit 1
  sleep 0.1
done
socket=''
for candidate in "$runtime"/wayland-*; do [[ -S "$candidate" ]] && socket="${candidate##*/}"; done
[[ -n "$socket" ]] || exit 1
WAYLAND_DISPLAY="$socket" "$client" 0 > "$report/persistent-client.log" 2>&1 &
client_pid=$!
for ((attempt=0;attempt<100;attempt++)); do
  rg -q 'CLIENT_FOCUS_ENTER' "$report/persistent-client.log" && break
  kill -0 "$client_pid" || exit 1
  sleep 0.1
done
rg -q 'CLIENT_CONFIGURE 960x540' "$report/persistent-client.log"
for iteration in {1..10}; do
  WAYLAND_DISPLAY="$socket" timeout 10 "$client" 3 > "$report/client-$iteration.log" 2>&1
  rg -q 'CLIENT_EXIT frames=3' "$report/client-$iteration.log"
  rg -q 'fullscreen=true' "$report/client-$iteration.log"
  rg -q 'CLIENT_FOCUS_ENTER' "$report/client-$iteration.log"
done
for ((attempt=0;attempt<100;attempt++)); do
  rg -q 'CLIENT_CONFIGURE 800x450' "$report/persistent-client.log" && break
  kill -0 "$client_pid" || exit 1
  sleep 0.1
done
rg -q 'CLIENT_CONFIGURE 800x450' "$report/persistent-client.log"
rg -q 'CLIENT_CONFIGURE 960x540' "$report/persistent-client.log"
WAYLAND_DISPLAY="$socket" timeout 10 "$client" 0 --popup > "$report/popup-client.log" 2>&1
rg -q 'POPUP_FRAME 2' "$report/popup-client.log"
rg -q 'POPUP_REPOSITIONED token=7' "$report/popup-client.log"
rg -q 'POPUP_CLOSED' "$report/popup-client.log"
focus_before=$(rg -c 'CLIENT_FOCUS_ENTER' "$report/persistent-client.log")
WAYLAND_DISPLAY="$socket" WAYLAND_DEBUG=client weston-simple-shm > "$report/foreign-client.log" 2>&1 &
foreign_pid=$!
sleep 1
kill -0 "$foreign_pid"
rg -q 'wl_callback.*done' "$report/foreign-client.log"
mkdir -p "$runtime/capture"
(cd "$runtime/capture" && WAYLAND_DISPLAY=archtv-host timeout 10 weston-screenshooter > "$report/capture.log" 2>&1)
shopt -s nullglob
shots=("$runtime/capture"/*.png)
((${#shots[@]})) || exit 1
cp "${shots[0]}" "$report/screen.png"
kill "$foreign_pid"
wait "$foreign_pid" 2>/dev/null || true
foreign_pid=''
sleep 0.2
[[ $(rg -c 'CLIENT_FOCUS_ENTER' "$report/persistent-client.log") -gt $focus_before ]]
kill "$compositor_pid"
wait "$compositor_pid"
compositor_pid=''
[[ ! -S "$runtime/$socket" ]]
rg -q 'TV_COMPOSITOR_STOPPED' "$report/compositor.log"
{
  date -u '+Fecha UTC: %Y-%m-%dT%H:%M:%SZ'
  echo 'PASS: 10 ciclos de cliente Rust, fullscreen, foco, resize a 800x450 y cliente SHM externo.'
  echo 'Foco restaurado tras cerrar cliente externo. Cierre SIGTERM limpio y socket retirado.'
} > "$report/result.txt"
echo 'Prueba gráfica del compositor propio correcta; ver reports/h2/.'
