from pathlib import Path
import json,subprocess,shutil
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/property-socket-build-2';out.mkdir();old=json.loads((r/'reports/android16-propertyinit-entry/link.json').read_text())['attempts'];rec={'scope':'Actual original property server negative socket diagnostic only; no successful MAC/persistence or supervisor acceptance','commands':[]}
for i,row in enumerate(old):
 cmd=[]
 for a in row['argv']:
  if a.startswith('--Map='):continue
  if a.endswith('/propertyinit-link-2/entry.cpp'):a=str(r/'reports/android16-property-socket/probe.cpp')
  elif a.endswith('/propertyinit-link-2/entry.o'):a=str(out/'probe.o')
  elif a.endswith('/propertyinit-link-2/entry'):a=str(out/'property-socket-probe')
  elif a.endswith('/libinit-native-archive-1/libinit-native-prototype.a'):a=str(r/'dist/aosp16/property-errors-build-1/libinit-adapted.a')
  cmd.append(a)
 if i==0:cmd[1:1]=['-I'+str(r/'dist/aosp16/property-errors-source-1')]
 else:cmd[1:1]=['--no-undefined','--no-allow-shlib-undefined']
 x=subprocess.run(cmd,capture_output=True,text=True,timeout=120);rec['commands'].append({'argv':cmd,'exit':x.returncode,'stderr':x.stderr});(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n');print(i,x.returncode,x.stderr[:2200],flush=True);assert x.returncode==0
exe=r/'dist/aosp16/property-socket-execution-2';exe.mkdir();(exe/'data').mkdir();shutil.copytree(r/'dist/aosp16/propertyinit-execution-2/vendor',exe/'vendor');shutil.copy2(out/'property-socket-probe',exe/'data/property-socket-probe');s=(r/'reports/android16-property-profile/reproduce/propertyinit-execution-2-reproduce.py').read_text().replace('propertyinit-execution-2','property-socket-execution-2').replace("mount('-o','remount,bind,ro',root/'data');",'');s=s.replace("(root/'dev/null').touch()","(root/'dev/socket').mkdir();(root/'dev/null').touch()");s=s.replace("os.execve('/data/entry',['/data/entry']","os.execve('/data/property-socket-probe',['/data/property-socket-probe']");(exe/'launcher.py').write_text(s);(out/'native-launcher.py').write_text(s)
