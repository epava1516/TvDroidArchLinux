#!/usr/bin/env python3
"""Bounded physical UI regression for the already inspected Markor348 note.

Uses the existing owned uinput sender and actual DRM captures. Never produces
runtime readiness, original-service results, permissions or note contents.
It neither consumes the run result nor sends a continuation.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time
import uuid

MAIN = "f5595d6ee79245d7b140334ec909efaae6c26f58a0c44bdc1ed5a3875248cebc"
EDITOR = "1ac26935642068519eb91bbfe02fe574b93c1e6ede2c14207b0bec3462d2e0c6"
HOME = "e49fab04df879ef2a8cc1ed04b3ea47276ce59663b30766f58b26806ba96c88e"


def run(cp):
    cp = cp.resolve()
    before = json.loads((cp / "before-launch.json").read_text())
    run_id = before["id"]
    assert str(uuid.UUID(run_id)) == run_id
    assert cp.parent == Path("/home/tv/recuperacion-archtv")
    assert cp.name == run_id + "-markor-software-launch"
    binding = json.loads((cp / "owner-start-readback.json").read_text())
    # The privileged owner already verified the actual kernel boot. Revalidate
    # its unique live InvocationID below instead of requiring this unprivileged
    # observer to read a restricted proc sysctl on every frame.
    unit = "archtv-host-owner-" + run_id + ".service"
    assert binding["unit"] == unit and binding["InvocationID"]
    assert before["markor_normal_close_token"] == "348ace01"
    result = {"id": run_id, "steps": [], "scope":
              "Selected real physical UI regression only. No APK, service, MAC, "
              "performance or recovery acceptance; original guards are independent."}
    overall = time.monotonic() + 600
    command_path = cp / "input-commands.jsonl"
    assert not command_path.exists()
    commands = 0

    def save():
        path = cp / "native-ui-sequence.json"
        temporary = path.with_suffix(".tmp")
        with temporary.open("w") as stream:
            json.dump(result, stream, indent=2)
            stream.write("\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)

    def owner():
        actual = dict(line.split("=", 1) for line in subprocess.check_output(
            ["systemctl", "show", unit, "-p", "MainPID", "-p", "InvocationID",
             "-p", "ActiveState", "-p", "LoadState"], text=True).splitlines())
        if actual.get("MainPID", "0") == "0" or actual.get("ActiveState") != "active":
            raise RuntimeError("Bound owner no longer active: " + repr(actual))
        assert actual["InvocationID"] == binding["InvocationID"], "Different invocation"
        # This scoped cohort has only the owned Android display and Home.
        # The recovery owner can remain alive after that display has closed.
        compositor_log = cp / "compositor.log"
        if (compositor_log.exists()
                and "TV_APP_CLOSED_HOME" in compositor_log.read_text(errors="replace")):
            raise RuntimeError("Owned display ended; no further physical input")
        if time.monotonic() >= overall:
            raise TimeoutError("Bounded UI observation deadline, never restart owner")

    def read_json(path):
        try:
            return json.loads(path.read_text())
        except (FileNotFoundError, json.JSONDecodeError):
            # Existing capture/sender observations can be in the middle of a write.
            return None

    def frame(digest, after):
        while True:
            owner()
            rows = read_json(cp / "capture-samples.json")
            if rows:
                sample = rows[-1]
                path = Path(sample["path"])
                assert path.parent == cp and not path.is_symlink()
                if (sample["observed_monotonic"] > after
                        and path.name == "smithay-frame-" + digest + ".ppm"
                        and path.is_file()):
                    with path.open("rb") as stream:
                        actual = hashlib.file_digest(stream, "sha256").hexdigest()
                    if actual == digest:
                        result["steps"].append({"capture": sample, "sha256": digest})
                        save()
                        return sample
            time.sleep(0.2)

    def send(operation):
        nonlocal commands
        owner()
        commands += 1
        operation = dict(operation, id=commands)
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | os.O_NOFOLLOW
        fd = os.open(command_path, flags, 0o600)
        try:
            wire = (json.dumps(operation) + "\n").encode()
            assert os.write(fd, wire) == len(wire)
            os.fsync(fd)
        finally:
            os.close(fd)
        # Queue once; observation retries must never repeat physical commands.
        while True:
            owner()
            events = read_json(cp / "interaction-events.json")
            if events and len(events["commands"]) >= commands:
                observed = events["commands"][commands - 1]
                assert observed["command"] == operation
                result["steps"].append({"physical_command": observed})
                save()
                return observed["written_monotonic"]
            time.sleep(0.1)

    try:
        while True:
            owner()
            root = read_json(cp / "root-before.json")
            if root is not None:
                assert root["boot_id"] == before["boot_id"]
                break
            time.sleep(0.1)
        frame(MAIN, 0)
        frame(EDITOR, send({"op": "click", "position": [300, 410]}))
        frame(MAIN, send({"op": "keys", "value": ["back"]}))
        home = frame(HOME, send({"op": "keys", "value": ["back"]}))
        frame(MAIN, home["observed_monotonic"])
        frame(EDITOR, send({"op": "click", "position": [300, 410]}))
        # A second natural Home restart occurs while the original editor is
        # foreground. Challenge real key/pointer routing again after repaint.
        while True:
            owner()
            log = (cp / "compositor.log").read_text(errors="replace")
            if log.count("SHELL_SURFACE_READY") >= 3:
                restarted = time.monotonic()
                break
            time.sleep(0.2)
        frame(EDITOR, restarted)
        frame(MAIN, send({"op": "keys", "value": ["back"]}))
        frame(EDITOR, send({"op": "click", "position": [300, 410]}))
        result.update(status="six_physical_commands_and_expected_frames_observed",
                      command_count=commands)
        save()
    except BaseException as error:
        result.update(status="failed_observation_no_runtime_acceptance",
                      error=repr(error), command_count=commands)
        save()
        raise


if __name__ == "__main__":
    assert len(sys.argv) == 2
    run(Path(sys.argv[1]))
