#!/usr/bin/env bash
# Internal PAM/TTY entrypoint for the owned APK Wayland experiment.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
target="${CARGO_TARGET_DIR:-$root/target}"
report="${ARCHTV_APK_REPORT:?report required}"
data="${ARCHTV_APK_DATA:?private test data required}"
export XDG_RUNTIME_DIR="/run/user/$(id -u)" LIBSEAT_BACKEND=logind
unset DISPLAY WAYLAND_DISPLAY EGL_PLATFORM
for ((attempt=0;attempt<100;attempt++)); do
  [[ $(loginctl show-session "${XDG_SESSION_ID:?PAM session required}" -p Active --value) == yes ]] && break
  sleep 0.1
done
mkdir -p "$report"
exec setpriv --inh-caps=-all --ambient-caps=-all "$target/debug/archtv-compositor" \
  --drm /dev/dri/card0 --mode 1280x720 --capture-after 6 "$report/scanout.ppm" --exit-after 60 \
  -- "$target/debug/archtv-apk-host" \
  "$HOME/.cache/archtv/art-host/host/art-13.0.0" \
  "${ARCHTV_APK_RUNTIME_DEX:?runtime DEX required}" \
  "$root/fixtures/apk/counter/golden/counter.apk" org.archtv.probe.MainActivity \
  "$data" "$report/art.stderr" "$report/frames" > "$report/compositor.log" 2>&1
