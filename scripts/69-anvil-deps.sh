#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
manifest_packages "$root/manifests/anvil-lab.txt"
echo 'Weston es un anfitrión temporal de pruebas, no un componente del producto.'
