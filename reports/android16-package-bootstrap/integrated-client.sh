#!/usr/bin/env bash
set -euo pipefail
run_id=$(/usr/bin/python -c 'import uuid;print(uuid.uuid4())')
unit="archtv-package-runner-$run_id"
experiment_kind=$(/usr/bin/python -c 'import json;from pathlib import Path;d=json.loads(Path("/home/tv/repositorio-principal/dist/aosp16/package-cohort-build-104/build-options.json").read_text());print(d.get("experiment_kind") or ("keymint-component" if d.get("keymint_component_diagnostic") else "markor-launch"))')
checkpoint="/home/tv/recuperacion-archtv/$run_id-$experiment_kind"
mkdir -m 700 "$checkpoint"
# Bind destination now, never discover a different daemon at delivery time.
: "${ARCHTV_CODEX_REMOTE:?explicit Codex remote required}" "${ARCHTV_CODEX_THREAD:?explicit thread required}"
/usr/bin/python - "$checkpoint" "$run_id" "$unit" "$ARCHTV_CODEX_REMOTE" "$ARCHTV_CODEX_THREAD" "$experiment_kind" <<'MANIFEST'
import json,sys
from pathlib import Path
cp,run,unit,remote,thread,kind=sys.argv[1:]
p=Path(cp)/'completion-manifest.json'
assert kind in ('keymint-component','keystore-component','keystore-java-component','markor-software-launch','markor-launch')
name={'keymint-component':'KeyMint v4 software component','keystore-component':'Original Keystore2 software Binder integration','keystore-java-component':'Original Java Keystore software integration','markor-software-launch':'Markor original software-security launch','markor-launch':'Markor integrated launch'}[kind]
with p.open('x') as f:json.dump(dict(id=run,checkpoint=cp,unit=unit,owner=unit,name=name,active_owner='active:'+run,remote=remote,thread=thread),f)
p.chmod(0o444)
MANIFEST
exec sudo -n systemd-run --unit="$unit" --wait --pipe --collect --property=RuntimeMaxSec=420 --property=KillMode=control-group --property=MemoryMax=512M --setenv="ARCHTV_RUN_CHECKPOINT=$checkpoint" --property="ExecStopPost=/usr/bin/python /home/tv/repositorio-principal/scripts/run_completion.py $checkpoint/completion-manifest.json" --working-directory=/home/tv/repositorio-principal /usr/bin/python /home/tv/repositorio-principal/reports/android16-apex-bootstrap/run.py dist/aosp16/package-cohort-build-104/payload-2.ext4 /home/tv/.cache/archtv/aosp16-qpr2/apex-data-store-1 "$XDG_RUNTIME_DIR/$WAYLAND_DISPLAY"
