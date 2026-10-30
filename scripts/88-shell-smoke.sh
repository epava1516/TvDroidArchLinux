#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
target="${CARGO_TARGET_DIR:-$root/target}"
if ! "$APPLY"; then echo 'Probará el shell Rust por DRM/Pixman con mando uinput y configuración aislada.'; exit 0; fi
[[ -z $(loginctl list-sessions --no-legend) ]]
if systemctl is-active --quiet getty@tty2.service; then echo 'tty2 tiene un getty activo.' >&2; exit 1; fi
report="$root/reports/h5-interactive"
mkdir -p "$report"
rm -f "$report/result.txt" "$report/compositor.log" "$report/ui-sequence.txt" "$report/startup.png" "$report/scanout.ppm"
rm -rf "$report/states"
fixture=$(mktemp -d)
initial_vt=$(sudo -n fgconsole)
unit="archtv-h5-$$"
cleanup() {
  local result=$?
  trap - EXIT
  sudo -n systemctl stop "$unit.service" 2>/dev/null || true
  sudo -n chvt "$initial_vt" || true
  rm -rf -- "$fixture"
  if ((result)); then echo 'FAIL: shell interactivo; consultar logs.' > "$report/result.txt"; fi
  exit "$result"
}
trap cleanup EXIT
python - "$fixture" "$target" <<'FIXTURE'
from pathlib import Path
import sys
import struct
import zlib
root,target=map(Path,sys.argv[1:])
data=root/'data'
apps=data/'applications'
apps.mkdir(parents=True)
(root/'config').mkdir()
icon=data/'probe.svg'
icon.write_text('<svg xmlns="http://www.w3.org/2000/svg" width="96" height="96"><rect width="96" height="96" rx="20" fill="#309d92"/><path d="M24 24h48v48H24z" fill="#fff"/></svg>')
png=data/'probe.png'
def chunk(kind,content):
    return struct.pack('>I',len(content))+kind+content+struct.pack('>I',zlib.crc32(kind+content))
rows=b''.join(b'\0'+bytes([45,112,170,255])*32 for _ in range(32))
png.write_bytes(b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR',struct.pack('>IIBBBBB',32,32,8,6,0,0,0))+chunk(b'IDAT',zlib.compress(rows))+chunk(b'IEND',b''))
broken=data/'broken.png'
broken.write_bytes(b'not a PNG')
terminal=root/'terminal-probe.py'
receipt=root/'terminal-typed.txt'
ready=root/'terminal-ready.txt'
terminal.write_text(f"""import sys, termios, tty
from pathlib import Path
old=termios.tcgetattr(sys.stdin)
try:
    tty.setraw(sys.stdin.fileno())
    Path({str(ready)!r}).write_text('ready')
    print('Arch TV: terminal Wayland real. Escape cierra la prueba.', flush=True)
    while True:
        ch=sys.stdin.read(1)
        if ch==chr(27): break
        if ch:
            Path({str(receipt)!r}).write_text(ch)
            print('Entrada recibida: '+repr(ch), flush=True)
finally:
    termios.tcsetattr(sys.stdin,termios.TCSADRAIN,old)
""")
for name,title,image in [('01-archtv-probe.desktop','Cliente A',icon),('02-archtv-second.desktop','Cliente B',png),('03-broken-icon.desktop','Sin icono',broken)]:
    program=str(target/'debug/archtv-test-client').replace('\\','\\\\').replace('"','\\"')
    command=f'"{program}" 0 --close-on-escape'
    if name=='01-archtv-probe.desktop':
        command=f'foot --app-id org.archtv.TerminalProbe --title "Arch TV · terminal real" -- /usr/bin/python "{terminal}"'
    (apps/name).write_text(f'[Desktop Entry]\nType=Application\nName={title}\nExec={command}\nIcon={image}\nTerminal=false\n')

FIXTURE
sudo -n systemd-run --unit="$unit" --collect \
  --property="User=$(id -un)" --property=PAMName=login --property=TTYPath=/dev/tty2 \
  --property=StandardInput=tty --property=TTYReset=yes --property=TTYVHangup=yes \
  --property=KillMode=control-group --property=TimeoutStopSec=10 \
  --property='RestrictAddressFamilies=AF_UNIX AF_NETLINK AF_PACKET' \
  --setenv="CARGO_TARGET_DIR=$target" --setenv="ARCHTV_SHELL_REPORT=$report" \
  --setenv="XDG_DATA_HOME=$fixture/data" --setenv="XDG_DATA_DIRS=$fixture/empty" \
  --setenv="XDG_CONFIG_HOME=$fixture/config" --setenv=RUST_LOG=archtv_compositor=debug,smithay=warn \
  "$root/scripts/87-shell-session.sh"
sudo -n chvt 2
sudo -n python "$root/scripts/lib/tv-ui-probe.py" "$report" "$fixture/config"
cp "$fixture/config/archtv/settings.json" "$report/persisted-settings.json"
cp "$fixture/terminal-typed.txt" "$report/terminal-input.txt"
# Restart the real shell and verify the persisted catalog/order loads again.
shell_pid=$(sed -n 's/.*SESSION_CHILD_STARTED pid=\([0-9]*\) shell=true.*/\1/p' "$report/compositor.log" | tail -1)
kill "$shell_pid"
for ((attempt=0;attempt<120;attempt++)); do
  if [[ $(rg -c SHELL_CATALOG "$report/compositor.log") -ge 2 ]] && \
     [[ $(rg -c SHELL_SURFACE_READY "$report/compositor.log") -ge 2 ]] && \
     [[ $(rg -c SHELL_CAPTURED "$report/compositor.log") -ge 2 ]]; then break; fi
  sleep 0.1
done
[[ $(rg -c SHELL_SURFACE_READY "$report/compositor.log") -ge 2 ]]
[[ $(rg -c SHELL_CAPTURED "$report/compositor.log") -ge 2 ]]
rg -q 'SHELL_CATALOG applications=3 favorites=2 hidden=0 recent=1' "$report/compositor.log"
rg -q 'SHELL_ICON id=02-archtv-second.desktop loaded=true' "$report/compositor.log"
rg -q 'SHELL_ICON id=01-archtv-probe.desktop loaded=true' "$report/compositor.log"
rg -q 'SHELL_ICON id=03-broken-icon.desktop loaded=false' "$report/compositor.log"
for ((attempt=0;attempt<150;attempt++)); do
  [[ -s "$report/scanout.ppm" ]] && break
  sleep 0.1
done
[[ -s "$report/scanout.ppm" ]]
python "$root/scripts/lib/ppm-to-png.py" "$report/scanout.ppm" "$report/scanout.png"
sudo -n systemctl kill --signal=SIGTERM --kill-whom=main "$unit.service"
for ((attempt=0;attempt<80;attempt++)); do
  systemctl is-active --quiet "$unit.service" || break
  sleep 0.1
done
rg -q TV_COMPOSITOR_STOPPED "$report/compositor.log"
rg -q DRM_STOPPED "$report/compositor.log"
if rg -q 'panicked|DRM_.*FAILED' "$report/compositor.log"; then exit 1; fi
{
  date -u '+Fecha UTC: %Y-%m-%dT%H:%M:%SZ'
  cat "$report/ui-sequence.txt"
  echo 'PASS: PNG/SVG fallback, persisted settings and shell restart; real DRM/Pixman presentation.'
  echo 'IP socket families disabled for the session; no Android session started.'
} > "$report/result.txt"
echo 'Prueba del shell correcta; ver reports/h5-interactive/.'
