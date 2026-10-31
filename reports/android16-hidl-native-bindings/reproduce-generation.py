from pathlib import Path
import json,subprocess,hashlib,shutil
r=Path('/home/tv/repositorio-principal');p=r/'reports/android16-hidl-native-bindings';old=r/'dist/aosp16/hidl-generated-1';out=r/'dist/aosp16/hidl-generated-native-closure-1';shutil.copytree(old,out);cache=Path('/home/tv/.cache/archtv/graphics-candidates-1');root=cache/'libhidl/transport';tool=r/'dist/aosp16/hidl-host-build-8/hidl-gen';hardware=cache/'hidl-generation-inputs';approved=set()
for line in (root/'current.txt').read_text().splitlines():
 words=line.split()
 if len(words)>=2 and len(words[0])==64:approved.add((words[0],words[1]))
rec={'scope':'Original manager package source generation for complete native closure, NOT native service execution','commands':[],'hash_matches':[]};roots=['-randroid.hardware:'+str(hardware),'-randroid.hidl:'+str(root)]
for v in ['1.0','1.1','1.2']:
 target='android.hidl.manager@'+v
 for lang in ['hash','c++-headers','c++-sources']:
  cmd=[str(tool),'-L'+lang]+roots+([] if lang=='hash' else ['-o',str(out)])+[target];x=subprocess.run(cmd,capture_output=True,text=True,timeout=60);rec['commands'].append({'argv':cmd,'exit_code':x.returncode,'stdout':x.stdout,'stderr':x.stderr});print(target,lang,x.returncode,x.stderr[:1200],flush=True);assert x.returncode==0
  if lang=='hash':
   assert x.stdout.strip()
   for line in x.stdout.splitlines():
    h,n=line.split();assert (h,n) in approved;pkg,name=n.split('::');ver=pkg.split('@')[1];src=root/'manager'/ver/(name+'.hal');assert hashlib.sha256(src.read_bytes()).hexdigest()==h;rec['hash_matches'].append({'hash':h,'fqname':n,'matches_original_current_and_raw_sha256':True})
rec['generated_files']=[{'path':str(f.relative_to(out)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in sorted(out.rglob('*')) if f.is_file()];(p/'generation.json').write_text(json.dumps(rec,indent=2)+'\n');print('Native closure files',len(rec['generated_files']),'manager frozen/raw hashes',len(rec['hash_matches']),flush=True)
