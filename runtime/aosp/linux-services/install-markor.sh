#!/system/bin/sh
# Trusted Linux installer orchestration of original PackageInstaller sessions.
# No boot/property mutation, API replacement, permission or signature override.
set -eu
apk_path=/data/local/tmp/markor.apk
apk_bytes=$(/system/bin/stat -c %s "$apk_path")
# Install into an actually unlocked, mounted original user environment.
# Original state immediately before a possibly blocking user-start, not a replacement.
/system/bin/dumpsys activity processes > /data/local/tmp/archtv-mc1/markor-boot-before-user.txt
# UserController can return early for the current running/locked user without
# registering start-user -w's listener. Observe the original state instead of
# making a redundant start request and waiting on an unregistered callback.
if /system/bin/cmd activity get-started-user-state 0 > /data/local/tmp/archtv-mc1/markor-user-state.txt 2>&1; then
    user_state=$(/system/bin/cat /data/local/tmp/archtv-mc1/markor-user-state.txt)
    case "$user_state" in
        BOOTING|RUNNING_LOCKED|RUNNING_UNLOCKING|RUNNING_UNLOCKED) ;;
        *) /system/bin/cat /data/local/tmp/archtv-mc1/markor-user-state.txt >&2; exit 1 ;;
    esac
else
    /system/bin/cmd activity start-user 0 > /data/local/tmp/archtv-mc1/markor-user-start.txt 2>&1
fi
user_wait=0
while [ "$user_wait" -lt 120 ]; do
    /system/bin/cmd activity get-started-user-state 0 > /data/local/tmp/archtv-mc1/markor-user-state.txt
    if /system/bin/grep -qx RUNNING_UNLOCKED /data/local/tmp/archtv-mc1/markor-user-state.txt; then break; fi
    user_wait=$((user_wait + 1))
    /system/bin/sleep 1
done
/system/bin/grep -qx RUNNING_UNLOCKED /data/local/tmp/archtv-mc1/markor-user-state.txt
# Launch only after the actual original volume is mounted; no volume or user
# property is assigned. The same original Sm class is used with our real ABI.
volume_wait=0
while [ "$volume_wait" -lt 120 ]; do
    CLASSPATH=/system/framework/sm.jar /system/bin/app_process64 /system/bin com.android.commands.sm.Sm list-volumes all > /data/local/tmp/archtv-mc1/markor-volumes.txt
    if /system/bin/grep -q '^emulated;0 mounted ' /data/local/tmp/archtv-mc1/markor-volumes.txt; then break; fi
    volume_wait=$((volume_wait + 1))
    /system/bin/sleep 1
