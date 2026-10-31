#!/usr/bin/env python3
"""Read-only inventory of native boot inputs; NOT an init/property implementation.

Never emits a runtime property file, derives a capability or starts Android.
Absolute symlinks are interpreted inside the supplied extracted filesystem.
"""
import argparse
import hashlib
import json
import os
from pathlib import Path, PurePosixPath


def inside(root, logical):
    pending = list(PurePosixPath(logical).parts[1:])
    parts = []
    links = 0
    while pending:
        component = pending.pop(0)
        if component in ("", "."):
            continue
        if component == "..":
            if not parts:
                raise ValueError("symlink escapes extracted root")
            parts.pop()
            continue
        candidate = root.joinpath(*parts, component)
        if candidate.is_symlink():
            links += 1
            if links > 40:
                raise ValueError("symlink cycle or excessive indirection")
            target = os.readlink(candidate)
            if target.startswith("/"):
                parts = []
            pending = list(PurePosixPath(target).parts)[int(target.startswith('/')):] + pending
        else:
            parts.append(component)
    return root.joinpath(*parts)


def inventory(root, logical, properties=False):
    path = inside(root, logical)
    result = {"logical_path": logical, "physical_relative_path": str(path.relative_to(root))}
    if not path.is_file():
        return {**result, "status": "absent"}
    data = path.read_bytes()
    result.update(status="present", sha256=hashlib.sha256(data).hexdigest(), bytes=len(data))
    if properties:
        entries = []
        unsupported = []
        for number, line in enumerate(data.decode().splitlines(), 1):
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            if '=' not in line or line.startswith('import '):
                unsupported.append({"line": number, "text": line})
                continue
            name, value = line.split('=', 1)
            entries.append({"name": name.strip(), "value": value.strip(), "line": number})
        result.update(entries=entries, unsupported_syntax=unsupported,
                      parsing_scope="Inventory only; original init parser/permissions/derivations not executed")
    return result


def audit(root):
    # Exact original PropertyLoadBootDefaults order. Legacy candidates are recorded,
    # not selected by an invented replacement for its SDK-dependent fallback.
    paths = ['/second_stage_resources/system/etc/ramdisk/build.prop', '/system/build.prop']
    for partition in ('system_ext', 'system_dlkm', 'vendor', 'vendor_dlkm',
                      'odm_dlkm', 'odm', 'product'):
        if partition == 'vendor':
            paths += ['/vendor/default.prop', '/vendor/build.prop']
        else:
            paths.append(f'/{partition}/etc/build.prop')
            if partition in ('system_ext', 'odm', 'product'):
                paths += [f'/{partition}/default.prop', f'/{partition}/build.prop']
    paths += ['/debug_ramdisk/props.debug', '/system/etc/ramdisk/build.prop', '/prop.default']
    props = [inventory(root, p, True) for p in paths]
    contexts = [inventory(root, f'/{part}/etc/selinux/{prefix}_property_contexts')
                for part, prefix in [('system', 'plat'), ('system_ext', 'system_ext'),
                                     ('vendor', 'vendor'), ('product', 'product'), ('odm', 'odm')]]
    return {'schema': 1, 'contract': 'A16-QPR2-1', 'properties': props, 'contexts': contexts,
            'runtime_properties_generated': False, 'original_init_executed': False,
            'limitations': ['Inventory, not loader equivalence or effective property values',
                           'No kernel/DT/bootconfig imports, derived defaults or live service',
                           'No ABI/API/ISA capability or security/certification acceptance',
                           'No signature or component source/binary equivalence validation']}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, required=True)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error('output already exists; preserve prior evidence')
    root = args.root.resolve(strict=True)
    result = audit(root)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open('x') as stream:
        json.dump(result, stream, indent=2)
        stream.write('\n')
    print(json.dumps({'present_property_files': sum(p['status'] == 'present' for p in result['properties']),
                      'present_context_files': sum(p['status'] == 'present' for p in result['contexts']),
                      'output': str(args.output)}))


if __name__ == '__main__':
    main()
