#!/usr/bin/env python3
"""Build a signed platform RRO; runtime policy/configuration remains unproven."""
from pathlib import Path
import hashlib,json,os,secrets,subprocess,sys

r=Path(__file__).resolve().parents[2]
out=(r/sys.argv[1]).resolve();out.mkdir()
source=r/'runtime/aosp/platform-overlay'
aapt=Path('/home/tv/.cache/archtv/apk-build-tools/aapt2')
apksig=Path('/home/tv/.cache/archtv/aosp16-qpr2/apksig-original-1')
core=apksig/'core-classes'
framework=r/'dist/aosp16/factory-inputs-3/root/system/framework/framework-res.apk'
signing=Path('/home/tv/.cache/archtv/platform-overlay-signing')
signing.mkdir(mode=0o700,exist_ok=True)
assert signing.stat().st_mode&0o077==0
password=signing/'password';key=signing/'overlay.p12'
if not password.exists():
    fd=os.open(password,os.O_WRONLY|os.O_CREAT|os.O_EXCL,0o600)
    with os.fdopen(fd,'w') as f:f.write(secrets.token_urlsafe(40)+'\n')
assert password.stat().st_mode&0o077==0
record={'scope':'Signed RRO bytes only; not original idmap/resource execution or APK compatibility','commands':[]}
def run(argv):
    p=subprocess.run(list(map(str,argv)),capture_output=True,text=True,timeout=150)
    record['commands'].append({'argv':list(map(str,argv)),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
    (out/'build.json').write_text(json.dumps(record,indent=2)+'\n')
    if p.returncode:raise RuntimeError(p.stderr)
if not key.exists():
    run(['keytool','-genkeypair','-keystore',key,'-storetype','PKCS12','-alias','archtv-overlay',
         '-keyalg','RSA','-keysize','3072','-validity','3650','-dname','CN=ArchTv Linux Platform Overlay',
         '-storepass:file',password,'-keypass:file',password])
    key.chmod(0o600)
assert key.stat().st_mode&0o077==0
run([aapt,'version'])
run([aapt,'compile','--dir',source/'res','-o',out/'resources.zip'])
run([aapt,'link','-I',framework,'--manifest',source/'AndroidManifest.xml',
     '--auto-add-overlay','-o',out/'unsigned.apk',out/'resources.zip'])
(out/'classes').mkdir()
run(['javac','-cp',core,'-d',out/'classes',r/'tools/apk/SignPlatformOverlay.java'])
run(['java','-cp',str(out/'classes')+':'+str(core),'SignPlatformOverlay',key,password,
     out/'unsigned.apk',out/'ArchTvPlatform.apk'])
inputs=[aapt,framework,apksig/'source.tar.gz',core/'com/android/apksig/ApkSigner.class',
        core/'com/android/apksig/ApkVerifier.class',r/'tools/apk/SignPlatformOverlay.java',
        *sorted(source.rglob('*.xml'))]
record['inputs_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in inputs}
record['apk_sha256']=hashlib.sha256((out/'ArchTvPlatform.apk').read_bytes()).hexdigest()
record['trust']='Own platform overlay signer; not an AOSP platform signing key. Vendor overlayable policy must still be enforced by original idmap2.'
record['private_material']='Outside Git in private build cache; values omitted'
(out/'build.json').write_text(json.dumps(record,indent=2)+'\n')
print(out,flush=True)
