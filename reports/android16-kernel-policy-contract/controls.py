from pathlib import Path
import importlib.util
import json
import re
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('policy_builder', ROOT / 'tools/aosp/build_linux_policy.py')
builder = importlib.util.module_from_spec(spec)
spec.loader.exec_module(builder)
contract = json.loads((ROOT / 'runtime/aosp/android16-qpr2/policy/kernel-6.18.59-contract.json').read_text())
rows = []
for name in ('linux', 'aosp'):
    path = ROOT / 'dist/aosp16/kernel-selinux-contract-1' / (name + '-policy.cil')
    text = path.read_text()
    declarations = '\n'.join(line for line in text.splitlines() if re.match(r'^\((class|common|classcommon) ', line))
    classes = builder.classes(builder.forms(declarations))
    if len(classes) != len(re.findall(r'^\(class ', text, re.M)):
        raise RuntimeError('Incomplete exported class inventory')
    orders = re.findall(r'^\(classorder \(([^()]*)\)\)$', text, re.M)
    if len(orders) != 1:
        raise RuntimeError('Expected one complete exported class order')
    try:
        audit = builder.audit_kernel_contract(classes, orders[0].split(), contract)
        if name != 'linux':
            raise RuntimeError('Original AOSP missing permissions went undetected')
        rows.append({'policy': name, 'status': 'names_present', 'audit': audit})
    except ValueError as error:
        if name != 'aosp' or 'watch_mountns' not in str(error) or 'allowed' not in str(error):
            raise
        rows.append({'policy': name, 'status': 'names_missing', 'error': str(error)})
with tempfile.TemporaryDirectory(prefix='archtv-kernel-contract-') as tmp:
    tmp = Path(tmp)
    profile = json.loads((ROOT / 'runtime/aosp/android16-qpr2/policy/build-profile.json').read_text())
    changed = tmp / 'contract.json'
    changed.write_text('{}\n')
    profile['kernel_contract']['path'] = str(changed)
    profile_path = tmp / 'profile.json'
    profile_path.write_text(json.dumps(profile))
    output = tmp / 'output'
    command = ['python', str(ROOT / 'tools/aosp/build_linux_policy.py'), '--profile', str(profile_path), '--output', str(output)]
    result = subprocess.run(command, capture_output=True, text=True, timeout=20)
    if result.returncode != 2 or 'Kernel contract hash mismatch' not in result.stderr or output.exists():
        raise RuntimeError('Contract drift was not refused before output')
    rows.append({'case': 'kernel_contract_drift', 'argv': command, 'exit_code': result.returncode,
                 'stderr': result.stderr, 'output_created': output.exists()})
Path(__file__).with_name('controls.json').write_text(json.dumps({
    'scope': 'Real original binary-export class inventories/order and CLI drift control, not kernel mapping execution',
    'results': rows}, indent=2) + '\n')
print('Original Linux accepted; original AOSP missing names detected; contract drift refused')
