#!/usr/bin/env python3
"""Build complete original AOSP IHealth default provider; no runtime claim."""
from pathlib import Path
import json,subprocess,hashlib,sys
r=Path(__file__).resolve().parents[2];out=(r/sys.argv[1]).resolve();out.mkdir()
study=Path('/home/tv/.cache/archtv/aosp16-qpr2/health-original-study-1');hw=study/'hardware-health';core=study/'healthd';cache=Path('/home/tv/.cache/archtv/graphics-candidates-1')
record={'scope':'Original health AIDL/default, BatteryMonitor and HealthLoop build; not execution, battery or framework readiness','commands':[],'sources':[]}
def run(argv):
 p=subprocess.run(list(map(str,argv)),capture_output=True,text=True,timeout=120)
 record['commands'].append({'argv':list(map(str,argv)),'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr});(out/'build.json').write_text(json.dumps(record,indent=2)+'\n');print(Path(str(argv[0])).name,p.returncode,p.stderr[:2200],flush=True);assert p.returncode==0,p.stderr
root=out/'interfaces';root.mkdir();(root/'health').symlink_to(hw,target_is_directory=True)
for version in ['1.0','2.0','2.1']:
 run([r/'dist/aosp16/hidl-host-build-8/hidl-gen','-Lc++-headers','-randroid.hardware:'+str(root),'-randroid.hidl:'+str(cache/'libhidl/transport'),'-o',out/'hidl','android.hardware.health@'+version])
api=hw/'aidl/aidl_api/android.hardware.health/4';h=(api/'.hash').read_text().splitlines()[-1]
run([r/'dist/aosp16/aidl-host-build-4/aidl','--lang=ndk','--structured','--stability=vintf','--version=4','--hash='+h,'--min_sdk_version=29','--omit_invocation','--out='+str(out/'aidl/src'),'--header_out='+str(out/'aidl/include'),'-I'+str(api)]+sorted(api.rglob('*.aidl')))
flags=json.loads((r/'reports/android16-hwc3-frontend/build.json').read_text())['results'][0]['argv'];flags=flags[:flags.index('-MMD')]
includes=[out/'aidl/include',out/'hidl',hw/'aidl/include',hw/'aidl/default/include',hw/'utils/libhealthloop/include',core/'include',core,study/'batteryservice/include',study/'bpf-wrappers/include',study/'bpf-headers/include',cache/'libhidl/base/include',cache/'libhidl/transport/include',cache/'libhwbinder/include']
flags+=['-DCHARGER_FORCE_NO_UI=1','-D_GNU_SOURCE']+['-I'+str(p) for p in includes]
units=[hw/'aidl/default'/n for n in ['main.cpp','Health.cpp','HalHealthLoop.cpp','LinkedCallback.cpp','health-convert.cpp']]+[core/'BatteryMonitor.cpp',hw/'aidl/android/hardware/health/translate-ndk.cpp',hw/'utils/libhealthloop/HealthLoop.cpp',hw/'utils/libhealthloop/utils.cpp']
for i,p in enumerate(units):
 obj=out/(str(i)+'.o');f=flags
 if p.suffix=='.c':f=[x for x in flags if not x.startswith('-std=')]+['-x','c','-std=gnu11']
 run(f+['-c',p,'-o',obj]);record['sources'].append({'path':str(p),'sha256':hashlib.file_digest(p.open('rb'),'sha256').hexdigest(),'object':str(obj)})
record['compiled']=True;(out/'build.json').write_text(json.dumps(record,indent=2)+'\n')

libs=r/'dist/aosp16/factory-inputs-3/root/system/lib64';support=r/'dist/aosp16/hwc3-frontend-2/link-libs'
needed=['android.hardware.health-V4-ndk.so','libbase.so','libbinder_ndk.so','libcutils.so','libhidlbase.so','liblog.so','libutils.so','libc++.so','libc.so','libm.so','libdl.so']
ld=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-toolchain-1/bin/ld.lld');binary=out/'android.hardware.health-service.example'
run([ld,'--error-limit=0','--no-undefined','--no-allow-shlib-undefined','-pie','--dynamic-linker=/system/bin/linker64','-z','relro','-z','now','--rpath-link='+str(libs),'--rpath-link='+str(support),r/'dist/aosp16/crt-native-1/crtbegin_dynamic.o']+[x['object'] for x in record['sources']]+['-L'+str(libs),'-L'+str(support)]+['-l:'+n for n in needed]+[cache/'compiler-builtins/libclang_rt.builtins-x86_64-android.a',r/'dist/aosp16/crt-native-1/crtend_android.o','-o',binary])
record['binary_sha256']=hashlib.file_digest(binary.open('rb'),'sha256').hexdigest();record['source_acquisition']={p.name:json.loads(p.read_text()) for p in study.glob('*source.json')};record['terminal']=True
(out/'build.json').write_text(json.dumps(record,indent=2)+'\n')
