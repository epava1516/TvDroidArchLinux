#!/usr/bin/env python3
"""Run the pinned SwiftShader/SPIRV original host generators; no runtime."""
from pathlib import Path
import argparse
import hashlib
import json
import subprocess
import sys

SOURCE = Path('/home/tv/.cache/archtv/aosp16-qpr2/swiftshader-source-1')
REVISION = 'd70203d9df3c70c4fc63fb29325d24e9c12dc43f'


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', required=True, type=Path)
    args = parser.parse_args()
    out = args.output.resolve()
    out.mkdir(parents=True, exist_ok=False)
    assert subprocess.check_output(['git', '-C', str(SOURCE), 'rev-parse', 'HEAD'], text=True).strip() == REVISION
    spirv = SOURCE / 'third_party/SPIRV-Tools'
    headers = SOURCE / 'third_party/SPIRV-Headers/include/spirv'
    commands = []

    def run(argv):
        result = subprocess.run(list(map(str, argv)), capture_output=True, text=True, timeout=60)
        commands.append({'argv': list(map(str, argv)), 'exit': result.returncode,
                         'stdout': result.stdout, 'stderr': result.stderr})
        (out / 'generation.json').write_text(json.dumps({'revision': REVISION,
            'commands': commands, 'scope': 'Original host generators only; no native renderer or APK acceptance.'}, indent=2) + '\n')
        result.check_returncode()

    # Exact grammar/prefix mapping in the original Android.bp genrule.
    ext = [('debuginfo', ''), ('glsl.std.450', ''), ('nonsemantic.clspvreflection', ''),
           ('nonsemantic.shader.debuginfo.100', 'SHDEBUG100_'),
           ('nonsemantic.vkspreflection', ''), ('opencl.debuginfo.100', 'CLDEBUG100_'),
           ('opencl.std.100', ''), ('spv-amd-gcn-shader', ''), ('spv-amd-shader-ballot', ''),
           ('spv-amd-shader-explicit-vertex-parameter', ''), ('spv-amd-shader-trinary-minmax', '')]
    run([sys.executable, spirv / 'utils/ggt.py', '--spirv-core-grammar', headers / 'unified1/spirv.core.grammar.json',
         *[f'--extinst={prefix},{headers / "unified1" / ("extinst." + name + ".grammar.json")}' for name,prefix in ext],
         '--core-tables-body-output', out / 'core_tables_body.inc',
         '--core-tables-header-output', out / 'core_tables_header.inc'])
    run([sys.executable, spirv / 'utils/generate_registry_tables.py',
         '--xml=' + str(headers / 'spir-v.xml'), '--generator-output=' + str(out / 'generators.inc')])
    run([sys.executable, spirv / 'utils/update_build_version.py', spirv / 'CHANGES', out / 'build-version.inc'])
    run([sys.executable, SOURCE / 'src/commit_id.py', 'gen', out / 'commit.h'])
    (out / 'artifacts.json').write_text(json.dumps({p.name: hashlib.sha256(p.read_bytes()).hexdigest()
        for p in out.glob('*.inc')}, indent=2) + '\n')
    print('Original generators passed:', out)


if __name__ == '__main__':
    main()
