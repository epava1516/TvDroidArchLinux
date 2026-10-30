#!/usr/bin/env bash
# Internal client: public Wayland socket only, no privileged shell identity.
set -euo pipefail
report="${ARCHTV_ANDROID_REPORT:?Set diagnostic report directory}"
unset WAYLAND_SOCKET ARCHTV_CONTROL_FD
waydroid session start > "$report/session.log" 2>&1 &
session_pid=$!
cleanup() {
  waydroid session stop || true
  kill "$session_pid" 2>/dev/null || true
}
trap cleanup EXIT
sleep 3
waydroid show-full-ui > "$report/ui.log" 2>&1 &
wait "$session_pid"
