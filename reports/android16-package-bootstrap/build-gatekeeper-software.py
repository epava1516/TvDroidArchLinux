#!/usr/bin/env python3
"""Build complete original nonsecure GateKeeper + SharedSecret service, not a stub."""
from pathlib import Path
import hashlib,json,subprocess,sys
r=Path(__file__).resolve().parents[2];out=(r/sys.argv[1]).resolve();out.mkdir()
b=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs')
hw=b/'gatekeeper-aidl-original/source/hardware/interfaces/gatekeeper/aidl'
secret=b/'security-hal-original/source/hardware/interfaces/security/sharedsecret/aidl'
km=b/'keymaster-original-v4/source/system/keymaster'
scrypt=b/'gatekeeper-scrypt-original/source/external/scrypt'
record={'scope':'Whole original software reference service build only, not publication/authentication/unlock/APK/MAC acceptance','commands':[],'sources':[],'provenance':{}}
for name in ['gatekeeper-aidl-original','gatekeeper-core-original','gatekeeper-scrypt-original','keymaster-original-v4','security-hal-original']:
 d=json.loads((b/name/'provenance.json').read_text());assert d['status']=='complete';record['provenance'][name]=d

def run(a):
 a=list(map(str,a));p=subprocess.run(a,capture_output=True,text=True,timeout=120)
 record['commands'].append({'argv':a,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});(out/'build.json').write_text(json.dumps(record,indent=2)+'\n');print(Path(a[0]).name,p.returncode,p.stderr[:1800],flush=True);assert p.returncode==0,p.stderr
apis=[hw/'aidl_api/android.hardware.gatekeeper/1',secret/'aidl_api/android.hardware.security.sharedsecret/1']
imports=apis+[b/'security-hal-original/source/hardware/interfaces/security/keymint/aidl/aidl_api/android.hardware.security.keymint/4',b/'security-hal-original/source/hardware/interfaces/security/secureclock/aidl/aidl_api/android.hardware.security.secureclock/1']
for api in apis:
 run([r/'dist/aosp16/aidl-host-build-4/aidl','--lang=ndk','--structured','--stability=vintf','--version=1','--hash='+(api/'.hash').read_text().splitlines()[-1],'--min_sdk_version=29','--omit_invocation','--out='+str(out/'aidl/src'),'--header_out='+str(out/'aidl/include'),*['-I'+str(p) for p in imports],*sorted(api.rglob('*.aidl'))])
flags=json.loads((r/'reports/android16-hwc3-frontend/build.json').read_text())['results'][0]['argv'];flags=flags[:flags.index('-MMD')]
flags+=['-fvisibility=hidden','-Wall','-Werror',*['-I'+str(p) for p in [out/'aidl/include',r/'dist/aosp16/keymint-software-build-3/aidl/include',km/'include',km/'ng/include',b/'gatekeeper-core-original/source/system/gatekeeper/include',scrypt,scrypt/'lib/crypto',scrypt/'lib/util',b/'keymint-boringssl-headers/source/external/boringssl/src/include']]]
units=[hw/'software'/n for n in ['GateKeeper.cpp','SharedSecret.cpp','service.cpp']]
for i,p in enumerate(units):
 obj=out/(str(i)+'.o');run(flags+['-c',p,'-o',obj]);record['sources'].append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'object':str(obj)})
# Exact x86_64 source/defines selected by original sources.bp, not a substitute.
p=scrypt/'lib/crypto/crypto_scrypt-sse.c';obj=out/'scrypt.o'
cflags=[x for x in flags if x not in ['-std=gnu++20','-nostdinc++']]+['-std=gnu17','-DHAVE_CONFIG_H','-DUSE_OPENSSL_PBKDF2','-Wno-unused-variable']
run(cflags+['-c',p,'-o',obj]);record['sources'].append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'object':str(obj)})
libs=r/'dist/aosp16/factory-inputs-3/root/system/lib64';support=r/'dist/aosp16/hwc3-frontend-2/link-libs'
needed=['android.hardware.security.keymint-V4-ndk.so','android.hardware.security.secureclock-V1-ndk.so','android.hardware.gatekeeper-V1-ndk.so','android.hardware.security.sharedsecret-V1-ndk.so','libbase.so','libbinder_ndk.so','libcrypto.so','libcutils.so','libgatekeeper.so','libhardware.so','libkeymaster_portable.so','liblog.so','libutils.so','libc++.so','libc.so','libm.so','libdl.so']
binary=out/'android.hardware.gatekeeper-service.nonsecure'
run([b.parent/'native-toolchain-1/bin/ld.lld','--no-undefined','--no-allow-shlib-undefined','-pie','--dynamic-linker=/system/bin/linker64','-z','relro','-z','now','--rpath-link='+str(libs),'--rpath-link='+str(support),r/'dist/aosp16/crt-native-1/crtbegin_dynamic.o',*[v['object'] for v in record['sources']],'-L'+str(libs),'-L'+str(support),*['-l:'+n for n in needed],Path('/home/tv/.cache/archtv/graphics-candidates-1/compiler-builtins/libclang_rt.builtins-x86_64-android.a'),r/'dist/aosp16/crt-native-1/crtend_android.o','-o',binary])
record['linked_libraries_sha256']={str((libs/n) if (libs/n).exists() else support/n):hashlib.sha256(((libs/n) if (libs/n).exists() else support/n).read_bytes()).hexdigest() for n in needed}
record['binary_sha256']=hashlib.sha256(binary.read_bytes()).hexdigest();record['terminal']=True
record['limitations']=['Original nonsecure reference is not CDD hardware protection','Runtime library ABI and service publication must be tested','No original vendor APEX packaged/activated by this build','Credential persistence and shared HMAC negotiation remain unproven']
(out/'build.json').write_text(json.dumps(record,indent=2)+'\n')
