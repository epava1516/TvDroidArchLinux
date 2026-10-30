#!/usr/bin/env bash
set -euo pipefail
source "$(dirname -- "${BASH_SOURCE[0]}")/lib/common.sh"
user_only
root=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)
echo 'Preparará Linux LTS y una entrada separada de systemd-boot; la selección predeterminada se conserva.'
manifest_packages "$root/manifests/kernel-lab.txt"
run sudo python "$root/scripts/lib/lts-boot-entry.py" /boot/loader/entries/arch.conf /boot/loader/entries/archtv-lts.conf
