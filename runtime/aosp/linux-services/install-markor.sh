#!/system/bin/sh
# Trusted Linux installer orchestration of original PackageInstaller sessions.
# No boot/property mutation, API replacement, permission or signature override.
set -eu
set -o pipefail
apk_path=/data/local/tmp/markor.apk
apk_bytes=$(/system/bin/stat -c %s "$apk_path")
# Wait for the original AMS boot completion before asking it to start/unlock
# users. This only reads the original property; no readiness is manufactured.
boot_wait=0
while [ "$(/system/bin/getprop sys.boot_completed)" != 1 ] && [ "$boot_wait" -lt 200 ]; do
    boot_wait=$((boot_wait + 1)); /system/bin/sleep 1
done
[ "$(/system/bin/getprop sys.boot_completed)" = 1 ]

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
    # Keep stderr and actual status: an empty file alone cannot distinguish an
    # empty original inventory from a failed or unfinished Java tool.
    volume_status=0
    CLASSPATH=/system/framework/sm.jar /system/bin/app_process64 /system/bin com.android.commands.sm.Sm list-volumes all > /data/local/tmp/archtv-mc1/markor-volumes.txt 2>/data/local/tmp/archtv-mc1/markor-volumes-error.txt || volume_status=$?
    /system/bin/printf 'volume_query attempt=%s exit=%s\n' "$volume_wait" "$volume_status"
    [ "$volume_status" -eq 0 ]
    if /system/bin/grep -q '^emulated;0 mounted ' /data/local/tmp/archtv-mc1/markor-volumes.txt; then break; fi
    volume_wait=$((volume_wait + 1))
    /system/bin/sleep 1
done
/system/bin/grep -q '^emulated;0 mounted ' /data/local/tmp/archtv-mc1/markor-volumes.txt

# Actual original PMS state before install/update; no package state seeded.
/system/bin/cmd package path --user 0 net.gsantner.markor > /data/local/tmp/archtv-mc1/markor-preinstall-path.txt 2>&1 || :
/system/bin/dumpsys package net.gsantner.markor > /data/local/tmp/archtv-mc1/markor-preinstall-dump.txt 2>&1
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
# Original doWriteSplit accepts '-' through getInFd(). Feed a pipe from the
# shell owner: passing the file path (or redirecting that file descriptor)
# would require system_server to read shell_data_file, correctly denied by MAC.
/system/bin/cat "$apk_path" | /system/bin/cmd package install-write -S "$apk_bytes" "$session_id" base.apk -
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
# Shell cannot inspect private app data under the original MAC/DAC contracts.
# Retain this actual diagnostic result, without making it an installation or
# launch predicate. Privileged Linux evidence collection observes backings
# separately; never grant shell access or create application data here.
app_data_status=0
/system/bin/stat -c '%n|inode=%i|uid=%u|gid=%g|mode=%a' /data/user/0/net.gsantner.markor /data/user_de/0/net.gsantner.markor > /data/local/tmp/archtv-mc1/markor-app-data.txt 2>&1 || app_data_status=$?
/system/bin/printf 'shell_private_data_stat exit=%s NOT_APP_DATA_ACCEPTANCE\n' "$app_data_status" >> /data/local/tmp/archtv-mc1/markor-app-data.txt
# Observe HOME candidates; explicit Markor launch does not require shell to
# disable a protected platform component. Actual256 rejected that operation.
# This does not establish the final Linux-only desktop/product profile.
/system/bin/cmd package query-activities --brief --user 0 -a android.intent.action.MAIN -c android.intent.category.HOME > /data/local/tmp/archtv-mc1/markor-home-after.txt
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
if [ -f /data/local/tmp/archtv-mc1/archtv-markor-workflow-token ]; then
    token=$(/system/bin/cat /data/local/tmp/archtv-mc1/archtv-markor-workflow-token)
    case "$token" in ''|*[!0-9a-f]*) exit 1;; esac
    [ "${#token}" -eq 8 ] || exit 1
    # External shell observer uses the original shared-storage FUSE view;
    # it cannot read the private /data/media backing. Original shell is an
    # app_domain; no new FUSE grant or fabricated note is introduced here.
    # Successful shell observation still does not prove ordinary app isolation.
    # Use the original public FUSE view. Direct /mnt/user traversal is
    # intentionally restricted by original vold; never bypass it with groups.
    note=/storage/emulated/0/Documents/markor/archtv-$token.md
    expected="archtv note $token"
    # Command substitution strips trailing newlines. Require the exact byte
    # count too, so an autosave before the final Enter cannot trigger force-stop.
    expected_bytes=$((${#expected} + 1))
    # One original-client diagnostic for the demonstrated namespace/FUSE gap.
    # It changes no access, mounts, data, readiness or acceptance predicate.
    {
        /system/bin/id
        /system/bin/id -Z
        for observed in "/storage/emulated/0/Documents/markor/archtv-$token.md" "$note" "/mnt/user/0/emulated/Documents/markor/archtv-$token.md"; do
            observed_status=0
            /system/bin/stat -c '%n|size=%s|uid=%u|gid=%g|mode=%a' "$observed" || observed_status=$?
            /system/bin/printf 'observer_stat_exit=%s\n' "$observed_status"
        done
    } > /data/local/tmp/archtv-mc1/markor-observer-paths.txt 2>&1 || :
    budget=$(/system/bin/cat /data/local/tmp/archtv-mc1/archtv-markor-workflow-budget)
    case "$budget" in ''|*[!0-9]*) exit 1;; esac
    [ "$budget" -ge 15 ] && [ "$budget" -le 585 ] || exit 1
    n=0
    while [ "$n" -lt "$budget" ]; do
        if [ -f "$note" ] && [ "$(/system/bin/stat -c %s "$note")" -eq "$expected_bytes" ] && [ "$(/system/bin/cat "$note")" = "$expected" ]; then break; fi
        n=$((n+1)); /system/bin/sleep 1
    done
    [ -f "$note" ] || exit 1
    [ "$(/system/bin/stat -c %s "$note")" -eq "$expected_bytes" ] || exit 1
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
