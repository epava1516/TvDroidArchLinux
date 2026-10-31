from pathlib import Path
import json,subprocess,shutil
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/persistence-native-build-1';out.mkdir();old=json.loads((r/'reports/android16-propertyinit-entry/link.json').read_text())['attempts'];rec={'scope':'Original persistent property functions, own multi-process regression; not service permission/ACK/durability under power loss acceptance','commands':[]}
for i,row in enumerate(old):
 cmd=[]
 for a in row['argv']:
  if a.startswith('--Map='):continue
  if a.endswith('/propertyinit-link-2/entry.cpp'):a=str(r/'reports/android16-persistence-native/probe.cpp')
  elif a.endswith('/propertyinit-link-2/entry.o'):a=str(out/'probe.o')
  elif a.endswith('/propertyinit-link-2/entry'):a=str(out/'persistence-probe')
  cmd.append(a)
 if i:cmd[1:1]=['--no-undefined','--no-allow-shlib-undefined','--Map='+str(out/'link.map')]
 x=subprocess.run(cmd,capture_output=True,text=True,timeout=120);rec['commands'].append({'argv':cmd,'exit':x.returncode,'stderr':x.stderr});(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n');print(i,x.returncode,x.stderr[:3000],flush=True);assert x.returncode==0
exe=r/'dist/aosp16/persistence-native-execution-1';exe.mkdir();(exe/'data').mkdir();(exe/'app').mkdir();shutil.copy2(out/'persistence-probe',exe/'data/persistence-probe');s=(r/'reports/android16-libui-link/native-launcher.py').read_text().replace('libui-native-execution-1','persistence-native-execution-1').replace('ui-runtime-probe','persistence-probe');(exe/'launcher.py').write_text(s);(out/'native-launcher.py').write_text(s)
