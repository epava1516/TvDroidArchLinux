#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
if ! "$APPLY"; then echo 'Experimento multimedia H6; requiere sesión Android/VLC activa. No certifica reproducción por sí solo.'; exit 0; fi
report="${ARCHTV_ANDROID_REPORT:-$root/reports/h6-media}"
mkdir -p "$report"
media="${XDG_CACHE_HOME:-$HOME/.cache}/archtv/media"
mkdir -p "$media"
ffmpeg -hide_banner -loglevel error -f lavfi -i testsrc2=size=640x360:rate=15 \
  -f lavfi -i sine=frequency=440:sample_rate=48000 -t 30 -af volume=0.05 \
  -c:v libx264 -preset ultrafast -crf 28 -pix_fmt yuv420p -c:a aac \
  -movflags +faststart -y "$media/archtv-av-test.mp4"
XDG_RUNTIME_DIR="/run/user/$(id -u)"
export XDG_RUNTIME_DIR
export PULSE_SERVER="unix:$XDG_RUNTIME_DIR/pulse/native"
server=''
recorder=''
cleanup() {
  for pid in "$recorder" "$server"; do
    if [[ -n "$pid" ]]; then kill -INT "$pid" 2>/dev/null || true; kill "$pid" 2>/dev/null || true; wait "$pid" 2>/dev/null || true; fi
  done
}
trap cleanup EXIT
python -m http.server 8765 --bind 192.168.240.1 --directory "$media" > "$report/media-http.log" 2>&1 &
server=$!
sink=$(pactl get-default-sink)
parec --device="$sink.monitor" --format=s16le --rate=48000 --channels=2 --file-format=wav "$report/audio-monitor.wav" > "$report/audio-capture.log" 2>&1 &
recorder=$!
sleep 1
sudo -n timeout -k 2 10 lxc-attach -P /var/lib/waydroid/lxc -n waydroid -- /system/bin/env PATH=/system/bin:/system/xbin /system/bin/am start -n org.videolan.vlc/.gui.video.VideoPlayerActivity -a android.intent.action.VIEW -d http://192.168.240.1:8765/archtv-av-test.mp4 -t video/mp4 2>&1 | cat > "$report/playback-intent.txt"
sleep 2
# First-run VLC tutorial is setup, separate from the uinput navigation proof.
sudo -n timeout -k 2 8 lxc-attach -P /var/lib/waydroid/lxc -n waydroid -- /system/bin/env PATH=/system/bin:/system/xbin /system/bin/input tap 40 40
sudo -n timeout -k 2 8 lxc-attach -P /var/lib/waydroid/lxc -n waydroid -- /system/bin/env PATH=/system/bin:/system/xbin /system/bin/input keyevent 126
sleep 3
sudo -n timeout -k 2 10 lxc-attach -P /var/lib/waydroid/lxc -n waydroid -- /system/bin/screencap -p | cat > "$report/video-frame-a.png"
sleep 3
sudo -n timeout -k 2 10 lxc-attach -P /var/lib/waydroid/lxc -n waydroid -- /system/bin/screencap -p | cat > "$report/video-frame-b.png"
sudo -n timeout -k 2 8 lxc-attach -P /var/lib/waydroid/lxc -n waydroid -- /system/bin/dumpsys media.audio_flinger 2>&1 | cat > "$report/android-audio.txt"
pactl list sink-inputs > "$report/pipewire-streams.txt"

sha256sum "$media/archtv-av-test.mp4" > "$report/media-sha256.txt"
echo 'CAPTURED: inspect frames, timing and continuous audio; this is not a PASS.' > "$report/media-result.txt"
