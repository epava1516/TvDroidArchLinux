#!/usr/bin/env python3
"""Build the pinned experimental Linux/AOSP policy; never install or load it."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import resource
import signal
import subprocess
import time


ROOT = Path(__file__).resolve().parents[2]
TOKENS = re.compile(r'"(?:\\.|[^"\\])*"|;[^\n]*|[()]')
GLOBAL = {"sensitivity", "category", "sid", "sidorder", "handleunknown", "mls", "policycap"}
CLASS_DECLS = {"class", "common", "classcommon", "classorder"}


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2) + "\n")


def forms(text):
    """Preserve statement bytes; this builder accepts only hash-pinned inputs."""
    depth, start, result = 0, None, []
    for match in TOKENS.finditer(text):
        if match[0] == "(":
            if depth == 0:
                start = match.start()
            depth += 1
        elif match[0] == ")":
            depth -= 1
            if depth < 0:
                raise ValueError("Unbalanced CIL")
            if depth == 0:
                result.append(text[start:match.end()])
    if depth:
        raise ValueError("Unbalanced CIL")
    return result


def keyword(form):
    return re.match(r"\(\s*([^\s()]+)", form)[1]


def classes(statements):
    declared, common, inherited = {}, {}, []
    for form in statements:
        key = keyword(form)
        if key in ("class", "common"):
            match = re.fullmatch(r"\((?:class|common)\s+(\S+)\s+\(([^()]*)\)\)", form)
            if not match:
                raise ValueError("Unsupported class declaration")
            target = declared if key == "class" else common
            if match[1] in target:
                raise ValueError("Duplicate class/common declaration")
            target[match[1]] = match[2].split()
        elif key == "classcommon":
            match = re.fullmatch(r"\(classcommon\s+(\S+)\s+(\S+)\)", form)
            if not match:
                raise ValueError("Unsupported classcommon")
            inherited.append((match[1], match[2]))
    for name, parent in inherited:
        declared[name] = common[parent] + declared[name]
    return declared


def resource_key(form):
    key = keyword(form)
    if key == "genfscon":
        match = re.match(r'\(genfscon\s+(\S+)\s+("(?:\\.|[^"\\])*"|\S+)', form)
        if not match:
            raise ValueError("Unsupported genfscon")
        return key, match[1], match[2]
    if key == "fsuse":
        match = re.match(r"\(fsuse\s+(\S+)\s+(\S+)", form)
        if not match:
            raise ValueError("Unsupported fsuse")
        return key, match[2]
    return None


def compose(source, class_order):
    """The tested sparse-universe algorithm, with explicit Linux global labels."""
    inventories = {name: classes(value) for name, value in source.items()}
    union = {}
    for name, permissions in inventories["aosp"].items():
        union[name] = permissions + [p for p in inventories["linux"].get(name, []) if p not in permissions]
    union.update({k: v for k, v in inventories["linux"].items() if k not in union})
    if len(class_order) != len(set(class_order)) or set(class_order) != set(union):
        raise ValueError("Pinned class order does not cover the complete union")
    if any(len(value) > 32 or len(value) != len(set(value)) for value in union.values()):
        raise ValueError("Invalid class permission union")
    owned = {resource_key(f): f for f in source["linux"] if resource_key(f) is not None}
    audit = {"type_counts": {}, "wrapped_expressions": {}, "assertion_counts": {},
             "replaced_resource_labels": [], "replaced_sid_contexts": [], "deduplicated_globals": []}
    transformed = {}
    for name, statements in source.items():
        if any("archtv_original_universe" in form for form in statements):
            raise ValueError("Reserved universe name already present")
        types = [re.fullmatch(r"\(type\s+(\S+)\)", f)[1] for f in statements if keyword(f) == "type"]
        if not types or len(types) != len(set(types)):
            raise ValueError("Invalid concrete type inventory")
        audit["type_counts"][name] = len(types)
        audit["wrapped_expressions"][name] = 0
        audit["assertion_counts"][name] = sum(keyword(f) in ("neverallow", "neverallowx") for f in statements)
        result = []
        for form in statements:
            if keyword(form) == "typeattributeset" and re.search(r"\((?:not|all)(?:\s|\))", form):
                match = re.fullmatch(r"\(typeattributeset\s+(\S+)\s+(.+)\)", form, re.S)
                if not match:
                    raise ValueError("Unsupported type attribute expression")
                form = "(typeattributeset " + match[1] + " (and (archtv_original_universe) " + match[2] + "))"
                audit["wrapped_expressions"][name] += 1
            result.append(form)
        result += ["(typeattribute archtv_original_universe)",
                   "(typeattributeset archtv_original_universe (" + " ".join(types) + "))"]
        transformed[name] = result
    globals_ = ["(class " + name + " (" + " ".join(union[name]) + "))" for name in class_order]
    globals_.append("(classorder (" + " ".join(class_order) + "))")
    local, seen = [], set()
    for name, statements in transformed.items():
        for form in statements:
            key, rk = keyword(form), resource_key(form)
            if name == "aosp" and rk is not None and rk in owned:
                audit["replaced_resource_labels"].append({"key": rk, "original": form, "linux_owner": owned[rk]})
                continue
            if name == "aosp" and key == "sidcontext":
                audit["replaced_sid_contexts"].append(form)
                continue
            if key in CLASS_DECLS:
                continue
            if key in GLOBAL:
                if form in seen:
                    audit["deduplicated_globals"].append(form)
                    continue
                globals_.append(form)
                seen.add(form)
            elif name == "aosp":
                globals_.append(form)
            else:
                local.append(form)
    audit["class_count"] = len(union)
    return "\n".join(globals_) + "\n(block linux\n" + "\n".join(local) + "\n)\n", audit


def compile_policy(tool, output, modules, wall_seconds, cpu_seconds):
    command = ["prlimit", "--as=2147483648", f"--cpu={cpu_seconds}", "--", str(tool),
               "-m", "-M", "true", "-G", "-c", "30", "-o", str(output / "policy.bin"),
               "-f", str(output / "file_contexts"), str(output / "combined.cil")] + list(map(str, modules))
    start = time.monotonic()
    with (output / "stdout.log").open("wb") as stdout, (output / "stderr.log").open("wb") as stderr:
        child = subprocess.Popen(command, stdout=stdout, stderr=stderr, start_new_session=True)
        write_json(output / "process.json", {"pid": child.pid, "argv": command, "status": "running"})
        try:
            code = child.wait(timeout=wall_seconds)
        except (subprocess.TimeoutExpired, KeyboardInterrupt) as error:
            os.killpg(child.pid, signal.SIGKILL)
            child.wait()
            code = 124 if isinstance(error, subprocess.TimeoutExpired) else 130
    usage = resource.getrusage(resource.RUSAGE_CHILDREN)
    record = {"argv": command, "exit_code": code, "elapsed_seconds": time.monotonic() - start,
              "cpu_user_seconds": usage.ru_utime, "cpu_system_seconds": usage.ru_stime,
              "max_rss_kib": usage.ru_maxrss, "neverallow_disabled": False,
              "limits": {"cpu_seconds_requested": cpu_seconds, "wall_seconds": wall_seconds,
                         "address_space_bytes": 2147483648}}
    write_json(output / "compiler.json", record)
    write_json(output / "process.json", {"pid": child.pid, "status": "terminal", "exit_code": code})
    return code


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", required=True, type=Path, help="New directory; existing output is never overwritten")
    parser.add_argument("--profile", type=Path, default=ROOT / "runtime/aosp/android16-qpr2/policy/build-profile.json")
    parser.add_argument("--aosp-cil", type=Path, default=ROOT / "dist/aosp16/factory-inputs-3/root/system/etc/selinux/plat_sepolicy.cil")
    parser.add_argument("--linux-cil", type=Path, default=ROOT / "dist/aosp16/refpolicy-baseline-1/source/policy.cil")
    parser.add_argument("--secilc", type=Path, default=ROOT / "dist/aosp16/selinux-tools-host-4/source/secilc/secilc")
    parser.add_argument("--compile", action="store_true", help="Run original host compiler; never installs or loads policy")
    parser.add_argument("--wall-seconds", type=int, default=240)
    parser.add_argument("--cpu-seconds", type=int, default=180)
    args = parser.parse_args()
    output = args.output.resolve()
    try:
        if output.exists():
            raise ValueError("Output already exists; preserve it and choose a new directory")
        profile = json.loads(args.profile.read_text())
        if (profile["schema"], profile["contract"], profile["global_label_owner"], profile["binary_policy_version"]) != (1, "A16-QPR2-1", "linux", 30):
            raise ValueError("Unsupported policy profile")
        if args.wall_seconds <= 0 or args.cpu_seconds <= 0:
            raise ValueError("Compiler budgets must be positive")
        inputs = {"aosp": args.aosp_cil.resolve(), "linux": args.linux_cil.resolve()}
        input_bytes = {k: p.read_bytes() for k, p in inputs.items()}
        hashes = {k: hashlib.sha256(data).hexdigest() for k, data in input_bytes.items()}
        if hashes != profile["input_sha256"]:
            raise ValueError("Input hash mismatch: no output written")
        if args.compile and digest(args.secilc) != profile["secilc_sha256"]:
            raise ValueError("Compiler hash mismatch: no output written")
        modules = [(ROOT / name).resolve() for name in profile["modules"]]
        module_bytes = {p: p.read_bytes() for p in modules}
        combined, audit = compose({k: forms(data.decode()) for k, data in input_bytes.items()}, profile["class_order"])
        output.mkdir(parents=True, exist_ok=False)
        (output / "combined.cil").write_text(combined)
        local_modules = []
        for index, (path, data) in enumerate(module_bytes.items()):
            dest = output / f"adapter-{index}-{path.name}"
            dest.write_bytes(data)
            local_modules.append(dest)
        write_json(output / "composition.json", audit)
        manifest = {"schema": 1, "contract": profile["contract"], "status": "generated",
                    "scope": "Experimental artifact only; no installation/load/live policy/service/APK approval",
                    "profile_sha256": digest(args.profile), "input_sha256": hashes,
                    "input_paths": {k: str(p) for k, p in inputs.items()},
                    "modules": {str(p.relative_to(ROOT)): hashlib.sha256(data).hexdigest() for p, data in module_bytes.items()},
                    "combined_cil_sha256": digest(output / "combined.cil"), "limitations": profile["limitations"]}
        write_json(output / "artifact.json", manifest)
        if args.compile:
            code = compile_policy(args.secilc.resolve(), output, local_modules, args.wall_seconds, args.cpu_seconds)
            manifest["status"] = "compiled_offline" if code == 0 else "compiler_failed"
            manifest["compiler_sha256"] = digest(args.secilc)
            manifest["compiler_exit_code"] = code
            if code == 0:
                manifest["binary_sha256"] = digest(output / "policy.bin")
            write_json(output / "artifact.json", manifest)
            if code:
                print(f"Compiler did not pass: {code}; evidence: {output}")
                return 1
        print(f"{manifest['status']}: {output}")
        return 0
    except (ValueError, OSError, KeyError) as error:
        parser.exit(2, f"{error}\n")


if __name__ == "__main__":
    raise SystemExit(main())
