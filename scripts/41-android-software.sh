#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
echo 'Perfil opcional para VM sin aceleración: detiene el contenedor Android y configura SwiftShader.'
run waydroid session stop
run sudo systemctl stop waydroid-container.service
run sudo python "$root/scripts/lib/waydroid-software.py"
run sudo waydroid upgrade -o
run sudo systemctl start waydroid-container.service
