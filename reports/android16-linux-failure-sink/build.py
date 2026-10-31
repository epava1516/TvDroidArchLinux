from pathlib import Path
import json,subprocess,shutil
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-linux-failure-sink';out=r/'dist/aosp16/linux-failure-sink-build-1';out.mkdir();old=json.loads((r/'reports/android16-child-reaper/build-attempt-2.json').read_text());record=[]
compile=next(x['argv'] for x in old['commands'] if '-c' in x['argv'] and str(r/'reports/android16-child-reaper/probe.cpp') in x['argv'])
link=next(x['argv'] for x in old['commands'] if str(r/'dist/aosp16/child-reaper-build-2/child-reaper-probe') in x['argv'])
for name,source in [('probe',d/'probe.cpp'),('worker',r/'runtime/aosp/native/linux-property-worker.cpp')]:
 c=compile[:compile.index('-c')]+['-c',str(source),'-o',str(out/(name+'.o'))]
 l=[str(out/(name+'.o')) if x.endswith('/child-reaper-build-2/probe.o') else str(out/('failure-probe' if name=='probe' else 'linux-property-worker')) if x.endswith('/child-reaper-build-2/child-reaper-probe') else x for x in link]
 for cmd in [c,l]:
  p=subprocess.run(cmd,capture_output=True,text=True,timeout=120);record.append({'argv':cmd,'exit':p.returncode,'stderr':p.stderr});(d/'build.json').write_text(json.dumps(record,indent=2)+'\n');print(name,p.returncode,p.stderr[:1500],flush=True);assert p.returncode==0
for case in ['normal','oversize','worker']:
 exe=r/('dist/aosp16/linux-failure-sink-'+case+'-1');exe.mkdir();(exe/'data').mkdir();shutil.copytree(r/'dist/aosp16/propertyinit-execution-2/vendor',exe/'vendor')
 s=(r/'reports/android16-rust-supervisor/launcher-diagnostic.py').read_text().replace('rust-supervisor-diagnostic-1','linux-failure-sink-'+case+'-1')
 if case=='worker':shutil.copy2(out/'linux-property-worker',exe/'data/linux-property-worker')
 else:
  (exe/'data/profiles').mkdir();target='reboot' if case=='normal' else 'reboot,'+'x'*25;fixture='service audit.failure /system/bin/servicemanager\n    user system\n    reboot_on_failure '+target+'\n';(exe/'data/profiles/service.rc').write_text(fixture);(d/('fixture-'+case+'.rc')).write_text(fixture);shutil.copy2(out/'failure-probe',exe/'data/failure-probe');i=s.index("os.execve('/data/linux-property-worker'");s=s[:i]+"os.execve('/data/failure-probe',['/data/failure-probe',"+repr(case)+"],{'ANDROID_ROOT':'/system','ANDROID_DATA':'/data','ARCHTV_NATIVE_CONTROL_FD':os.environ['ARCHTV_NATIVE_CONTROL_FD']})\n"
 (exe/'launcher.py').write_text(s);shutil.copy2(exe/'launcher.py',d/('launcher-'+case+'.py'))
