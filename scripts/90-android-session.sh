#!/usr/bin/env bash
# Internal PAM/logind entrypoint for Android integration diagnostics.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
report="${ARCHTV_ANDROID_REPORT:?Set diagnostic report directory}"
target="${CARGO_TARGET_DIR:-$root/target}"
XDG_RUNTIME_DIR="/run/user/$(id -u)"
export XDG_RUNTIME_DIR LIBSEAT_BACKEND=logind
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
unset DISPLAY WAYLAND_DISPLAY EGL_PLATFORM
for ((attempt=0;attempt<100;attempt++)); do
  [[ $(loginctl show-session "${XDG_SESSION_ID:?PAM session required}" -p Active --value) == yes ]] && break
  sleep 0.1
done
systemctl --user start pipewire.service pipewire-pulse.service wireplumber.service
exec setpriv --inh-caps=-all --ambient-caps=-all "$target/debug/archtv-compositor" \
  --drm /dev/dri/card0 --mode 1280x720 --exit-after 600 \
  --capture-after "${ARCHTV_ANDROID_CAPTURE_AFTER:-120}" "$report/scanout.ppm" \
  -- "$root/scripts/91-android-client.sh" > "$report/compositor.log" 2>&1
