#!/usr/bin/env bash
# Test real shell buffers and presentation through the nested Wayland backend.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
target="${CARGO_TARGET_DIR:-$root/target}"
if ! "$APPLY"; then echo 'Validará el shell real a 720p/1080p/4K con Weston headless de prueba.'; exit 0; fi
visual_python="${ARCHTV_VISUAL_PYTHON:-$HOME/.local/share/archtv-tools/visual-analysis/bin/python}"
[[ -x "$visual_python" ]] || { echo "Instala lab/visual/requirements.txt en un venv y define ARCHTV_VISUAL_PYTHON." >&2; exit 1; }
report="$root/reports/h5-resolutions"
mkdir -p "$report"
echo 'RUNNING: nested shell resolutions' > "$report/result.txt"
runtime=$(mktemp -d)
host_pid=''
compositor_pid=''
cleanup() {
  local result=$?
  trap - EXIT
  for pid in "$compositor_pid" "$host_pid"; do
    if [[ -n "$pid" ]]; then kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; fi
  done
  rm -rf -- "$runtime"
  if ((result)); then echo 'FAIL: resolution validation; inspect logs.' > "$report/result.txt"; fi
  exit "$result"
}
trap cleanup EXIT
export XDG_RUNTIME_DIR="$runtime" LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe EGL_PLATFORM=wayland
export XDG_DATA_HOME="$runtime/data" XDG_DATA_DIRS="$runtime/data" XDG_CONFIG_HOME="$runtime/config"
unset DISPLAY WAYLAND_SOCKET ARCHTV_CONTROL_FD
mkdir -p "$XDG_DATA_HOME/applications" "$XDG_CONFIG_HOME"
for index in {1..12}; do
  cat > "$XDG_DATA_HOME/applications/probe-$index.desktop" <<DESKTOP
[Desktop Entry]
Type=Application
Name=Aplicación $index
Comment=Aplicación de prueba de resolución
Exec=$target/debug/archtv-test-client 3
Icon=missing-test-icon
DESKTOP
done
for dimensions in 1280x720 1920x1080 3840x2160; do
  width=${dimensions%x*}; height=${dimensions#*x}
  case_report="$report/$dimensions"
  mkdir -p "$case_report"
  rm -f "$case_report/shell.png" "$case_report/presented.png"
  rm -rf -- "$case_report/states"
  setpriv --inh-caps=-all --ambient-caps=-all weston --backend=headless --renderer=pixman \
    --shell=kiosk-shell.so --fake-seat --width="$width" --height="$height" \
    --socket=archtv-host --no-config --idle-time=0 --debug --log="$case_report/host.log" \
    > "$case_report/host-stderr.log" 2>&1 &
  host_pid=$!
  for ((attempt=0;attempt<200;attempt++)); do
    [[ -S "$runtime/archtv-host" ]] && break
    kill -0 "$host_pid"; sleep 0.1
  done
  WAYLAND_DISPLAY=archtv-host setpriv --inh-caps=-all --ambient-caps=-all \
    "$target/debug/archtv-compositor" --winit --mode "$dimensions" --shell --exit-after 90 \
    -- "$target/debug/archtv-shell" --capture-after 8 "$case_report/shell.png" \
    --capture-states "$case_report/states" --exit-after 85 > "$case_report/compositor.log" 2>&1 &
  compositor_pid=$!
  for ((attempt=0;attempt<600;attempt++)); do
    [[ -s "$case_report/states/home.png" && -s "$case_report/shell.png" ]] && break
    kill -0 "$compositor_pid"; sleep 0.1
  done
  [[ -s "$case_report/states/home.png" && -s "$case_report/shell.png" ]]
  rg -q "SHELL_FRAME .*size=$dimensions" "$case_report/compositor.log"
  rg -q 'SHELL_WALLPAPER loaded=true' "$case_report/compositor.log"
  mkdir -p "$runtime/capture"
  (cd "$runtime/capture" && WAYLAND_DISPLAY=archtv-host timeout 15 weston-screenshooter > "$case_report/capture.log" 2>&1)
  shots=("$runtime/capture/"*.png)
  cp "${shots[0]}" "$case_report/presented.png"
  rm -f "$runtime/capture/"*.png
  kill "$compositor_pid"; wait "$compositor_pid"; compositor_pid=''
  kill "$host_pid"; wait "$host_pid"; host_pid=''
  rg -q 'TV_COMPOSITOR_STOPPED' "$case_report/compositor.log"
done
"$visual_python" "$root/scripts/lib/verify-shell-resolutions.py" "$report"
{
  date -u '+Fecha UTC: %Y-%m-%dT%H:%M:%SZ'
  echo 'PASS: real SCTK shell buffers and nested presentation at 1280x720, 1920x1080, 3840x2160.'
  echo 'Software graphics in Weston headless kiosk; no native 4K hardware or performance claim.'
} > "$report/result.txt"
