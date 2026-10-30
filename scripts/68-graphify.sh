#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
venv="$HOME/.local/share/archtv-tools/graphify"
run python -m venv "$venv"
run "$venv/bin/python" -m pip install -r "$root/lab/graphify/requirements.txt"
if ! "$APPLY"; then exit 0; fi
mkdir -p "$HOME/.local/bin"
ln -sfn "$venv/bin/graphify" "$HOME/.local/bin/graphify"
cd "$root"
export GRAPHIFY_BACKEND=none GRAPHIFY_MAX_WORKERS=1 PYTHONHASHSEED=0
"$venv/bin/graphify" install --project --platform codex
"$venv/bin/graphify" hook install
mkdir -p graphify-out
printf '%s\n' "$venv/bin/python" > graphify-out/.graphify_python
# Keep hook rebuilds local and bounded on the development VM.
python - "$root" <<'PATCH'
from pathlib import Path
import sys
root=Path(sys.argv[1])
for name in ['post-commit','post-checkout','post-merge','post-rewrite']:
    path=root/'.git/hooks'/name
    text=path.read_text()
    marker='# graphify-hook-start\n'
    settings='export GRAPHIFY_BACKEND=none\nexport GRAPHIFY_MAX_WORKERS=1\n'
    if settings not in text:
        path.write_text(text.replace(marker,marker+settings,1))
PATCH
# A new interactive Bash shell can find the installed CLI directly.
python - "$HOME/.bashrc" <<'SHELL'
from pathlib import Path
import sys
path=Path(sys.argv[1])
text=path.read_text() if path.exists() else ''
marker='# Arch TV development tools'
if marker not in text:
    path.write_text(text+'\n'+marker+'\nexport PATH="$HOME/.local/bin:$PATH"\n')
SHELL
"$venv/bin/graphify" --version
