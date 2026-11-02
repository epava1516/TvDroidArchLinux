#!/system/bin/sh
# Trusted Linux installer orchestration of original PackageInstaller sessions.
# No boot/property mutation, API replacement, permission or signature override.
set -eu
apk_path=/data/local/tmp/markor.apk
apk_bytes=$(/system/bin/stat -c %s "$apk_path")
created=$(/system/bin/cmd package install-create --user 0 -i android -S "$apk_bytes")
/system/bin/printf '%s\n' "$created"
case "$created" in
 'Success: created install session ['*']') ;;
 *) exit 1 ;;
esac
session_id=${created##*\[}
session_id=${session_id%\]}
case "$session_id" in ''|*[!0-9]*) exit 1;; esac
committed=false
trap 'task_status=$?; if [ "$committed" = false ]; then /system/bin/cmd package install-abandon "$session_id" >&2 || :; fi; exit "$task_status"' EXIT
/system/bin/cmd package install-write -S "$apk_bytes" "$session_id" base.apk "$apk_path"
/system/bin/cmd package install-commit "$session_id"
committed=true
/system/bin/cmd activity start-user -w 0 > /data/local/tmp/archtv-mc1/markor-user-start.txt 2>&1
resolved=$(/system/bin/cmd package resolve-activity --brief --user 0 -a android.intent.action.MAIN -c android.intent.category.LAUNCHER net.gsantner.markor)
/system/bin/printf '%s\n' "$resolved" > /data/local/tmp/archtv-mc1/markor-resolve.txt
component=$(/system/bin/printf '%s\n' "$resolved" | /system/bin/tail -n 1)
case "$component" in net.gsantner.markor/*) ;; *) exit 1;; esac
/system/bin/cmd activity start-activity -W --user 0 -n "$component" > /data/local/tmp/archtv-mc1/markor-launch.txt 2>&1
