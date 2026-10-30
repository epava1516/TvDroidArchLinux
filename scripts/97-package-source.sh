#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
cd "$root"
if ! "$APPLY"; then echo 'Archivará las fuentes comprometidas, con SHA-256 y receta para tres paquetes Arch. No compila ni instala.'; exit 0; fi
paths=(Cargo.toml Cargo.lock crates licenses LICENSE THIRD_PARTY.md packaging)
[[ -z $(git status --porcelain --untracked-files=all -- "${paths[@]}") ]] || { echo 'Guarda primero las modificaciones de fuentes en Git.' >&2; exit 1; }
base_version=$(python -c 'import tomllib; print(tomllib.load(open("Cargo.toml","rb"))["workspace"]["package"]["version"])')
version="$base_version.r$(git rev-list --count HEAD).g$(git rev-parse --short=12 HEAD)"
output="$root/dist/packages/$version"
mkdir -p "$output"
archive="$output/archtv-$version.tar.gz"
git archive --format=tar --prefix="archtv-$version/" HEAD "${paths[@]}" | gzip -n > "$archive"
python - "$root" "$output" "$version" "$archive" <<'RECIPE'
import hashlib
from pathlib import Path
import sys
root, output, version, archive = sys.argv[1:]
text = (Path(root)/'packaging/arch/PKGBUILD.in').read_text()
text = text.replace('@PKGVER@', version).replace('@SOURCE_SHA256@', hashlib.sha256(Path(archive).read_bytes()).hexdigest())
(Path(output)/'PKGBUILD').write_text(text)
RECIPE
(cd "$output" && makepkg --printsrcinfo > .SRCINFO && makepkg --verifysource)
git rev-parse HEAD > "$output/source-commit.txt"
git show -s --format=%ct HEAD > "$output/source-date-epoch.txt"
sha256sum "$archive" "$output/PKGBUILD" > "$output/SHA256SUMS"
printf 'Fuentes y receta verificadas: %s\n' "$output"
