#!/usr/bin/env bash
# Diagnostic only: boot_completed is necessary but does not certify usable Android.
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
target="${CARGO_TARGET_DIR:-$root/target}"
if ! "$APPLY"; then echo 'Probará arranque Android y captura DRM a 720p; hasta 9 minutos, conservando datos.'; exit 0; fi
[[ -z $(loginctl list-sessions --no-legend) ]]
[[ $(sudo -n lxc-info -P /var/lib/waydroid/lxc -n waydroid -sH) == STOPPED ]]
if systemctl is-active --quiet getty@tty2.service; then echo 'tty2 ocupado.' >&2; exit 1; fi
report="${ARCHTV_ANDROID_REPORT:-$root/reports/h6-boot-probe}"
mkdir -p "$report"
report=$(realpath "$report")
rm -f "$report/scanout.ppm" "$report/scanout.png" "$report/boot-completed.txt"
echo 'RUNNING: Android boot diagnostic' > "$report/result.txt"
unit="archtv-h6-$$"
initial_vt=$(sudo -n fgconsole)
cleanup() {
  local result=$?
  trap - EXIT
  sudo -n systemctl stop "$unit.service" 2>/dev/null || true
  waydroid session stop || true
  sudo -n timeout -k 3 20 waydroid container stop || true
  sudo -n chvt "$initial_vt" || true
  # lxc/waydroid may change the owner of inherited diagnostic stdout files.
  sudo -n chown -R "$(id -u):$(id -g)" "$report"
  if ((result)); then echo 'FAIL: boot diagnostic; inspect logs. H6 remains unverified.' > "$report/result.txt"; fi
  exit "$result"
}
trap cleanup EXIT
uname -a > "$report/host-kernel.txt"
free -h > "$report/memory-before.txt"
lscpu > "$report/cpu.txt"
pacman -Q waydroid lxc linux > "$report/host-packages.txt"
sudo -n cat /var/lib/waydroid/waydroid.cfg | cat > "$report/waydroid.cfg"
sudo -n sha256sum /var/lib/waydroid/images/system.img /var/lib/waydroid/images/vendor.img | cat > "$report/image-sha256.txt"
sudo -n systemd-run --unit="$unit" --collect \
  --property="User=$(id -un)" --property=PAMName=login --property=TTYPath=/dev/tty2 \
  --property=StandardInput=tty --property=TTYReset=yes --property=TTYVHangup=yes \
  --property=KillMode=control-group --property=TimeoutStopSec=15 \
  --setenv="CARGO_TARGET_DIR=$target" --setenv="ARCHTV_ANDROID_REPORT=$report" \
  --setenv=RUST_LOG=archtv_compositor=debug,smithay=info "$root/scripts/90-android-session.sh"
sudo -n chvt 2
started=$SECONDS
booted=false
while ((SECONDS-started<540)); do
  systemctl is-active --quiet "$unit.service" || break
  property=$(sudo -n timeout -k 2 8 lxc-attach -P /var/lib/waydroid/lxc -n waydroid -- /system/bin/getprop sys.boot_completed 2>/dev/null || true)
  if [[ ${property//$'\r'/} == 1 ]]; then
    if ! "$booted"; then
      printf '1\n' > "$report/boot-completed.txt"
      date -u '+Boot observed UTC: %Y-%m-%dT%H:%M:%SZ' > "$report/boot-observed.txt"
      echo "elapsed_seconds=$((SECONDS-started))" >> "$report/boot-observed.txt"
      booted=true
    fi
  fi
  [[ -s "$report/scanout.ppm" ]] && "$booted" && break
  sleep 5
done
sudo -n timeout -k 2 15 lxc-attach -P /var/lib/waydroid/lxc -n waydroid -- /system/bin/logcat -b crash -d 2>&1 | cat > "$report/crash.txt" || true
sudo -n timeout -k 2 15 lxc-attach -P /var/lib/waydroid/lxc -n waydroid -- /system/bin/logcat -d -t 500 2>&1 | cat > "$report/logcat-tail.txt" || true
sudo -n chown -R "$(id -u):$(id -g)" "$report"
free -h > "$report/memory-after.txt"
"$booted"
[[ -s "$report/scanout.ppm" ]]
python "$root/scripts/lib/ppm-to-png.py" "$report/scanout.ppm" "$report/scanout.png"
{
  date -u '+Fecha UTC: %Y-%m-%dT%H:%M:%SZ'
  echo 'PARTIAL: sys.boot_completed=1 observed and real DRM screenshot captured.'
  echo 'Inspect screenshot and crash log. Usable apps/input/audio/video/recovery remain unverified; H6 is not closed.'
} > "$report/result.txt"
