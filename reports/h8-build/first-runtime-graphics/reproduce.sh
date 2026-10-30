#!/usr/bin/env bash
set -euo pipefail
report=/home/tv/repositorio-principal/reports/h8-build/first-runtime-graphics
mkdir -p "$report"
runtime=$(mktemp -d /tmp/archtv-package-runtime.XXXXXX)
host_pid=''
cleanup() {
  if [[ -n "$host_pid" ]]; then kill "$host_pid" 2>/dev/null || true; wait "$host_pid" 2>/dev/null || true; fi
  rm -rf -- "$runtime"
}
trap cleanup EXIT
export XDG_RUNTIME_DIR="$runtime"
unset DISPLAY WAYLAND_DISPLAY WAYLAND_SOCKET
setpriv --inh-caps=-all --ambient-caps=-all weston --backend=headless --renderer=pixman --shell=kiosk-shell.so --fake-seat --width=1280 --height=720 --socket=archtv-host --no-config --idle-time=0 --log="$report/host.log" > "$report/host-stderr.log" 2>&1 &
host_pid=$!
for ((attempt=0;attempt<200;attempt++)); do
  [[ -S "$runtime/archtv-host" ]] && break
  kill -0 "$host_pid"
  sleep 0.1
done
sudo -n arch-nspawn /home/tv/.cache/archtv/install-test/root --bind="$runtime:/run/archtv-probe" --bind="$report:/report" /usr/bin/setpriv --reuid=1000 --regid=1000 --clear-groups --inh-caps=-all --ambient-caps=-all /usr/bin/env HOME=/tmp XDG_RUNTIME_DIR=/run/archtv-probe XDG_CONFIG_HOME=/tmp/archtv-package-config WAYLAND_DISPLAY=archtv-host LIBGL_ALWAYS_SOFTWARE=1 GALLIUM_DRIVER=llvmpipe EGL_PLATFORM=wayland /usr/bin/archtv-compositor --winit --mode 1280x720 --shell --exit-after 25 -- /usr/bin/archtv-shell --capture-after 5 /report/shell.png --exit-after 20 > "$report/compositor.log" 2>&1
[[ -s "$report/shell.png" ]]
rg -q 'SHELL_FRAME .*size=1280x720' "$report/compositor.log"
rg -q 'SHELL_WALLPAPER loaded=true' "$report/compositor.log"
rg -q TV_COMPOSITOR_STOPPED "$report/compositor.log"
if rg -q 'panicked|error while loading shared libraries' "$report/compositor.log"; then exit 1; fi
printf '%s\n' 'PASS: installed compositor and shell rendered at 720p in runtime container, nested on host Weston with software graphics.' 'Native DRM session selection and Android are not covered.' > "$report/result.txt"
