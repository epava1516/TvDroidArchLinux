from pathlib import Path
import json,subprocess,hashlib,importlib.util,re,shutil
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/service-profile-build-2';out.mkdir();d=out/'link-libs';d.mkdir();old=json.loads((r/'dist/aosp16/service-profile-build-1/build.json').read_text())['commands'];flags=old[0]['argv'][:old[0]['argv'].index('-c')];src=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/lmkd/source/system/memory/lmkd/liblmkd_utils.cpp');cmd=flags+['-c',str(src),'-o',str(out/'liblmkd_utils.o')];x=subprocess.run(cmd,capture_output=True,text=True,timeout=120);rec={'scope':'Original complete liblmkd_utils source plus original GSI libxml2/bootloader providers; no lmkd/recovery operation executed','compile':{'argv':cmd,'exit':x.returncode,'stderr':x.stderr,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()},'providers':[]};(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n');print('support compile',x.returncode,x.stderr[:2000],flush=True);assert x.returncode==0
sp=importlib.util.spec_from_file_location('audit',r/'tools/aosp/audit_boot_inputs.py');m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);root=r/'dist/aosp16/factory-inputs-3/root';linkold=old[-1]['argv'];queue=[]
for a in linkold:
 if a.endswith('.so') and Path(a).is_file():queue.append((Path(a).name,Path(a)))
new=[]
for name in ['libxml2.so','libbootloader_message.so']:
 p=m.inside(root,'/system/lib64/'+name);queue.append((name,p));new.append(str(p))
seen=set()
while queue:
 name,p=queue.pop(0)
 if name in seen:continue
 seen.add(name);assert p.is_file(),p;(d/name).symlink_to(p);needed=re.findall(r'\(NEEDED\).*?\[([^]]+)\]',subprocess.check_output(['readelf','-d',str(p)],text=True));rec['providers'].append({'name':name,'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'needed':needed})
 for n in needed:
  logical=('/apex/com.android.runtime/lib64/bionic/' if n in ['libc.so','libm.so','libdl.so'] else '/system/lib64/')+n;f=m.inside(root,logical)
  if not f.is_file():
   candidates=list((root/'apex').glob('*/lib64/'+n));assert len(candidates)==1,(n,candidates);f=candidates[0]
  queue.append((n,f))
cmd=[str(out/'verify-service-profile') if a.endswith('/service-profile-build-1/verify-service-profile') else '--rpath-link='+str(d) if a.startswith('--rpath-link=') else a for a in linkold];cmd[cmd.index('-o'):cmd.index('-o')]=[str(out/'liblmkd_utils.o')]+new;x=subprocess.run(cmd,capture_output=True,text=True,timeout=120);rec['link']={'argv':cmd,'exit':x.returncode,'stderr':x.stderr};(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n');print('link',x.returncode,x.stderr[:5000],flush=True)
