from pathlib import Path
import json,subprocess,hashlib
r=Path('/home/tv/repositorio-principal');p=r/'reports/android16-hidl-generator';tool=r/'dist/aosp16/hidl-host-build-8/hidl-gen';assert tool.is_file();out=r/'dist/aosp16/hidl-generated-1';out.mkdir();cache=Path('/home/tv/.cache/archtv/graphics-candidates-1');hardware=cache/'hidl-generation-inputs';transport=cache/'libhidl/transport';roots=['-randroid.hardware:'+str(hardware),'-randroid.hidl:'+str(transport)];targets=['android.hardware.graphics.common@1.0','android.hardware.graphics.common@1.1','android.hardware.graphics.common@1.2','android.hardware.graphics.composer@2.1','android.hidl.base@1.0'];approved=set()
for file in [hardware/'current.txt',transport/'current.txt']:
 for line in file.read_text().splitlines():
  words=line.split()
  if len(words)>=2 and len(words[0])==64:approved.add((words[0],words[1]))
record={'scope':'Original generated transport source/header artifacts and original frozen hash comparison; NOT compiled native interface, service, device or APK compatibility','tool_sha256':hashlib.sha256(tool.read_bytes()).hexdigest(),'commands':[],'hash_matches':[]}
for target in targets:
 for lang in ['hash','c++-headers','c++-sources']:
  cmd=[str(tool),'-L'+lang]+roots+([] if lang=='hash' else ['-o',str(out)])+[target];x=subprocess.run(cmd,capture_output=True,text=True,timeout=60);row={'target':target,'language':lang,'argv':cmd,'exit_code':x.returncode,'stdout':x.stdout,'stderr':x.stderr};record['commands'].append(row);(p/'generation.json').write_text(json.dumps(record,indent=2)+'\n');print(target,lang,x.returncode,x.stderr[:1500],flush=True);assert x.returncode==0
  if lang=='hash':
   assert x.stdout.strip(), 'empty hash output for '+target
   for line in x.stdout.splitlines():
    words=line.split();assert len(words)==2 and (words[0],words[1]) in approved,line;record['hash_matches'].append({'hash':words[0],'fqname':words[1],'matches_original_current':True})
record['generated_files']=[{'path':str(f.relative_to(out)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'bytes':f.stat().st_size} for f in sorted(out.rglob('*')) if f.is_file()];(p/'generation.json').write_text(json.dumps(record,indent=2)+'\n');print('Frozen hashes matched',len(record['hash_matches']),'generated files',len(record['generated_files']),flush=True)
