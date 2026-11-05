#!/system/bin/sh
# Trusted Linux installer orchestration of original PackageInstaller sessions.
# No boot/property mutation, API replacement, permission or signature override.
set -eu
set -o pipefail
/system/bin/printf 'native_cli_PATH=%s\n' "$PATH"
apk_path=/data/local/tmp/markor.apk
apk_bytes=$(/system/bin/stat -c %s "$apk_path")
# Explicit trusted installer target; original PMS must discover/validate the
# actual APK. Old payloads without this input keep their pinned Markor route.
target_package=net.gsantner.markor
if [ -f /data/local/tmp/archtv-mc1/archtv-install-package ]; then
    IFS= read -r target_package < /data/local/tmp/archtv-mc1/archtv-install-package
fi
case "$target_package" in ''|*[!a-zA-Z0-9_.]*) exit 1;; esac

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

# Optional controlled media input goes through the original provider API.
# No direct /data/media writes, fabricated inventory or URI. Original content
# catches provider errors, so every effect is independently queried/read back.
media_source=/data/local/tmp/archtv-mc1/archtv-media-input.mp4
if [ -f "$media_source" ]; then
    [ "$target_package" = org.videolan.vlc ] || exit 1
    IFS= read -r media_name < /data/local/tmp/archtv-mc1/archtv-media-test-name
    case "$media_name" in
        archtv-test-????????.mp4)
            media_collection=content://media/external_primary/video/media
            media_mime=video/mp4
            media_relative_path=Movies/ ;;
        archtv-test-????????.m4a)
            media_collection=content://media/external_primary/audio/media
            media_mime=audio/mp4
            media_relative_path=Music/ ;;
        *) exit 1;;
    esac
    case "$media_name" in *[!a-zA-Z0-9_.-]*) exit 1;; esac
    media_where="_display_name='$media_name' AND relative_path='$media_relative_path'"
    /system/bin/content query --user 0 --uri "$media_collection" --projection _id --where "$media_where" --extra 'android\:query-arg-match-pending:i:1' > /data/local/tmp/archtv-mc1/media-before.txt 2>/data/local/tmp/archtv-mc1/media-query-error.txt
    media_before=$(/system/bin/cat /data/local/tmp/archtv-mc1/media-before.txt)
    if [ "$media_before" = 'No result found.' ]; then
        /system/bin/content insert --user 0 --uri "$media_collection" --bind "_display_name:s:$media_name" --bind "mime_type:s:$media_mime" --bind "relative_path:s:$media_relative_path" --bind is_pending:i:1 > /data/local/tmp/archtv-mc1/media-insert.txt 2>&1
    fi
    /system/bin/content query --user 0 --uri "$media_collection" --projection _id --where "$media_where" --extra 'android\:query-arg-match-pending:i:1' > /data/local/tmp/archtv-mc1/media-id.txt 2>/data/local/tmp/archtv-mc1/media-query-error.txt
    [ "$(/system/bin/wc -l < /data/local/tmp/archtv-mc1/media-id.txt)" -eq 1 ]
    /system/bin/grep -Eq '^Row: 0 _id=[0-9]+$' /data/local/tmp/archtv-mc1/media-id.txt
    media_row=$(/system/bin/cat /data/local/tmp/archtv-mc1/media-id.txt)
    media_id=${media_row##*=}
    media_uri=$media_collection/$media_id
    /system/bin/printf '%s\n' "$media_uri" > /data/local/tmp/archtv-mc1/media-uri.txt
    /system/bin/cat "$media_source" | /system/bin/content write --user 0 --uri "$media_uri" > /data/local/tmp/archtv-mc1/media-write.txt 2>&1
    /system/bin/content read --user 0 --uri "$media_uri" > /data/local/tmp/archtv-mc1/media-readback.mp4 2>/data/local/tmp/archtv-mc1/media-read-error.txt
    media_expected=$(/system/bin/sha256sum "$media_source")
    media_actual=$(/system/bin/sha256sum /data/local/tmp/archtv-mc1/media-readback.mp4)
    [ "${media_expected%% *}" = "${media_actual%% *}" ]
    [ "$(/system/bin/stat -c %s "$media_source")" -eq "$(/system/bin/stat -c %s /data/local/tmp/archtv-mc1/media-readback.mp4)" ]
    /system/bin/printf 'SOURCE %s\nREADBACK %s\n' "$media_expected" "$media_actual" > /data/local/tmp/archtv-mc1/media-bytes.txt
    /system/bin/content update --user 0 --uri "$media_uri" --bind is_pending:i:0 > /data/local/tmp/archtv-mc1/media-publish.txt 2>&1
    /system/bin/content query --user 0 --uri "$media_uri" --projection is_pending > /data/local/tmp/archtv-mc1/media-published.txt 2>/data/local/tmp/archtv-mc1/media-query-error.txt
    /system/bin/grep -qx 'Row: 0 is_pending=0' /data/local/tmp/archtv-mc1/media-published.txt
fi

# Actual original PMS state before install/update; no package state seeded.
/system/bin/cmd package path --user 0 $target_package > /data/local/tmp/archtv-mc1/markor-preinstall-path.txt 2>&1 || :
/system/bin/dumpsys package $target_package > /data/local/tmp/archtv-mc1/markor-preinstall-dump.txt 2>&1
# Kernel-derived labels from original Android ps under its original shell role.
# Diagnostic status is retained; this does not override the external SID gate.
ps_status=0
/system/bin/ps -A -o PID,LABEL,NAME > /data/local/tmp/archtv-mc1/android-ps-before.txt 2>/data/local/tmp/archtv-mc1/android-ps-error.txt || ps_status=$?
/system/bin/printf 'ps_before_exit=%s\n' "$ps_status" > /data/local/tmp/archtv-mc1/android-ps-status.txt
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
ps_status=0
/system/bin/ps -A -o PID,LABEL,NAME > /data/local/tmp/archtv-mc1/android-ps-postinstall.txt 2>/data/local/tmp/archtv-mc1/android-ps-error.txt || ps_status=$?
/system/bin/printf 'ps_postinstall_exit=%s\n' "$ps_status" >> /data/local/tmp/archtv-mc1/android-ps-status.txt
# Preserve the original PMS readback before user-start can block or the cohort stops.
/system/bin/cmd package path --user 0 $target_package > /data/local/tmp/archtv-mc1/markor-postcommit-path.txt
/system/bin/dumpsys package $target_package > /data/local/tmp/archtv-mc1/markor-postcommit-dump.txt
# Real original service-manager/PMS reads required by the functional verifier.
# Preserve the commands' output/status; never write an expected result string.
/system/bin/service check package > /data/local/tmp/archtv-mc1/package-query.txt
/system/bin/cmd package list packages --user 0 > /data/local/tmp/archtv-mc1/package-list.txt
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
/system/bin/stat -c '%n|inode=%i|uid=%u|gid=%g|mode=%a' /data/user/0/$target_package /data/user_de/0/$target_package > /data/local/tmp/archtv-mc1/markor-app-data.txt 2>&1 || app_data_status=$?
/system/bin/printf 'shell_private_data_stat exit=%s NOT_APP_DATA_ACCEPTANCE\n' "$app_data_status" >> /data/local/tmp/archtv-mc1/markor-app-data.txt
# Observe HOME candidates; explicit Markor launch does not require shell to
# disable a protected platform component. Actual256 rejected that operation.
# This does not establish the final Linux-only desktop/product profile.
/system/bin/cmd package query-activities --brief --user 0 -a android.intent.action.MAIN -c android.intent.category.HOME > /data/local/tmp/archtv-mc1/markor-home-after.txt
resolved=$(/system/bin/cmd package resolve-activity --brief --user 0 -a android.intent.action.MAIN -c android.intent.category.LAUNCHER $target_package)
/system/bin/printf '%s\n' "$resolved" > /data/local/tmp/archtv-mc1/markor-resolve.txt
component=$(/system/bin/printf '%s\n' "$resolved" | /system/bin/tail -n 1)
case "$component" in "$target_package"/*) ;; *) exit 1;; esac
# Local-media experiments use VLC's declared VIEW contract, resolved by
# original PMS. URI access is granted by original AMS; never synthesize a URI
# or bypass provider permission checks. Actual playback still needs evidence.
if [ -n "${media_uri:-}" ]; then
    media_resolved=$(/system/bin/cmd package resolve-activity --brief --user 0 -a android.intent.action.VIEW -c android.intent.category.DEFAULT -d "$media_uri" -t "$media_mime" -p "$target_package")
    /system/bin/printf '%s\n' "$media_resolved" > /data/local/tmp/archtv-mc1/media-resolve.txt
    media_component=$(/system/bin/printf '%s\n' "$media_resolved" | /system/bin/tail -n 1)
    case "$media_component" in "$target_package"/*) ;; *) exit 1;; esac
    /system/bin/cmd activity start-activity -W --user 0 --grant-read-uri-permission -a android.intent.action.VIEW -d "$media_uri" -t "$media_mime" -n "$media_component" > /data/local/tmp/archtv-mc1/media-launch.txt 2>&1
    # One original launch per audio experiment. Actual317's MAIN followed by
    # immediate VIEW overlapped MediaParsingService foreground start/stop/restart.
    # Preserve the real command output for the generic observer as an exact
    # alias, not a second launch or a manufactured readiness response.
    /system/bin/cp /data/local/tmp/archtv-mc1/media-launch.txt /data/local/tmp/archtv-mc1/markor-launch.txt
    # Measurement control after actual318: repeated AudioFlinger dumps take
    # service locks during the short source. Keep playback free of these dumps,
    # then query the original service once after 30 seconds. HAL position logs
    # remain unchanged. A late dump and counters still do not prove signal output.
    /system/bin/sleep 30
    dump_path=/data/local/tmp/archtv-mc1/audio-flinger-1.txt
    /system/bin/printf '\nSNAPSHOT 1 BEGIN late_after_seconds=30\n' > "$dump_path"
    dump_status=0
    /system/bin/dumpsys -t 1 media.audio_flinger >> "$dump_path" 2>&1 || dump_status=$?
    /system/bin/printf 'SNAPSHOT 1 END exit=%s\n' "$dump_status" >> "$dump_path"
    /system/bin/printf 'snapshot=1 late_after_seconds=30 exit=%s NOT_AUDIO_ACCEPTANCE\n' "$dump_status" > /data/local/tmp/archtv-mc1/audio-flinger-status.txt

else
    /system/bin/cmd activity start-activity -W --user 0 -n "$component" > /data/local/tmp/archtv-mc1/markor-launch.txt 2>&1
fi
ps_status=0
/system/bin/ps -A -o PID,LABEL,NAME > /data/local/tmp/archtv-mc1/android-ps-after.txt 2>/data/local/tmp/archtv-mc1/android-ps-error.txt || ps_status=$?
/system/bin/printf 'ps_after_exit=%s\n' "$ps_status" >> /data/local/tmp/archtv-mc1/android-ps-status.txt
app_pid=$(/system/bin/pidof "$target_package" || :)
case "$app_pid" in
    ''|*[!0-9]*) /system/bin/printf 'app_pid_unavailable\n' > /data/local/tmp/archtv-mc1/android-app-status.txt ;;
    *) /system/bin/cat /proc/$app_pid/status > /data/local/tmp/archtv-mc1/android-app-status.txt 2>&1 || : ;;
esac
# Actual APIs and pixels after launch, not an app-compatibility success marker.
CLASSPATH=/system/framework/sm.jar /system/bin/app_process64 /system/bin com.android.commands.sm.Sm list-volumes all > /data/local/tmp/archtv-mc1/markor-volumes.txt
/system/bin/cmd overlay list --user 0 > /data/local/tmp/archtv-mc1/markor-overlays.txt
/system/bin/cat /proc/self/mountinfo > /data/local/tmp/archtv-mc1/markor-mountinfo.txt
/system/bin/screencap -p /data/local/tmp/archtv-mc1/markor-sf.png

# Optional real-APK lifecycle experiment. Only the UI may create/write the note.
if [ -f /data/local/tmp/archtv-mc1/archtv-markor-workflow-token ]; then
    [ "$target_package" = net.gsantner.markor ] || exit 1
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
        for observed in "$note" "/mnt/user/0/emulated/0/Documents/markor/archtv-$token.md" "/mnt/user/0/emulated/Documents/markor/archtv-$token.md"; do
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
    before=$(/system/bin/pidof $target_package)
    case "$before" in ''|*[!0-9]*) exit 1;; esac
    /system/bin/printf 'before_pid=%s\n' "$before" > /data/local/tmp/archtv-mc1/markor-lifecycle.txt
    /system/bin/cmd activity force-stop --user 0 $target_package >> /data/local/tmp/archtv-mc1/markor-lifecycle.txt 2>&1
    n=0
    while [ -d /proc/$before ] && [ "$n" -lt 10 ]; do n=$((n+1)); /system/bin/sleep 1; done
    [ ! -d /proc/$before ]
    /system/bin/printf 'previous_process_absent=%s\n' "$before" >> /data/local/tmp/archtv-mc1/markor-lifecycle.txt
    /system/bin/cmd activity start-activity -W --user 0 -n "$component" > /data/local/tmp/archtv-mc1/markor-relaunch.txt 2>&1
    /system/bin/grep -qx 'Status: ok' /data/local/tmp/archtv-mc1/markor-relaunch.txt
    after=$(/system/bin/pidof $target_package)
    case "$after" in ''|*[!0-9]*) exit 1;; esac
    [ "$after" != "$before" ]
    /system/bin/printf 'after_pid=%s\n' "$after" >> /data/local/tmp/archtv-mc1/markor-lifecycle.txt
    /system/bin/sha256sum "$note" > /data/local/tmp/archtv-mc1/markor-note-after-relaunch.txt
fi

# Separate real Back/navigation experiment. Only physical UI input may move
# Markor out of the foreground. These original commands observe AMS and
# relaunch; they never finish/kill tasks, inject Back or manufacture readiness.
if [ -f /data/local/tmp/archtv-mc1/archtv-markor-normal-close-token ]; then
    [ "$target_package" = net.gsantner.markor ] || exit 1
    [ ! -f /data/local/tmp/archtv-mc1/archtv-markor-workflow-token ] || exit 1
    token=$(/system/bin/cat /data/local/tmp/archtv-mc1/archtv-markor-normal-close-token)
    case "$token" in ''|*[!0-9a-f]*) exit 1;; esac
    [ "${#token}" -eq 8 ] || exit 1
    budget=$(/system/bin/cat /data/local/tmp/archtv-mc1/archtv-markor-normal-close-budget)
    case "$budget" in ''|*[!0-9]*) exit 1;; esac
    [ "$budget" -ge 15 ] && [ "$budget" -le 585 ] || exit 1
    normal_out=/data/local/tmp/archtv-mc1
    note=/storage/emulated/0/Documents/markor/archtv-$token.md
    expected="archtv note $token"
    [ "$(/system/bin/stat -c %s "$note")" -eq "$((${#expected} + 1))" ] || exit 1
    [ "$(/system/bin/cat "$note")" = "$expected" ] || exit 1
    /system/bin/cat "$note" > "$normal_out/markor-normal-note-bytes.bin"
    /system/bin/sha256sum "$note" > "$normal_out/markor-normal-note-before.txt"
    normal_dump() {
        # Real354 exceeded the diagnostic3s bound while the APK remained visible.
        # Keep this finite and reject partial/error output below; a successful
        # longer diagnostic is not a latency or stability acceptance result.
        /system/bin/dumpsys -t 10 activity activities > "$1" 2> "$1.stderr"
        [ ! -s "$1.stderr" ] || return 1
        /system/bin/grep -qx 'ACTIVITY MANAGER ACTIVITIES (dumpsys activity activities)' "$1" || return 1
        if /system/bin/grep -Eq 'DUMP TIMEOUT|DUMP FAILED|Error dumping service|Permission Denial|Can.t find service' "$1"; then return 1; fi
    }
    normal_markor_resumed() {
        /system/bin/grep -Eq '^  ResumedActivity: ActivityRecord\{[^}]* u0 net[.]gsantner[.]markor/' "$1"
    }
    normal_dump "$normal_out/markor-normal-activities-before.txt"
    normal_markor_resumed "$normal_out/markor-normal-activities-before.txt" || exit 1
    /system/bin/dumpsys -t 10 activity processes > "$normal_out/markor-normal-processes-before.txt"
    n=0
    while [ "$n" -lt "$budget" ]; do
        normal_dump "$normal_out/markor-normal-activities-last.txt"
        if ! normal_markor_resumed "$normal_out/markor-normal-activities-last.txt"; then break; fi
        n=$((n+2)); /system/bin/sleep 2
    done
    [ "$n" -lt "$budget" ] || exit 1
    /system/bin/cp "$normal_out/markor-normal-activities-last.txt" "$normal_out/markor-normal-activities-background.txt"
    /system/bin/dumpsys -t 10 activity processes > "$normal_out/markor-normal-processes-background.txt"
    # Android can retain a stopped task and process after normal Back. The
    # dumps, actual input and original lifecycle logs must distinguish this
    # from finish, crash or ANR; foreground absence alone is not app acceptance.
    /system/bin/printf 'MARKOR_NORMAL_TOP_RESUMED_ABSENT NOT_TASK_FINISH_OR_APK_ACCEPTANCE\n'
    /system/bin/sha256sum "$note" > "$normal_out/markor-normal-note-background.txt"
    /system/bin/cmp "$normal_out/markor-normal-note-before.txt" "$normal_out/markor-normal-note-background.txt"
    if [ -f /data/local/tmp/archtv-mc1/archtv-markor-home-launch ]; then
        # Observe only. The actual Home user action must request the original
        # gateway launch. Never substitute a CLI relaunch or write its result.
        [ "$(/system/bin/cat /data/local/tmp/archtv-mc1/archtv-markor-home-launch)" = 1 ] || exit 1
        n=0
        while [ "$n" -lt "$budget" ]; do
            normal_dump "$normal_out/markor-normal-activities-relaunched.txt"
            if normal_markor_resumed "$normal_out/markor-normal-activities-relaunched.txt"; then break; fi
            n=$((n+2)); /system/bin/sleep 2
        done
        [ "$n" -lt "$budget" ] || exit 1
    else
        /system/bin/sleep 3
        /system/bin/cmd activity start-activity -W --user 0 -n "$component" > "$normal_out/markor-normal-relaunch.txt" 2>&1
        /system/bin/grep -qx 'Status: ok' "$normal_out/markor-normal-relaunch.txt"
        normal_dump "$normal_out/markor-normal-activities-relaunched.txt"
    fi
    normal_markor_resumed "$normal_out/markor-normal-activities-relaunched.txt" || exit 1
    /system/bin/sha256sum "$note" > "$normal_out/markor-normal-note-relaunched.txt"
    /system/bin/cmp "$normal_out/markor-normal-note-before.txt" "$normal_out/markor-normal-note-relaunched.txt"
fi
