#!/usr/bin/env bash
set -euo pipefail
run_id=$(/usr/bin/python -c 'import uuid;print(uuid.uuid4())')
unit="archtv-package-runner-$run_id"
checkpoint="/home/tv/recuperacion-archtv/$run_id-markor-launch"
mkdir -m 700 "$checkpoint"
# Bind destination now, never discover a different daemon at delivery time.
: "${ARCHTV_CODEX_REMOTE:?explicit Codex remote required}" "${ARCHTV_CODEX_THREAD:?explicit thread required}"
/usr/bin/python - "$checkpoint" "$run_id" "$unit" "$ARCHTV_CODEX_REMOTE" "$ARCHTV_CODEX_THREAD" <<'MANIFEST'
import json,sys
from pathlib import Path
cp,run,unit,remote,thread=sys.argv[1:]
p=Path(cp)/'completion-manifest.json'
with p.open('x') as f:json.dump(dict(id=run,checkpoint=cp,unit=unit,owner=unit,name='Markor integrated launch',remote=remote,thread=thread),f)
p.chmod(0o444)
MANIFEST
exec sudo -n systemd-run --unit="$unit" --wait --pipe --collect --property=RuntimeMaxSec=270 --property=KillMode=control-group --property=MemoryMax=512M --setenv="ARCHTV_RUN_CHECKPOINT=$checkpoint" --property="ExecStopPost=/usr/bin/python /home/tv/repositorio-principal/scripts/run_completion.py $checkpoint/completion-manifest.json" --working-directory=/home/tv/repositorio-principal /usr/bin/python /home/tv/repositorio-principal/reports/android16-apex-bootstrap/run.py dist/aosp16/package-cohort-build-20/payload-2.ext4 /home/tv/.cache/archtv/aosp16-qpr2/apex-data-store-1 "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY"
