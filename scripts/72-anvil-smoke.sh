#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
lab="${ARCHTV_LAB_ROOT:-${XDG_CACHE_HOME:-$HOME/.cache}/archtv}"
binary="$lab/smithay/target/debug/anvil"
if ! "$APPLY"; then
  echo "Arrancará Weston headless/Pixman, $binary --winit y weston-simple-shm."
  echo 'Forzará llvmpipe; capturará salida y consumo; terminará los procesos de prueba.'
  exit 0
fi
[[ -x "$binary" ]] || { echo 'Compila primero con 71-anvil-build.sh --apply.' >&2; exit 1; }
[[ "$(git -C "$lab/smithay" rev-parse HEAD)" == "$(cat "$root/lab/anvil/revision.txt")" ]] || exit 1
report="$root/reports/anvil"
mkdir -p "$report"
rm -f -- "$report/screen.png" "$report/metrics.txt" "$report/result.txt"
runtime=$(mktemp -d)
chmod 700 "$runtime"
host_pid=''
anvil_pid=''
client_pid=''
cleanup() {
  local result=$?
  trap - EXIT
  for pid in "$client_pid" "$anvil_pid" "$host_pid"; do
    if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; fi
  done
  for pid in "$client_pid" "$anvil_pid" "$host_pid"; do
    if [[ -n "$pid" ]]; then wait "$pid" 2>/dev/null || true; fi
  done
  rm -rf -- "$runtime"
  if (( result != 0 )); then printf 'FAIL: prueba de Anvil, código %s\n' "$result" > "$report/result.txt"; fi
  exit "$result"
}
trap cleanup EXIT
export XDG_RUNTIME_DIR="$runtime"
export LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe EGL_PLATFORM=wayland
unset DISPLAY
setpriv --inh-caps=-all --ambient-caps=-all \
  weston --backend=headless --renderer=pixman --shell=kiosk-shell.so \
  --fake-seat --width=1280 --height=720 --socket=archtv-host --no-config \
  --idle-time=0 --debug --log="$report/weston.log" > "$report/weston-stderr.log" 2>&1 &
host_pid=$!
for ((attempt=0; attempt<200; attempt++)); do
  [[ -S "$runtime/archtv-host" ]] && break
  kill -0 "$host_pid" 2>/dev/null || { echo 'Falló Weston; revisa reports/anvil/weston.log' >&2; exit 1; }
  sleep 0.1
done
[[ -S "$runtime/archtv-host" ]] || exit 1
WAYLAND_DISPLAY=archtv-host RUST_LOG=anvil=debug,smithay=debug NO_COLOR=1 \
  setpriv --inh-caps=-all --ambient-caps=-all "$binary" --winit > "$report/anvil.log" 2>&1 &
anvil_pid=$!
socket=''
for ((attempt=0; attempt<200; attempt++)); do
  kill -0 "$anvil_pid" 2>/dev/null || { echo 'Falló Anvil; revisa reports/anvil/anvil.log' >&2; exit 1; }
  for candidate in "$runtime"/wayland-*; do
    if [[ -S "$candidate" ]]; then socket="${candidate##*/}"; break; fi
  done
  [[ -n "$socket" ]] && break
  sleep 0.1
done
[[ -n "$socket" ]] || { echo 'Anvil no publicó socket.' >&2; exit 1; }
WAYLAND_DISPLAY="$socket" WAYLAND_DEBUG=client \
  setpriv --inh-caps=-all --ambient-caps=-all weston-simple-shm > "$report/client.log" 2>&1 &
client_pid=$!
sleep 3
kill -0 "$client_pid"
rg -q 'wl_surface.*commit' "$report/client.log"
rg -q 'wl_callback.*done' "$report/client.log"
python - "$anvil_pid" "$report/metrics.txt" <<'PY'
from pathlib import Path
import os
import sys
import time
pid, output = sys.argv[1:]
proc = Path('/proc') / pid

def ticks():
    fields = (proc / 'stat').read_text().split(') ', 1)[1].split()
    return int(fields[11]) + int(fields[12])

before = ticks()
start = time.monotonic()
time.sleep(3)
elapsed = time.monotonic() - start
cpu = 100 * (ticks() - before) / os.sysconf('SC_CLK_TCK') / elapsed
memory = '\n'.join(line for line in (proc / 'smaps_rollup').read_text().splitlines()
                   if line.startswith(('Rss:', 'Pss:')))
Path(output).write_text(f'Anvil dev build; cliente SHM animado; ventana de medida {elapsed:.2f}s\n'
                        f'CPU: {cpu:.2f}% de un núcleo\n{memory}\n'
                        'No es un benchmark del compositor propio ni una medida de reposo.\n')
PY
mkdir -p "$runtime/captures"
(cd "$runtime/captures" && WAYLAND_DISPLAY=archtv-host timeout 10 weston-screenshooter > "$report/capture.log" 2>&1)
shopt -s nullglob
shots=("$runtime/captures"/*.png)
((${#shots[@]} > 0)) || { echo 'No se generó captura.' >&2; exit 1; }
cp -- "${shots[0]}" "$report/screen.png"
{
  date -u '+Fecha UTC: %Y-%m-%dT%H:%M:%SZ'
  echo 'PASS: Weston headless/Pixman → Anvil winit/GLES → cliente SHM'
  printf 'Socket de Anvil: %s\n' "$socket"
  echo 'Se observaron commits y callbacks de frame del cliente.'
  echo 'Captura: reports/anvil/screen.png'
} > "$report/result.txt"
echo 'Prueba Anvil correcta; ver reports/anvil/.'
