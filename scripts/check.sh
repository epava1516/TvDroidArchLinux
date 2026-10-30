#!/usr/bin/env bash
set -euo pipefail
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"
for file in scripts/*.sh scripts/lib/*.sh packaging/session/archtv-session packaging/arch/*.sh packaging/arch/PKGBUILD.in; do bash -n "$file"; done
shellcheck -x -e SC1091,SC2034 scripts/*.sh scripts/lib/*.sh packaging/session/archtv-session packaging/arch/*.sh
python -m py_compile scripts/lib/*.py packaging/arch/*.py packaging/iso/*.py tools/apk/*.py
python - <<'CHECK'
from pathlib import Path
import re
import tomllib
for path in Path('manifests').glob('*.txt'):
    names = [line.strip() for line in path.read_text().splitlines() if line.strip() and not line.lstrip().startswith('#')]
    assert len(names) == len(set(names)), f'Duplicados en {path}'
    assert all(re.fullmatch(r'[a-z0-9@+_.-]+', name) for name in names), path
print('Manifiestos válidos')
revision = Path('lab/anvil/revision.txt').read_text().strip()
assert re.fullmatch(r'[0-9a-f]{40}', revision), 'Revisión Smithay inválida'
lock = tomllib.loads(Path('lab/anvil/Cargo.lock').read_text())
assert any(package['name'] == 'anvil' for package in lock['package']), 'Falta Anvil en Cargo.lock'
assert any(package['name'] == 'smithay' for package in lock['package']), 'Falta Smithay en Cargo.lock'
print('Revisión y Cargo.lock de Anvil válidos')
workspace = tomllib.loads(Path('Cargo.toml').read_text())
product = tomllib.loads(Path('Cargo.lock').read_text())
assert workspace['workspace']['dependencies']['smithay']['rev'] == revision
assert any(p['name'] == 'archtv-compositor' for p in product['package'])
assert any(p['name'] == 'archtv-test-client' for p in product['package'])
print('Workspace y lock del producto válidos')
CHECK
cargo fmt --all -- --check
echo 'Scripts, manifiestos, locks y formato Rust verificados; compilar y probar por separado.'
