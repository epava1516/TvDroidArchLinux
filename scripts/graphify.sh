#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"
graphify_bin="${GRAPHIFY_BIN:-$HOME/.local/bin/graphify}"
[[ -x "$graphify_bin" ]] || { echo 'Instala Graphify con ./scripts/68-graphify.sh --apply' >&2; exit 1; }
export GRAPHIFY_BACKEND=none GRAPHIFY_MAX_WORKERS=1 PYTHONHASHSEED=0
operation="${1:-status}"
if (($#)); then shift; fi
case "$operation" in
  build)
    "$graphify_bin" extract . --code-only --cargo --max-workers 1
    "$graphify_bin" cluster-only . --no-label
    "$graphify_bin" tree --label 'Arch TV · Rust/Smithay'
    ;;
  update)
    "$graphify_bin" update .
    "$graphify_bin" tree --label 'Arch TV · Rust/Smithay'
    ;;
  query|explain|path|affected|god-nodes|watch)
    exec "$graphify_bin" "$operation" "$@"
    ;;
  status)
    "$graphify_bin" --version
    python - <<'STATUS'
import json
from pathlib import Path
path=Path('graphify-out/graph.json')
if path.exists():
    data=json.loads(path.read_text())
    print(f"Mapa: {len(data.get('nodes',[]))} nodos, {len(data.get('links',data.get('edges',[])))} relaciones")
else:
    print('Mapa pendiente: ejecutar ./scripts/graphify.sh build')
for line in Path('ROADMAP.md').read_text().splitlines():
    if line.startswith('| H'):
        print(line)
STATUS
    ;;
  *) echo 'Uso: graphify.sh [status|build|update|query|explain|path|affected|god-nodes|watch] [argumentos]' >&2; exit 2 ;;
esac
