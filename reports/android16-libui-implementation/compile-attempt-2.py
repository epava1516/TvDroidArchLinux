from pathlib import Path
import json,subprocess,time,hashlib,re
root=Path('/home/tv/repositorio-principal');out=root/'dist/aosp16/libui-implementation-build-2';out.mkdir();(out/'logs').mkdir()
native=Path('/home/tv/.cache/archtv/graphics-candidates-1/frameworks-native')
old=json.loads((root/'reports/android16-libui-source-closure/native-compile.json').read_text())['results'][0]['argv'];flags=old[:old.index('-MMD')]
flags += ['-I'+str(native/'include'),'-I'+str(native/'libs/arect/include')]
flags += ['-I'+str(root/'dist/aosp16/libui-interface-generated-1/hidl'),'-I'+str(root/'dist/aosp16/libui-interface-generated-1/aidl/include'),'-I/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/system-core/source/system/core/libgrallocusage/include','-I'+str(native/'libs/gralloc/types/include'),'-I/home/tv/.cache/archtv/graphics-candidates-1/hardware-interfaces/graphics/mapper/stable-c/include','-I/home/tv/.cache/archtv/graphics-candidates-1/hardware-interfaces/graphics/mapper/stable-c/implutils/include']
bp=(native/'libs/ui/Android.bp').read_text();blocks=[]
for name in ['libui-types','libui']:
 start=bp.index('name: "'+name+'"');m=re.search(r'srcs: \[(.*?)\]',bp[start:],re.S);files=re.findall(r'"([^" ]+\.cpp)"',m.group(1));blocks += [(name,native/'libs/ui'/f) for f in files]
rec={'scope':'All original libui and whole-static libui-types implementation source units, diagnostic compile only; no link or runtime acceptance','results':[]}
failed={Path(x['source']).name for x in json.loads((root/'reports/android16-libui-implementation/compile-attempt-1.json').read_text())['results'] if x['exit_code']}
for module,src in blocks:
 if src.name not in failed:continue
 cmd=flags+['-MMD','-MF',str(out/(src.stem+'.d')),'-c',str(src),'-o',str(out/(src.stem+'.o'))];t=time.monotonic();p=subprocess.run(cmd,capture_output=True,text=True,timeout=150)
 (out/'logs'/(src.stem+'.log')).write_text(p.stdout+p.stderr)
 rec['results'].append({'module':module,'source':str(src),'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'argv':cmd,'exit_code':p.returncode,'seconds':time.monotonic()-t,'stderr':p.stderr})
 (out/'state.json').write_text(json.dumps(rec,indent=2)+'\n');print(src.name,p.returncode,p.stderr[:400],flush=True)
rec['terminal']=True;(out/'state.json').write_text(json.dumps(rec,indent=2)+'\n')
