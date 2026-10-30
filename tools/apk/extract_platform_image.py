#!/usr/bin/env python3
"""Verify a pinned official archive and extract selected static research inputs.

Does not mount, boot or execute an Android image. SDK license/NOTICE remain
inputs for review, not a claim that the image may be redistributed in Arch TV.
"""
import argparse
import hashlib
import json
import shutil
import zipfile
from pathlib import Path


def digest(path, algorithm="sha256"):
    h = hashlib.new(algorithm)
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--archive", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    manifest = root / "runtime/aosp/platform-image.json"
    pinned = json.loads(manifest.read_text())
    archive = args.archive.resolve()
    if (archive.stat().st_size != pinned["bytes"]
            or digest(archive, "sha1") != pinned["published_sha1"]
            or digest(archive) != pinned["observed_sha256"]):
        raise SystemExit("Archive identity mismatch; nothing extracted")
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=False)
    selected = ["build.prop", "source.properties", "NOTICE.txt", "system.img"]
    extracted = {}
    with zipfile.ZipFile(archive) as source:
        for name in selected:
            member = "x86_64/" + name
            info = source.getinfo(member)
            if len([i for i in source.infolist() if i.filename == member]) != 1:
                raise SystemExit("Duplicate archive member: " + member)
            if info.file_size > 8 * 1024 ** 3:
                raise SystemExit("Unexpected input size: " + member)
            destination = output / name
            with source.open(info) as src, destination.open("xb") as dst:
                shutil.copyfileobj(src, dst, 1024 * 1024)
            if destination.stat().st_size != info.file_size:
                raise SystemExit("Extracted size mismatch: " + member)
            extracted[member] = {"bytes": info.file_size, "sha256": digest(destination)}
    result = {"archive_sha256": pinned["observed_sha256"],
              "manifest_sha256": digest(manifest), "extractor_sha256": digest(Path(__file__)),
              "files": extracted,
              "scope": "Selected static files only; ZIP CRC checked by zipfile. No mount, boot or APK execution. Output must be new; failed partial outputs are retained for diagnosis."}
    (output / "provenance.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
