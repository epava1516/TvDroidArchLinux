#!/usr/bin/env bash
set -euo pipefail
unit="archtv-package-runner-$(date -u +%s%N)"
exec sudo -n systemd-run --unit="$unit" --wait --pipe --collect --property=RuntimeMaxSec=270 --property=KillMode=control-group --property=MemoryMax=512M --property=ExecStopPost='/usr/bin/python /home/tv/.cache/archtv/kernel-aosp16-1/apex-completion.py' --working-directory=/home/tv/repositorio-principal /usr/bin/python /home/tv/repositorio-principal/reports/android16-apex-bootstrap/run.py dist/aosp16/package-cohort-build-20/payload-2.ext4 /home/tv/.cache/archtv/aosp16-qpr2/apex-data-store-1 "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY"
