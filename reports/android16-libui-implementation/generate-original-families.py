from pathlib import Path
import json,subprocess,hashlib
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/libui-interface-generated-1';out.mkdir();cache=Path('/home/tv/.cache/archtv/graphics-candidates-1');hw=cache/'hardware-interfaces';tr=cache/'libhidl/transport';tool=r/'dist/aosp16/hidl-host-build-8/hidl-gen';rec={'scope':'Complete original allocator/mapper transport families generation only, no native service/runtime acceptance','commands':[],'hash_matches':[]}
approved=set()
for repo,path in [(hw,'current.txt'),(cache/'libhidl','transport/current.txt')]:
 text=subprocess.check_output(['git','-C',str(repo),'show','HEAD:'+path],text=True)
 for l in text.splitlines():
  w=l.split()
  if len(w)>=2 and len(w[0])==64:approved.add((w[0],w[1]))
targets=['android.hardware.graphics.allocator@'+v for v in ['2.0','3.0','4.0']]+['android.hardware.graphics.mapper@'+v for v in ['2.0','2.1','3.0','4.0']]
for target in targets:
 for lang in ['hash','c++-headers','c++-sources']:
  cmd=[str(tool),'-L'+lang,'-randroid.hardware:'+str(hw),'-randroid.hidl:'+str(tr)]+([] if lang=='hash' else ['-o',str(out/'hidl')])+[target];x=subprocess.run(cmd,capture_output=True,text=True,timeout=90);rec['commands'].append({'argv':cmd,'exit':x.returncode,'stdout':x.stdout,'stderr':x.stderr});print(target,lang,x.returncode,flush=True);assert x.returncode==0,x.stderr
  if lang=='hash':
   for l in x.stdout.splitlines():
    w=l.split();assert len(w)==2 and tuple(w) in approved,l;rec['hash_matches'].append(w)
common=hw/'common/aidl/aidl_api/android.hardware.common/2';graphics=hw/'graphics/common/aidl';alloc=hw/'graphics/allocator/aidl/aidl_api/android.hardware.graphics.allocator/2';files=sorted(alloc.rglob('*.aidl'));h=(alloc/'.hash').read_text().splitlines()[-1];cmd=[str(r/'dist/aosp16/aidl-host-build-4/aidl'),'--lang=ndk','--structured','--stability=vintf','--version=2','--hash='+h,'--min_sdk_version=29','--omit_invocation','--out='+str(out/'aidl/src'),'--header_out='+str(out/'aidl/include')]+['-I'+str(p) for p in [common,graphics,alloc]]+[str(p) for p in files];x=subprocess.run(cmd,capture_output=True,text=True,timeout=90);rec['commands'].append({'argv':cmd,'exit':x.returncode,'stdout':x.stdout,'stderr':x.stderr});assert x.returncode==0,x.stderr
rec['files']=[{'path':str(p.relative_to(out)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.rglob('*')) if p.is_file()];(out/'generation.json').write_text(json.dumps(rec,indent=2)+'\n');print('GENERATED',len(rec['files']),'HASH_MATCHES',len(rec['hash_matches']),flush=True)
