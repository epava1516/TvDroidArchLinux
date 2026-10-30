#!/usr/bin/env bash
# Internal session entrypoint: launched by systemd with PAM and a real TTY.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
report="$root/reports/h3"
target="${CARGO_TARGET_DIR:-$root/target}"
mkdir -p "$report"
XDG_RUNTIME_DIR="/run/user/$(id -u)"
export XDG_RUNTIME_DIR LIBSEAT_BACKEND=logind
unset DISPLAY WAYLAND_DISPLAY EGL_PLATFORM
for ((attempt=0;attempt<100;attempt++)); do
  [[ $(loginctl show-session "${XDG_SESSION_ID:?PAM session required}" -p Active --value) == yes ]] && break
  sleep 0.1
done
options=(--drm /dev/dri/card0 --capture-after 4 "$report/screen.ppm" --exit-after 45)
client_options=(0 --popup-grab)
if [[ ${ARCHTV_PROBE_SESSION:-0} == 1 ]]; then
  report="$root/reports/h4"
  mkdir -p "$report"
  export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
  systemctl --user start pipewire.service pipewire-pulse.service wireplumber.service
  systemctl --user is-active dbus.service pipewire.service pipewire-pulse.service wireplumber.service > "$report/user-services.txt"
  options=(--drm /dev/dri/card0 --shell --exit-after 55)
  client_options=(0 --control-on-enter)
fi
exec setpriv --inh-caps=-all --ambient-caps=-all "$target/debug/archtv-compositor" \
  "${options[@]}" -- "$target/debug/archtv-test-client" "${client_options[@]}" > "$report/compositor.log" 2>&1
