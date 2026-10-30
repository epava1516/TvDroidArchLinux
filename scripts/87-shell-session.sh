#!/usr/bin/env bash
# Internal test entrypoint in a PAM/logind session; no persistent autologin.
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
report="${ARCHTV_SHELL_REPORT:-$root/reports/h5-interactive}"
target="${CARGO_TARGET_DIR:-$root/target}"
mkdir -p "$report/states"
XDG_RUNTIME_DIR="/run/user/$(id -u)"
export XDG_RUNTIME_DIR LIBSEAT_BACKEND=logind
export DBUS_SESSION_BUS_ADDRESS="unix:path=$XDG_RUNTIME_DIR/bus"
unset DISPLAY WAYLAND_DISPLAY EGL_PLATFORM
for ((attempt=0;attempt<100;attempt++)); do
  [[ $(loginctl show-session "${XDG_SESSION_ID:?PAM session required}" -p Active --value) == yes ]] && break
  sleep 0.1
done
python - "$report/offline-proof.txt" <<'OFFLINE'
import errno
from pathlib import Path
import socket
import sys
results=[]
for family in (socket.AF_INET,socket.AF_INET6):
    try:
        connection=socket.socket(family,socket.SOCK_STREAM)
    except OSError as error:
        assert error.errno in (errno.EAFNOSUPPORT,errno.EPERM,errno.EACCES), error
        results.append(f'{family.name}: creation refused, errno={error.errno}')
    else:
        connection.close()
        raise RuntimeError('The integration test requires IP socket families disabled')
Path(sys.argv[1]).write_text('\n'.join(results)+'\n')
OFFLINE
systemctl --user start pipewire.service pipewire-pulse.service wireplumber.service
exec setpriv --inh-caps=-all --ambient-caps=-all "$target/debug/archtv-compositor" \
  --drm /dev/dri/card0 --mode "${ARCHTV_SHELL_MODE:-1920x1080}" --shell --exit-after 120 --capture-after 15 "$report/scanout.ppm" \
  -- "$target/debug/archtv-shell" --capture-after 4 "$report/startup.png" \
  --capture-states "$report/states" --exit-after 115 > "$report/compositor.log" 2>&1
