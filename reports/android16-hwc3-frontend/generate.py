from pathlib import Path
import json,subprocess,hashlib
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/hwc3-aidl-v4-1';out.mkdir();(out/'include').mkdir();(out/'src').mkdir()
hw=Path('/home/tv/.cache/archtv/graphics-candidates-1/hardware-interfaces');tool=r/'dist/aosp16/aidl-host-build-4/aidl'
common=hw/'common/aidl/aidl_api/android.hardware.common/2';graphics=hw/'graphics/common/aidl';drm=hw/'drm/common/aidl/aidl_api/android.hardware.drm.common/1';composer=hw/'graphics/composer/aidl/aidl_api/android.hardware.graphics.composer3/4'
roots=[common,graphics,drm,composer];rec={'scope':'Original A16 frozen ComposerV4/DRM commonV1 generation; graphics common currentV7 import is NOT frozenV7; reuse previous commonV2/graphicsV7 generated headers. Not linked/executed ABI acceptance.','tool_sha256':hashlib.sha256(tool.read_bytes()).hexdigest(),'results':[]}
for root,version in [(drm,1),(composer,4)]:
 h=(root/'.hash').read_text().splitlines()[-1].strip();assert len(h)==40
 files=sorted(root.rglob('*.aidl'));cmd=[str(tool),'--lang=ndk','--structured','--stability=vintf','--version='+str(version),'--hash='+h,'--min_sdk_version=29','--omit_invocation','--out='+str(out/'src'),'--header_out='+str(out/'include')]+['-I'+str(p) for p in roots]+list(map(str,files))
 x=subprocess.run(cmd,capture_output=True,text=True,timeout=90);rec['results'].append({'argv':cmd,'version':version,'hash_argument':h,'inputs':[{'path':str(f),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in files],'exit':x.returncode,'stderr':x.stderr});(out/'generation.json').write_text(json.dumps(rec,indent=2)+'\n');print(root.name,len(files),x.returncode,x.stderr[:1800],flush=True);assert x.returncode==0
rec['generated_files']=[{'path':str(p.relative_to(out)),'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in sorted(out.rglob('*')) if p.is_file() and p.name!='generation.json'];(out/'generation.json').write_text(json.dumps(rec,indent=2)+'\n')
