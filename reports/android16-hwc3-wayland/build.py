from pathlib import Path
import subprocess,json,hashlib,shutil,time
r=Path('/home/tv/repositorio-principal');cache=Path('/home/tv/.cache/archtv/graphics-candidates-1');out=r/'dist/aosp16/hwc3-wayland-1';out.mkdir();tree=out/'source';shutil.copytree(cache/'goldfish-hwc3',tree);record={'scope':'Whole original HWC3 frontend/factory with real Wayland backend compile; not runtime/mapper/timing/APK acceptance','commands':[]}
def run(cmd,timeout=150):
 t=time.monotonic();p=subprocess.run(cmd,capture_output=True,text=True,timeout=timeout);record['commands'].append({'argv':list(map(str,cmd)),'exit':p.returncode,'seconds':time.monotonic()-t,'stderr':p.stderr});(out/'build.json').write_text(json.dumps(record,indent=2)+'\n');print(Path(str(cmd[0])).name,p.returncode,p.stderr[:1800],flush=True)
 if p.returncode:raise SystemExit(p.returncode)
for patch in ['goldfish-hwc3-backend-headers.patch','goldfish-hwc3-wayland-factory.patch','goldfish-hwc3-wayland-display.patch']:run(['patch','--batch','--forward','-p1','-d',str(tree),'-i',str(r/'runtime/aosp/android16-qpr2/patches'/patch)])
flags=json.loads((r/'reports/android16-hwc3-frontend/build.json').read_text())['results'][0]['argv'];flags=flags[:flags.index('-MMD')];flags=[arg for arg in flags if not arg.endswith('/dist/aosp16/hwc3-frontend-2/source')];flags+=['-D_GNU_SOURCE','-I'+str(tree),'-I'+str(r/'runtime/aosp/native'),'-I'+str(cache/'jsoncpp/include'),'-I'+str(cache/'wayland/src'),'-I'+str(r/'dist/aosp16/wayland-client-1/generated'),'-I'+str(r/'dist/aosp16/wayland-output-3')]
units=[tree/(n+'.cpp') for n in ['Main','Composer','ComposerClient','ComposerResources','Common','Display','DisplayConfig','Layer','VsyncThread','Device']]+[r/'runtime/aosp/native'/n for n in ['linux-wayland-output.cpp','linux-wayland-frame-composer.cpp','linux-wayland-display-finder.cpp']];record['sources']=[]
for source in units:
 obj=out/(source.stem+'.o');run(flags+['-MMD','-MF',str(out/(source.stem+'.d')),'-c',str(source),'-o',str(obj)]);record['sources'].append({'path':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'object_sha256':hashlib.sha256(obj.read_bytes()).hexdigest()})
record['terminal']=True;(out/'build.json').write_text(json.dumps(record,indent=2)+'\n')
