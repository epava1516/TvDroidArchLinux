#!/usr/bin/env python3
"""Source-reviewed, equal-size original Zygote target adaptation; not a source rebuild.
Preserves all original executable instructions except the selected class target and security/fork hooks. No SDK stubs.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,zipfile,zlib,struct
r=Path(__file__).resolve().parents[2];out=(r/sys.argv[1]).resolve();out.mkdir()
parent=r/'dist/aosp16/keystore-framework-profile-2';original=parent/'framework.jar';build=json.loads((parent/'build.json').read_text());assert hashlib.sha256(original.read_bytes()).hexdigest()==build['output']['sha256']
source=Path('/home/tv/.cache/archtv/aosp16-qpr2/package-bootstrap-study-1/ZygoteInit.java');assert hashlib.sha256(source.read_bytes()).hexdigest()=='e2299c75b02bfe180deb346b14d80a71cafe5258a05f0ff6c3f39fc024441bae'
assert source.read_text().count('"com.android.server.SystemServer"')==1
patch=r/'runtime/aosp/android16-qpr2/patches/framework-zygote-selected-entry.patch'
planner=r/'tools/aosp/ZygoteSelectedEntryPlan.java';engine=Path('/home/tv/.local/share/rea/android/jadx-headless-mcp-0.7.1-all.jar');commands=[]
def run(argv):
 p=subprocess.run(list(map(str,argv)),text=True,capture_output=True);commands.append({'argv':list(map(str,argv)),'exit':p.returncode,'stderr':p.stderr});(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');assert p.returncode==0,p.stderr;return p.stdout
run(['javac','-cp',engine,'-d',out,planner]);plan=run(['java','-cp',str(out)+':'+str(engine),'ZygoteSelectedEntryPlan',original,out/'adapted.dex']).strip().split();assert len(plan)==4,plan
entry,methods,differences,original_references=plan;assert entry.endswith('.dex') and differences=='1'
changed=[];output=out/'framework.jar'
with zipfile.ZipFile(original) as src,zipfile.ZipFile(output,'w',compression=zipfile.ZIP_STORED) as dst:
 for info in src.infolist():
  raw=src.read(info.filename)
  if info.filename==entry:
   replacement=(out/'adapted.dex').read_bytes()
   changed.append({'entry':entry,'method':'ZygoteInit.forkSystemServer','before':'com.android.server.SystemServer','after':'archtv.runtime.SelectedRuntime','methods_verified':int(methods),'instruction_differences':int(differences),'original_shared_string_references':int(original_references),'original_sha256':hashlib.sha256(raw).hexdigest(),'adapted_sha256':hashlib.sha256(replacement).hexdigest()});raw=replacement
  dst.writestr(info,raw)
assert len(changed)==1
with zipfile.ZipFile(original) as src,zipfile.ZipFile(output) as dst:
 assert src.namelist()==dst.namelist()
 for name in src.namelist():
  if name!=entry:assert src.read(name)==dst.read(name)
record={'parent':str(original),'parent_sha256':hashlib.sha256(original.read_bytes()).hexdigest(),'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'source_patch_sha256':hashlib.sha256(patch.read_bytes()).hexdigest(),'planner_sha256':hashlib.sha256(planner.read_bytes()).hexdigest(),'builder_sha256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'output':str(output),'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'changes':changed,'commands':commands,'scope':'Original framework plus prior explicit keystore profile; one Zygote target instruction reference adapted with dexlib2; shared SystemServer references retained and all executable instruction operands compared. Original fork/security/UID/GID/capability/classloader instructions retained. No source rebuild, runtime or APK compatibility acceptance.'}
(out/'build.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps(record['changes']))
