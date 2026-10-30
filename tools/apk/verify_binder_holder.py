#!/usr/bin/env python3
"""Exercise the original holder allocator/finalizer with ASan allocation interception and LSan."""
import argparse,hashlib,json,os,subprocess
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--build',type=Path,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
root=Path(__file__).resolve().parents[2];build=a.build.resolve();proof=json.loads((build/'result.json').read_text());library=build/'libarchtv_binder_holder.so'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert proof['build_pass'] and sha(library)==proof['library_sha256']
out=a.output.resolve();out.mkdir(parents=True,exist_ok=False);fixture=root/'fixtures/aosp-binder-holder/holder-lifetime.cpp'
commands=[['clang++','-std=c++17','-O1','-g','-fsanitize=address','-fno-omit-frame-pointer',str(fixture),'-ldl','-o',str(out/'probe')],[str(out/'probe'),str(library)]]
env=dict(os.environ,ASAN_OPTIONS='detect_leaks=1');env.pop('LSAN_OPTIONS',None);env.pop('LD_PRELOAD',None)
result={'lifetime_pass':False,'commands':commands,'fixture_sha256':sha(fixture),'library_sha256':sha(library),'verifier_sha256':sha(Path(__file__)),'asan_options':env['ASAN_OPTIONS'],'scope':'12800 empty original holders allocated/finalized through original JNI exports, 100 cycles of 128 unique live pointers. Sanitized probe intercepts allocations; loaded production library is not compiler-instrumented. Not ART GC/finalizer scheduling, native JavaBBinder transport, IPC, extensions or general runtime lifetime proof.'}
for i,cmd in enumerate(commands):
 with (out/(str(i)+'.stdout')).open('w') as stdout,(out/(str(i)+'.stderr')).open('w') as stderr:r=subprocess.run(cmd,stdout=stdout,stderr=stderr,env=env,timeout=60)
 if r.returncode:
  result.update(failed_step=i,exit_code=r.returncode);break
else:
 result['lifetime_pass']='NATIVE_BINDER_HOLDER_OK objects=12800 cycles=100' in (out/'1.stdout').read_text()
(out/'result.json').write_text(json.dumps(result,indent=2)+'\n')
if not result['lifetime_pass']:raise SystemExit('Holder lifetime verification failed: '+str(out))
print(out/'result.json')
