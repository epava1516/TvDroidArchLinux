#!/usr/bin/env python3
"""Reuse the checked filesystem/EA packager for one original APEX cohort."""
from pathlib import Path
import sys,subprocess,json
repo=Path(__file__).resolve().parents[2];out=(repo/sys.argv[1]).resolve()
assert out.is_relative_to(repo/'dist/aosp16') and (out/'artifacts.json').is_file() and not (out/'payload.json').exists()
text=(repo/'reports/android16-hwmanager-cohort/build-payload-descriptor.py').read_text()
text=text.replace("out=r/'dist/aosp16/hwmanager-cohort-4'",'out=Path('+repr(str(out))+')')
expected=out/'apex-expected.json'
expected.write_text(json.dumps(json.loads((repo/'reports/android16-apex-bootstrap/complete-inputs.json').read_text())['modules'],indent=2)+'\n')
text=text.replace("image=out/'payload-2.ext4'", "record('/apex-expected.json',out/'apex-expected.json','u:object_r:vendor_configs_file:s0',0o600)\nimage=out/'payload-2.ext4'")
text=text.replace("(d/'payload-descriptor.json')","(out/'payload.json')")
recipe=out/'build-payload.py';recipe.write_text(text);subprocess.run([sys.executable,str(recipe)],check=True)
