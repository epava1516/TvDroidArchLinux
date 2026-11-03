#!/usr/bin/env python3
"""Compile a JCA integration client; SDK signatures never enter runtime payload."""
from pathlib import Path
import subprocess,zipfile,json,hashlib,sys
r=Path(__file__).resolve().parents[2];o=(r/sys.argv[1]).resolve();o.mkdir();(o/'classes').mkdir();(o/'dex').mkdir()
sdk=Path('/home/tv/.cache/archtv/apk-build-tools/android.jar');src=r/'fixtures/aosp-keystore2-software/OriginalJavaProviderProbe.java';cmds=[]
for stage in range(2):
 a=['javac','-source','8','-target','8','-bootclasspath',str(sdk),'-d',str(o/'classes'),str(src)] if stage==0 else ['java','-cp','/home/tv/.cache/archtv/apk-build-tools/r8.jar','com.android.tools.r8.D8','--min-api','36','--lib',str(sdk),'--output',str(o/'dex'),*[str(x) for x in (o/'classes').rglob('*.class')]]
 p=subprocess.run(a,capture_output=True,text=True);cmds.append({'argv':a,'exit':p.returncode,'stderr':p.stderr});record={'commands':cmds,'scope':'Fixture only, SDK signatures compile-time only; no Android classes packaged','source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'sdk_sha256':hashlib.sha256(sdk.read_bytes()).hexdigest()};(o/'build.json').write_text(json.dumps(record,indent=2)+'\n');assert p.returncode==0,p.stderr
with zipfile.ZipFile(o/'probe.jar','w') as z:z.write(o/'dex/classes.dex','classes.dex')
record['jar_sha256']=hashlib.sha256((o/'probe.jar').read_bytes()).hexdigest();(o/'build.json').write_text(json.dumps(record,indent=2)+'\n');print(o)
