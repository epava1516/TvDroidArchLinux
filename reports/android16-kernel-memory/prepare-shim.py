#!/usr/bin/env python3
"""Apply the original ACK C shim to an extracted, verified Linux 6.18.59 tree.

No build, install, security change or reboot. Original shim source stays intact.
"""
from pathlib import Path
import argparse, difflib, hashlib, json, re

parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--linux-source', type=Path, required=True)
parser.add_argument('--ack-source', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
linux = args.linux_source.resolve()
ack = args.ack_source.resolve()
out = args.output.resolve()
assert linux.name == 'linux-6.18.59' and (linux / 'Makefile').is_file()
verification = json.loads((linux.parents[1] / 'verified-source.json').read_text())
assert verification['developer_signature_valid'] and verification['version'] == '6.18.59'
expected = {
    'mm/memfd-ashmem-shim.c': 'c40e9d5a3feeea31fc2a21a31591803909c1599a9f18fa18d8b9536e8bfebad0',
    'mm/memfd-ashmem-shim.h': '493f414cf379fb78167d6ffea191511c6391e57bb2232ffa7b2c14e0a050de66',
    'mm/memfd-ashmem-shim-internal.h': '83ff01d33eca8ec64a9df8b905da18261f0cc51231f7ebfdd26b3e876a5a2850',
}
original = {}
modified = {}
for logical, digest in expected.items():
    assert not (linux / logical).exists(), ('Preserve existing candidate', logical)
    data = (ack / logical.replace('/', '__')).read_bytes()
    assert hashlib.sha256(data).hexdigest() == digest, logical
    original[logical] = ''
    modified[logical] = data.decode()
for logical in ['mm/shmem.c', 'mm/Makefile', 'mm/Kconfig']:
    original[logical] = (linux / logical).read_text()
    assert 'MEMFD_ASHMEM_SHIM' not in original[logical]
    modified[logical] = original[logical]
marker = '#include "internal.h"\n'
assert modified['mm/shmem.c'].count(marker) == 1
modified['mm/shmem.c'] = modified['mm/shmem.c'].replace(marker, marker +
    '\n#ifdef CONFIG_MEMFD_ASHMEM_SHIM\n#include "memfd-ashmem-shim.h"\n#endif\n')
marker = '\t.fallocate\t= shmem_fallocate,\n#endif\n};'
assert modified['mm/shmem.c'].count(marker) == 1
modified['mm/shmem.c'] = modified['mm/shmem.c'].replace(marker,
    '\t.fallocate\t= shmem_fallocate,\n#endif\n#ifdef CONFIG_MEMFD_ASHMEM_SHIM\n'
    '\t.unlocked_ioctl = memfd_ashmem_shim_ioctl,\n#ifdef CONFIG_COMPAT\n'
    '\t.compat_ioctl = memfd_ashmem_shim_compat_ioctl,\n#endif\n#endif\n};')
marker = 'obj-$(CONFIG_MEMFD_CREATE) += memfd.o\n'
assert modified['mm/Makefile'].count(marker) == 1
modified['mm/Makefile'] = modified['mm/Makefile'].replace(marker,
    marker + 'obj-$(CONFIG_MEMFD_ASHMEM_SHIM) += memfd-ashmem-shim.o\n')
config = re.search(r'(?ms)^config MEMFD_ASHMEM_SHIM\n.*?(?=^source |^config |\Z)',
                   (ack / 'mm__Kconfig').read_text()).group(0)
marker = 'config SECRETMEM\n'
assert modified['mm/Kconfig'].count(marker) == 1
modified['mm/Kconfig'] = modified['mm/Kconfig'].replace(marker, config + marker)
out.mkdir(parents=True, exist_ok=False)
patch = ''
records = {}
for logical, text in modified.items():
    patch += ''.join(difflib.unified_diff(original[logical].splitlines(True),
        text.splitlines(True), fromfile='a/'+logical if original[logical] else '/dev/null',
        tofile='b/'+logical, n=0))
    records[logical] = {
        'before_sha256': hashlib.sha256(original[logical].encode()).hexdigest() if original[logical] else None,
        'after_sha256': hashlib.sha256(text.encode()).hexdigest(),
        'original_ACK_body_unchanged': logical in expected,
    }
(out / 'linux-6.18.59-ack-ashmem.patch').write_text(patch)
for logical, text in modified.items():
    (linux / logical).write_text(text)
(out / 'preparation.json').write_text(json.dumps({
    'scope': 'Offline source adaptation only; not a compiled/installed/booted or accepted kernel',
    'linux_source': str(linux), 'linux_verification': verification,
    'ack_commit': '18290a0bb038a4db4d097f66a9c6bd6a14e1f320',
    'ack_origin': 'https://android.googlesource.com/kernel/common/',
    'patch_sha256': hashlib.sha256(patch.encode()).hexdigest(), 'files': records,
    'limits': ['Original GPL-2.0 shim/headers preserved unchanged; only Kbuild/Kconfig/shmem wiring adapted.',
               'Upstream read/exec removal and purge/unpin limitations remain; not full ashmem ABI/security acceptance.',
               'No legacy /dev/ashmem character device or proven compat32/ARM support.',
               'Require original memfd guard and shared-memory positive/negative runtime tests before admission.'],
}, indent=2)+'\n')
print(out / 'preparation.json')
