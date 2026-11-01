#!/usr/bin/env bash
set -euo pipefail
export XDG_RUNTIME_DIR="/run/user/$(id -u)" LIBSEAT_BACKEND=logind RUST_LOG=archtv_compositor=debug,smithay=warn
unset DISPLAY WAYLAND_DISPLAY EGL_PLATFORM
out=${1:?}
for ((attempt=0;attempt<60;attempt++)); do
 [[ $(loginctl show-session "${XDG_SESSION_ID:?}" -p Active --value) == yes ]] && break
 sleep 0.1
done
exec /home/tv/.cache/archtv/compositor-native/debug/archtv-compositor --drm /dev/dri/card0 --capture-after 30 "$out/screen.ppm" --exit-after 170 -- /usr/bin/bash /home/tv/repositorio-principal/reports/android16-package-bootstrap/integrated-client.sh > "$out/compositor.log" 2>&1