done
/system/bin/grep -q '^emulated;0 mounted ' /data/local/tmp/archtv-mc1/markor-volumes.txt

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
# Preserve the original PMS readback before user-start can block or the cohort stops.
/system/bin/cmd package path --user 0 net.gsantner.markor > /data/local/tmp/archtv-mc1/markor-postcommit-path.txt
/system/bin/dumpsys package net.gsantner.markor > /data/local/tmp/archtv-mc1/markor-postcommit-dump.txt
IFS= read -r installed_line < /data/local/tmp/archtv-mc1/markor-postcommit-path.txt
case "$installed_line" in package:/data/app/*/base.apk) ;; *) exit 1;; esac
installed_apk=${installed_line#package:}
source_hash=$(/system/bin/sha256sum "$apk_path")
installed_hash=$(/system/bin/sha256sum "$installed_apk")
[ "${source_hash%% *}" = "${installed_hash%% *}" ] || exit 1
/system/bin/printf 'SOURCE %s\nINSTALLED %s\n' "$source_hash" "$installed_hash" > /data/local/tmp/archtv-mc1/markor-installed-bytes.txt
# Observe directories created by original PMS/installd; never mkdir app data.
/system/bin/stat -c '%n|inode=%i|uid=%u|gid=%g|mode=%a' /data/user/0/net.gsantner.markor /data/user_de/0/net.gsantner.markor > /data/local/tmp/archtv-mc1/markor-app-data.txt 2>&1
/system/bin/ls -ldZ /data/user/0/net.gsantner.markor /data/user_de/0/net.gsantner.markor >> /data/local/tmp/archtv-mc1/markor-app-data.txt
# Retire only the original bootstrap component after real framework unlock.
/system/bin/cmd package disable --user 0 com.android.settings/.FallbackHome > /data/local/tmp/archtv-mc1/markor-bootstrap-home-stop.txt
/system/bin/cmd activity force-stop --user 0 com.android.settings
/system/bin/cmd package query-activities --brief --user 0 -a android.intent.action.MAIN -c android.intent.category.HOME > /data/local/tmp/archtv-mc1/markor-home-after.txt
/system/bin/grep -qx 'No activities found' /data/local/tmp/archtv-mc1/markor-home-after.txt
resolved=$(/system/bin/cmd package resolve-activity --brief --user 0 -a android.intent.action.MAIN -c android.intent.category.LAUNCHER net.gsantner.markor)
/system/bin/printf '%s\n' "$resolved" > /data/local/tmp/archtv-mc1/markor-resolve.txt
component=$(/system/bin/printf '%s\n' "$resolved" | /system/bin/tail -n 1)
case "$component" in net.gsantner.markor/*) ;; *) exit 1;; esac
/system/bin/cmd activity start-activity -W --user 0 -n "$component" > /data/local/tmp/archtv-mc1/markor-launch.txt 2>&1
# Actual APIs and pixels after launch, not an app-compatibility success marker.
CLASSPATH=/system/framework/sm.jar /system/bin/app_process64 /system/bin com.android.commands.sm.Sm list-volumes all > /data/local/tmp/archtv-mc1/markor-volumes.txt
/system/bin/cmd overlay list --user 0 > /data/local/tmp/archtv-mc1/markor-overlays.txt
/system/bin/cat /proc/self/mountinfo > /data/local/tmp/archtv-mc1/markor-mountinfo.txt
/system/bin/screencap -p /data/local/tmp/archtv-mc1/markor-sf.png

# Optional real-APK lifecycle experiment. Only the UI may create/write the note.
if [ -f /vendor/etc/archtv-markor-workflow-token ]; then
    token=$(/system/bin/cat /vendor/etc/archtv-markor-workflow-token)
    case "$token" in ''|*[!0-9a-f]*) exit 1;; esac
    [ "${#token}" -eq 8 ] || exit 1
    # Privileged original system_server observer, not an app access test.
    # media_rw is in pinned original ZygoteInit groups; do not expand app FUSE access.
    note=/data/media/0/Documents/archtv-$token.md
    expected="archtv note $token"
    n=0
    while [ "$n" -lt 165 ]; do
        if [ -f "$note" ] && [ "$(/system/bin/cat "$note")" = "$expected" ]; then break; fi
        n=$((n+1)); /system/bin/sleep 1
    done
    [ -f "$note" ] || exit 1
    [ "$(/system/bin/cat "$note")" = "$expected" ] || exit 1
    [ "$(/system/bin/stat -c %s "$note")" -le 4096 ]
    /system/bin/cat "$note" > /data/local/tmp/archtv-mc1/markor-note-bytes.bin
    /system/bin/sha256sum "$note" > /data/local/tmp/archtv-mc1/markor-note-before-stop.txt
    before=$(/system/bin/pidof net.gsantner.markor)
    case "$before" in ''|*[!0-9]*) exit 1;; esac
    /system/bin/printf 'before_pid=%s\n' "$before" > /data/local/tmp/archtv-mc1/markor-lifecycle.txt
    /system/bin/cmd activity force-stop --user 0 net.gsantner.markor >> /data/local/tmp/archtv-mc1/markor-lifecycle.txt 2>&1
    n=0
    while [ -d /proc/$before ] && [ "$n" -lt 10 ]; do n=$((n+1)); /system/bin/sleep 1; done
    [ ! -d /proc/$before ]
    /system/bin/printf 'previous_process_absent=%s\n' "$before" >> /data/local/tmp/archtv-mc1/markor-lifecycle.txt
    /system/bin/cmd activity start-activity -W --user 0 -n "$component" > /data/local/tmp/archtv-mc1/markor-relaunch.txt 2>&1
    /system/bin/grep -qx 'Status: ok' /data/local/tmp/archtv-mc1/markor-relaunch.txt
    after=$(/system/bin/pidof net.gsantner.markor)
    case "$after" in ''|*[!0-9]*) exit 1;; esac
    [ "$after" != "$before" ]
    /system/bin/printf 'after_pid=%s\n' "$after" >> /data/local/tmp/archtv-mc1/markor-lifecycle.txt
    /system/bin/sha256sum "$note" > /data/local/tmp/archtv-mc1/markor-note-after-relaunch.txt
fi
