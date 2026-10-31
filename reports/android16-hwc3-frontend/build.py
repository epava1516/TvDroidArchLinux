from pathlib import Path
import json,subprocess,hashlib,shutil,difflib,time,sys
r=Path('/home/tv/repositorio-principal');cache=Path('/home/tv/.cache/archtv/graphics-candidates-1');source=cache/'goldfish-hwc3';out=r/'dist/aosp16'/('hwc3-frontend-2' if len(sys.argv)<2 else sys.argv[1]);out.mkdir();tree=out/'source';shutil.copytree(source,tree)
inventory=json.loads((r/'reports/android16-graphics-resume/goldfish-source-inventory.json').read_text())
for row in inventory['files']:
 assert hashlib.sha256((source/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
patch=r/'runtime/aosp/android16-qpr2/patches/goldfish-hwc3-backend-headers.patch'
subprocess.run(['patch','--batch','--forward','-p1','-i',str(patch)],cwd=tree,check=True,capture_output=True)
shutil.copyfile(patch,out/'backend-header-boundary.patch')
old=json.loads((r/'reports/android16-libui-link/native-compile.json').read_text())['results'][0]['argv'];flags=old[:old.index('-MMD')];flags+=['-I'+str(r/'dist/aosp16/hwc3-aidl-v4-1/include'),'-I'+str(cache/'hardware-interfaces/graphics/composer/2.2/utils/resources/include'),'-I'+str(cache/'hardware-interfaces/graphics/composer/aidl/include')]
names=['Main','Composer','ComposerClient','ComposerResources','Common','Display','DisplayConfig','Layer','VsyncThread'];rec={'scope':'Complete original HWC3 frontend implementation units, two pointer-only header edits and two unused backend includes removed; compile only. No factory/displayfinder/FrameComposer backend, executable, service/frame/APK acceptance.','results':[],'patch_sha256':hashlib.sha256((out/'backend-header-boundary.patch').read_bytes()).hexdigest()}
for name in names:
 src=tree/(name+'.cpp');cmd=flags+['-MMD','-MF',str(out/(name+'.d')),'-c',str(src),'-o',str(out/(name+'.o'))];t=time.monotonic();p=subprocess.run(cmd,capture_output=True,text=True,timeout=150);rec['results'].append({'source':str(src),'original_source_sha256':hashlib.sha256((source/src.name).read_bytes()).hexdigest(),'argv':cmd,'exit':p.returncode,'seconds':time.monotonic()-t,'stderr':p.stderr});(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n');print(name,p.returncode,p.stderr[:1400],flush=True)
rec['terminal']=True;(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n')

if any(row["exit"] != 0 for row in rec["results"]): raise SystemExit(1)
