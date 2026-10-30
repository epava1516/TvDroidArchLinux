#!/usr/bin/env bash
set -euo pipefail
clock_path=/sys/devices/system/clocksource/clocksource0/current_clocksource
original=$(cat "$clock_path")
[[ "$original" == tsc ]]
[[ " $(cat /sys/devices/system/clocksource/clocksource0/available_clocksource) " == *' kvm-clock '* ]]
restore() {
  printf '%s\n' "$original" > "$clock_path"
  printf 'Restored clocksource: %s\n' "$(cat "$clock_path")"
}
trap restore EXIT
printf 'Original clocksource: %s\n' "$original"
printf 'kvm-clock\n' > "$clock_path"
[[ $(cat "$clock_path") == kvm-clock ]]
python /home/tv/repositorio-principal/scripts/lib/clock-probe.py /home/tv/repositorio-principal/reports/h6-lts-stability/clock-kvm.json --seconds 20
