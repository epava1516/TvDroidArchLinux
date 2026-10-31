# Prepare a NEW private diagnostic case; no mount, service or action is executed.
from pathlib import Path
import argparse, hashlib, json, shutil
r = Path('/home/tv/repositorio-principal')
report = r / 'reports/android16-service-profile'
p = argparse.ArgumentParser()
p.add_argument('--case', choices=['canonical', 'bad-option', 'bad-arity', 'missing'], required=True)
p.add_argument('--output', type=Path, required=True)
a = p.parse_args()
out = a.output.resolve()
out.mkdir()
(out / 'data/profiles').mkdir(parents=True)
(out / 'app').mkdir()
profile = r / 'dist/aosp16/propertyinit-execution-2/vendor'
version = profile / 'etc/selinux/plat_sepolicy_vers.txt'
assert hashlib.sha256(version.read_bytes()).hexdigest() == json.loads((report / 'vendor-profile.json').read_text())['sha256']
shutil.copytree(profile, out / 'vendor')
artifact = r / 'dist/aosp16/service-profile-build-3/verify-service-profile'
assert hashlib.sha256(artifact.read_bytes()).hexdigest() == json.loads((report / 'findings.json').read_text())['artifact']['sha256']
shutil.copy2(artifact, out / 'data/verify-service-profile')
if a.case == 'canonical':
    for item in json.loads((report / 'canonical-paths.json').read_text()):
        if item['logical'].startswith('/system'):
            source = Path(item['resolved'])
            assert hashlib.sha256(source.read_bytes()).hexdigest() == item['sha256']
    by_name = {x['name']: x for x in json.loads((report / 'profile-provenance.json').read_text())}
    vendor = out / 'vendor/etc/init'
    vendor.mkdir()
    for name, target in [('vndservicemanager.rc', 'vndservicemanager.rc'), ('composer.rc', 'android.hardware.graphics.composer@2.1-service.rc')]:
        item = by_name[name]
        source = Path(item['path'])
        assert hashlib.sha256(source.read_bytes()).hexdigest() == item['sha256']
        shutil.copy2(source, vendor / target)
    args = ['/system/etc/init/servicemanager.rc', '/vendor/etc/init/vndservicemanager.rc', '/system_ext/etc/init/hwservicemanager.rc', '/vendor/etc/init/android.hardware.graphics.composer@2.1-service.rc']
elif a.case == 'missing':
    args = ['/data/profiles/absent.rc']
else:
    shutil.copy2(report / 'fixtures' / (a.case + '.rc'), out / 'data/profiles/rejected.rc')
    args = ['/data/profiles/rejected.rc']
s = (r / 'reports/android16-libui-link/native-launcher.py').read_text()
s = s.replace("out=r/'dist/aosp16/libui-native-execution-1'", 'out=Path(' + repr(str(out)) + ')')
s = s.replace("'data','dev','proc'", "'data','vendor','dev','proc'")
s = s.replace("(root/'etc').symlink_to('/system/etc');", "mount('--bind',out/'vendor',root/'vendor');mount('-o','remount,bind,ro',root/'vendor');(root/'etc').symlink_to('/system/etc');")
s = s.replace("os.execve('/data/ui-runtime-probe',['/data/ui-runtime-probe']", "os.execve('/data/verify-service-profile'," + repr(['/data/verify-service-profile'] + args))
assert '/data/verify-service-profile' in s and str(out) in s
(out / 'launcher.py').write_text(s)
print(out / 'launcher.py')
