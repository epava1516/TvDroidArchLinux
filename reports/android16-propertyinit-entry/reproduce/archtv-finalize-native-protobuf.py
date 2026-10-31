from pathlib import Path
import json,hashlib,subprocess,shutil
r=Path('/home/tv/repositorio-principal');prior=r/'dist/aosp16/protobuf-native-1';s=json.loads((prior/'state.json').read_text());assert s['status']=='terminal' and len(s['results'])==146;out=r/'dist/aosp16/protobuf-native-2';out.mkdir();(out/'objects').mkdir();rows=[]
for row in s['results']:
 record=dict(row);dest=out/'objects'/Path(row.get('object',('105-log_sink_set.cc.o' if row['module']=='absl_log_internal_log_sink_set' else '140-common.cc.o'))).name
 if row['exit_code']==0:
  p=Path(row['object']);assert hashlib.sha256(p.read_bytes()).hexdigest()==row['object_sha256'];shutil.copy2(p,dest);record.update(object=str(dest),reused_sha_verified=True)
 else:
  assert row['module'] in ['absl_log_internal_log_sink_set','libprotobuf-cpp-lite'];assert "'android/log.h' file not found" in row['first_error'];cmd=list(row['argv']);cmd[cmd.index('-o')+1]=str(dest);cmd.insert(cmd.index('-c'),'-I/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/logging/source/system/logging/liblog/include');run=subprocess.run(cmd,capture_output=True,text=True);record.update(argv=cmd,exit_code=run.returncode,stdout=run.stdout,stderr=run.stderr,reused_sha_verified=False)
  if run.returncode==0:record.update(object=str(dest),object_sha256=hashlib.sha256(dest.read_bytes()).hexdigest())
 rows.append(record)
result={'scope':'Original protobuf/Abseil whole source closure prototype, original module liblog exported headers applied only to its consuming source; not full Soong equivalence or runtime readiness','status':'terminal','results':rows,'all_compiled':all(x['exit_code']==0 for x in rows),'prior_evidence':str(prior/'state.json')}
if result['all_compiled']:
 archive=out/'libprotobuf-lite-with-original-absl-prototype.a';cmd=['ar','rcsD',str(archive)]+[x['object'] for x in rows];subprocess.run(cmd,check=True);result.update(archive=str(archive),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
(out/'state.json').write_text(json.dumps(result,indent=2)+'\n');print('all compiled',result['all_compiled']);print([x.get('stderr') for x in rows if x['exit_code']])
