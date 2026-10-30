#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
manifest_packages "$root/manifests/base.txt"
run sudo systemctl enable --now NetworkManager.service
run sudo systemctl enable --now systemd-timesyncd.service
echo 'Se conserva la configuración existente de zram, cuentas, sudoers y red.'
