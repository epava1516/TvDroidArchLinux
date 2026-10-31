#!/usr/bin/env bash
set -euo pipefail
exec sudo -n timeout --kill-after=2 45 setpriv --inh-caps=-all --ambient-caps=-all unshare --mount --pid --fork --net --ipc --uts /usr/bin/python /home/tv/repositorio-principal/reports/android16-hwc3-wayland/execute-graphics.py "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY" --observe-logs
