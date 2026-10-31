from pathlib import Path
import sys,tarfile,hashlib,subprocess,json
r=Path('/home/tv/repositorio-principal');out=Path(sys.argv[1]);out.mkdir();archive=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/system-core/source.tar.gz');assert hashlib.sha256(archive.read_bytes()).hexdigest()=='4babe45eb994e8469b767b7775a1553ce0b9fed0e0a4c37797124fc764fdfde1'
files=['persistent_properties.h','persistent_properties.cpp','property_service.cpp','property_service.h','init.cpp','init.h'];rec={'source_commit':'e9d1fa3705d7fbd0ac1c942bc4c276161bfbfed1','patches':[]}
with tarfile.open(archive) as t:
 for n in files:(out/n).write_bytes(t.extractfile('init/'+n).read())
for name in ['0001-property-persistence-errors.patch','0002-property-service-shutdown.patch','0003-linux-property-action-coordinator.patch']:
 p=r/'runtime/aosp/android16-qpr2/patches'/name;cmd=['/usr/bin/patch','--batch','--fuzz=0','-p2','-d',str(out),'-i',str(p)];x=subprocess.run(cmd,capture_output=True,text=True);rec['patches'].append({'path':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'argv':cmd,'exit':x.returncode,'stdout':x.stdout,'stderr':x.stderr});assert x.returncode==0,x.stderr
rec['files']=[{'name':n,'sha256':hashlib.sha256((out/n).read_bytes()).hexdigest()} for n in files];(out/'application.json').write_text(json.dumps(rec,indent=2)+'\n');print('Zero-fuzz patch chain applied to pinned archive files')
