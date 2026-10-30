#!/usr/bin/env python3
"""Build the owned counter APK without Gradle or an Android runtime."""
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import tempfile
import zipfile

parser = argparse.ArgumentParser()
parser.add_argument('--tools', type=Path, required=True)
parser.add_argument('--output', type=Path, required=True)
parser.add_argument('--jdk', type=Path, default=Path('/usr/lib/jvm/java-17-openjdk'))
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
fixture = root/'fixtures/apk/counter'
manifest = json.loads((fixture/'toolchain.json').read_text())
for item in manifest['artifacts']:
    with (args.tools/item['file']).open('rb') as stream:
        if hashlib.file_digest(stream, 'sha256').hexdigest() != item['sha256']:
            raise SystemExit('Tool checksum mismatch: '+item['file'])
args.output.mkdir(parents=True, exist_ok=False)
out = args.output.resolve()
args.tools = args.tools.resolve()
def run(command):
    subprocess.run([str(part) for part in command], check=True)
with tempfile.TemporaryDirectory(prefix='archtv-apk-') as temporary:
    work = Path(temporary)
    aapt = work/'aapt2'
    with zipfile.ZipFile(args.tools/'aapt2.jar') as archive:
        aapt.write_bytes(archive.read('aapt2'))
    aapt.chmod(0o700)
    for name in ['generated', 'classes', 'dex']:
        (work/name).mkdir()
    run([aapt, 'compile', '--dir', fixture/'res', '-o', work/'compiled.zip'])
    run([aapt, 'link', '-I', args.tools/'android.jar', '--manifest', fixture/'AndroidManifest.xml',
         '--java', work/'generated', '-o', work/'resources.apk', work/'compiled.zip'])
    sources = sorted((fixture/'src').rglob('*.java'))+sorted((work/'generated').rglob('*.java'))
    run([args.jdk/'bin/javac', '-source', '8', '-target', '8', '-bootclasspath', args.tools/'android.jar',
         '-encoding', 'UTF-8', '-d', work/'classes', *sources])
    run([args.jdk/'bin/jar', 'cf', work/'classes.jar', '-C', work/'classes', '.'])
    run([args.jdk/'bin/java', '-cp', args.tools/'r8.jar', 'com.android.tools.r8.D8', '--release',
         '--min-api', '21', '--lib', args.tools/'android.jar', '--output', work/'dex', work/'classes.jar'])
    with zipfile.ZipFile(work/'resources.apk') as resources, zipfile.ZipFile(out/'counter-unsigned.apk', 'w') as apk:
        entries = {name:resources.read(name) for name in resources.namelist() if not name.endswith('/')}
        entries.update({path.name:path.read_bytes() for path in (work/'dex').glob('*.dex')})
        for name, data in sorted(entries.items()):
            info = zipfile.ZipInfo(name, date_time=(2020, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            apk.writestr(info, data)
    key = args.tools/'counter-fixture.p12'
    if not key.exists():
        run([args.jdk/'bin/keytool', '-genkeypair', '-noprompt', '-alias', 'archtv-fixture', '-keyalg', 'RSA',
             '-keysize', '2048', '-storetype', 'PKCS12', '-keystore', key, '-storepass', 'archtv-fixture',
             '-keypass', 'archtv-fixture', '-dname', 'CN=ArchTV APK Fixture', '-validity', '3650'])
        key.chmod(0o600)
    shutil.copyfile(out/'counter-unsigned.apk', out/'counter.apk')
    run([args.jdk/'bin/jarsigner', '-keystore', key, '-storepass', 'archtv-fixture',
         '-sigalg', 'SHA256withRSA', '-digestalg', 'SHA-256', out/'counter.apk', 'archtv-fixture'])
    run([args.jdk/'bin/jarsigner', '-verify', out/'counter.apk'])
    with (out/'manifest.txt').open('w') as stream:
        subprocess.run([str(aapt), 'dump', 'badging', str(out/'counter.apk')], stdout=stream, check=True)
    run(['python', root/'tools/apk/apk_inventory.py', out/'counter.apk', out/'inventory.json'])
source_hashes = {str(path.relative_to(fixture)):hashlib.sha256(path.read_bytes()).hexdigest()
                 for path in sorted(fixture.rglob('*')) if path.is_file()}
artifacts = {path.name:hashlib.sha256(path.read_bytes()).hexdigest()
             for path in out.glob('*.apk')}
(out/'provenance.json').write_text(json.dumps({'source_sha256':source_hashes, 'toolchain':manifest,
    'apk_sha256':artifacts, 'scope':'Build, static inventory and JAR v1 test signing only. No APK runtime execution; no APK v2/v3 verifier or binary reproducibility claim.'}, indent=2)+'\n')
print(out/'counter.apk')
