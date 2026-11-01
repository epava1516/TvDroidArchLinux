#!/usr/bin/env python3
"""Build orchestration DEX and explicit diagnostic service RC; never execute Android."""
from pathlib import Path
import argparse, hashlib, json, subprocess, zipfile

ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--output', type=Path, required=True)
args = parser.parse_args()
out = args.output.resolve()
out.mkdir(parents=True, exist_ok=False)
classes = out / 'classes'
classes.mkdir()
dex = out / 'dex'
dex.mkdir()
source = ROOT / 'runtime/aosp/linux-services/org/archtv/aosplinux/SelectedServices.java'
commands = []
for stage in range(2):
    argv = ['javac', '--release', '8', '-d', str(classes), str(source), str(source.with_name('ServiceLauncher.java'))] if stage == 0 else ['java', '-cp', '/home/tv/.cache/archtv/apk-build-tools/r8.jar',
              'com.android.tools.r8.D8', '--min-api', '36', '--output', str(dex),
              *map(str, classes.rglob('*.class'))]
    result = subprocess.run(argv, capture_output=True, text=True, timeout=90)
    commands.append({'argv': argv, 'exit': result.returncode, 'stderr': result.stderr})
    (out / 'build.json').write_text(json.dumps({'commands': commands,
        'source_sha256': hashlib.sha256(source.read_bytes()).hexdigest(),
        'launcher_sha256': hashlib.sha256(source.with_name('ServiceLauncher.java').read_bytes()).hexdigest(),
        'scope': 'Orchestration build only; no service, display, APK or MAC acceptance'}, indent=2)+'\n')
    result.check_returncode()
jar = out / 'archtv-selected-services.jar'
with zipfile.ZipFile(jar, 'w', compression=zipfile.ZIP_STORED) as archive:
    archive.write(dex / 'classes.dex', 'classes.dex')
# Reuse the previously derived original GSI/APEX classpath, with every path
# present in the selected original filesystem. Do not invent boot class stubs.
profile = ROOT / 'dist/aosp16/property-profile-client-5/app/classpath'
original = ROOT / 'dist/aosp16/factory-inputs-3/root'
environment = {}
for line in profile.read_text().splitlines():
    export, name, value = line.split(' ', 2)
    assert export == 'export' and name in ['BOOTCLASSPATH', 'DEX2OATBOOTCLASSPATH',
        'SYSTEMSERVERCLASSPATH', 'STANDALONE_SYSTEMSERVER_JARS']
    for path in value.split(':'):
        assert path.startswith(('/apex/', '/system/')) and (original / path.lstrip('/')).is_file(), path
    environment[name] = value
# Keep the original complete system-server classpath as a classloader unit;
# only the explicitly selected service is started, never SystemServer.main.
environment.update({'ANDROID_ROOT': '/system', 'ANDROID_ASSETS': '/system/app',
    'ANDROID_DATA': '/data', 'ANDROID_ART_ROOT': '/apex/com.android.art',
    'ANDROID_I18N_ROOT': '/apex/com.android.i18n', 'ANDROID_TZDATA_ROOT': '/apex/com.android.tzdata',
    'CLASSPATH': '/vendor/framework/archtv-selected-services.jar'})
rc = ('service archtv-selected-services /system/bin/app_process64 '
      '-Xmx384m -Xnoimage-dex2oat /system/bin --application --nice-name=archtv-selected-services '
      'org.archtv.aosplinux.ServiceLauncher\n'
      '    user system\n    group system graphics\n    seclabel u:r:system_server:s0\n'
      '    capabilities SYS_NICE\n    disabled\n    oneshot\n')
rc += ''.join('    setenv '+name+' '+value+'\n' for name, value in environment.items())
(out / 'selected-services.rc').write_text(rc)
(out / 'artifacts.json').write_text(json.dumps({'jar_sha256': hashlib.sha256(jar.read_bytes()).hexdigest(),
    'rc_sha256': hashlib.sha256(rc.encode()).hexdigest(),
    'classpath_source': str(profile), 'classpath_sha256': hashlib.sha256(profile.read_bytes()).hexdigest(),
    'limits': 'Explicit diagnostic system UID/domain, not canonical zygote spawn or MAC acceptance; no full Android boot'}, indent=2)+'\n')
print(out)
