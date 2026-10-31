from pathlib import Path
import subprocess,json,shutil,hashlib,time
r=Path('/home/tv/repositorio-principal');s=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs');prior=r/'dist/aosp16/libinit-native-group-5';old=json.loads((prior/'state.json').read_text());assert old['status']=='terminal' and len(old['results'])==52;out=r/'dist/aosp16/libinit-native-finalize-1';out.mkdir();(out/'objects').mkdir();base=old['common_argv'];extra='-I'+str(s/'libxml2-target/source/external/libxml2/include');source=s/'system-core/source/system/core/init';rows=[];start=time.monotonic();state={'source_base_commit':old['source_base_commit'],'common_argv':base+[extra],'status':'running','scope':'All52source construction; reuse only after actual before/after compiler preprocessor byte equality and object SHA validation. Not full Soong/sanitizer/product equivalence or runtime acceptance. Generated source members and dependency graph tracked separately.','results':rows}
for row in old['results']:
 name=row['source'];src=source/name;dest=out/'objects'/(name+'.o');record={'source':name,'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest()}
 if row.get('exit_code')==0:
  hashes=[]
  for options in [base,base+[extra]]:
   run=subprocess.run(options+['-E','-P',str(src)],capture_output=True)
   if run.returncode:raise SystemExit(run.stderr.decode(errors='replace'))
   hashes.append(hashlib.sha256(run.stdout).hexdigest())
  record['preprocessor_before_after_sha256']=hashes
  if hashes[0]==hashes[1]:
   obj=prior/'objects'/(name+'.o');assert hashlib.sha256(obj.read_bytes()).hexdigest()==row['object_sha256'];shutil.copy2(obj,dest);record.update(exit_code=0,reused_after_token_equality=True,object_sha256=row['object_sha256'])
 if not dest.exists():
  argv=base+[extra,'-c',str(src),'-o',str(dest)];run=subprocess.run(argv,capture_output=True,text=True);record.update(exit_code=run.returncode,reused_after_token_equality=False,argv=argv,stdout=run.stdout,stderr=run.stderr)
  if run.returncode==0:record['object_sha256']=hashlib.sha256(dest.read_bytes()).hexdigest()
 rows.append(record);(out/'state.json').write_text(json.dumps(state,indent=2)+'\n');print(len(rows),52,name,record['exit_code'],'reuse' if record.get('reused_after_token_equality') else 'compile',flush=True)
state.update(status='terminal',elapsed_seconds=time.monotonic()-start,all52_sources_compiled=all(x['exit_code']==0 for x in rows));(out/'state.json').write_text(json.dumps(state,indent=2)+'\n');print('Terminal, all52',state['all52_sources_compiled'],flush=True)
