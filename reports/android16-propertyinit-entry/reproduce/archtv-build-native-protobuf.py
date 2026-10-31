from pathlib import Path
import re,json,subprocess,hashlib,time,os
r=Path('/home/tv/repositorio-principal');cache=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs');proto=cache/'protobuf/source/external/protobuf';absl=cache/'abseil/source/external/abseil-cpp';out=r/'dist/aosp16/protobuf-native-1';out.mkdir();(out/'objects').mkdir();(out/'logs').mkdir()
def modules(path):
 text=path.read_text();result={}
 for m in re.finditer(r'^([a-z_]+) \{',text,re.M):
  i=m.end();depth=1;quote=False;escape=False
  while depth:
   c=text[i];i+=1
   if quote:
    if escape:escape=False
    elif c=='\\':escape=True
    elif c=='"':quote=False
   elif c=='"':quote=True
   elif c=='{':depth+=1
   elif c=='}':depth-=1
  block=text[m.end():i-1];name=re.search(r'^    name: "([^"]+)"',block,re.M)
  if name:result[name[1]]={'kind':m[1],'text':block}
 return result
def arr(block,key):
 match=re.search(r'^    '+key+r': \[(.*?)\]',block,re.M|re.S)
 return re.findall(r'"([^"]+)"',match[1]) if match else []
pmods=modules(proto/'Android.bp');amods=modules(absl/'Android.bp');roots=arr(pmods['libprotobuf-cpp-lite-defaults']['text'],'static_libs');seen={}
def visit(name):
 if name in seen:return
 mod=amods[name];assert mod['kind']=='cc_library_static',name;seen[name]=mod
 for dep in arr(mod['text'],'whole_static_libs')+arr(mod['text'],'static_libs'):visit(dep)
for name in roots:visit(name)
# Generated Abseil headers are original copies, not synthesized contracts.
gen=out/'generated';gen.mkdir();header_rows=[]
for name,mod in seen.items():
 for hn in arr(mod['text'],'generated_headers'):
  rule=amods[hn];assert rule['kind']=='genrule'
  inputs=arr(rule['text'],'srcs');outputs=arr(rule['text'],'out');assert len(inputs)==len(outputs)
  for src,dest in zip(inputs,outputs):
   assert dest=='my_include_dir/'+src,(src,dest)
   source=absl/src;target=gen/dest;target.parent.mkdir(parents=True,exist_ok=True);data=source.read_bytes()
   if target.exists():assert target.read_bytes()==data
   else:target.write_bytes(data)
   header_rows.append({'module':hn,'source':str(source),'output':str(target),'sha256':hashlib.sha256(data).hexdigest()})
base=json.loads((r/'dist/aosp16/libinit-build-1/epoll-compile-clang21.json').read_text())['argv'];common=[x for x in base[:base.index('-c')] if x!='-O0'];profile=json.loads((r/'dist/aosp16/libinit-native-global-profile-1.json').read_text())['groups'];common+=sum((profile[n] for n in ['commonGlobalCflags','deviceGlobalCflags','commonGlobalCppflags','deviceGlobalCppflags']),[])+['-fno-rtti'];post=profile['noOverrideGlobalCflags']+profile['noOverride64GlobalCflags'];includes=['-I'+str(proto/'src'),'-I'+str(proto/'third_party/utf8_range'),'-I'+str(gen/'my_include_dir'),'-I'+str(absl)]
rows=[]
for name,mod in seen.items():
 flags=arr(mod['text'],'cflags')+arr(mod['text'],'cppflags')
 assert not arr(mod['text'],'defaults') or arr(mod['text'],'defaults')==['absl_defaults'],name
 for source in arr(mod['text'],'srcs'):rows.append((name,absl/source,flags))
flags=arr(pmods['protobuf-cflags-defaults']['text'],'cflags')
for source in arr(pmods['libprotobuf-cpp-lite-tlsagnostic-defaults']['text'],'srcs'):rows.append(('libprotobuf-cpp-lite',proto/source,flags))
assert len({str(p) for _,p,_ in rows})==len(rows)
state={'status':'running','pid_in_namespace':os.getpid(),'scope':'Original Android.bp module transitive source closure, selected platform clang/Bionic, serial prototype; not full Soong equivalence or service/APK acceptance','roots':roots,'abseil_modules':list(seen),'source_count':len(rows),'generated_headers':header_rows,'common_argv':common+includes,'results':[]};start=time.monotonic();(out/'state.json').write_text(json.dumps(state,indent=2)+'\n');print('modules',len(seen),'sources',len(rows),flush=True)
for i,(module,source,flags) in enumerate(rows):
 obj=out/'objects'/(str(i).zfill(3)+'-'+source.name+'.o');cmd=common+flags+post+includes
 if source.suffix=='.c':cmd=[x for x in cmd if not x.startswith('-std=') and x!='-nostdinc++' and x!='-fno-rtti'];cmd+=['-std=gnu23']
 cmd+=['-c',str(source),'-o',str(obj)];run=subprocess.run(cmd,capture_output=True,text=True,timeout=180);log=out/'logs'/(str(i).zfill(3)+'.log');log.write_text(run.stdout+run.stderr);row={'module':module,'source':str(source),'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'argv':cmd,'exit_code':run.returncode,'log':str(log)}
 if run.returncode==0:row.update(object=str(obj),object_sha256=hashlib.sha256(obj.read_bytes()).hexdigest())
 else:row['first_error']=next((line for line in run.stderr.splitlines() if 'error:' in line),run.stderr[:400])
 state['results'].append(row);(out/'state.json').write_text(json.dumps(state,indent=2)+'\n');print(i+1,len(rows),module,source.name,run.returncode,flush=True)
state.update(status='terminal',elapsed_seconds=time.monotonic()-start,all_compiled=all(x['exit_code']==0 for x in state['results']))
if state['all_compiled']:
 archive=out/'libprotobuf-lite-with-original-absl-prototype.a';subprocess.run(['ar','rcsD',str(archive)]+[x['object'] for x in state['results']],check=True);state.update(archive=str(archive),archive_sha256=hashlib.sha256(archive.read_bytes()).hexdigest())
(out/'state.json').write_text(json.dumps(state,indent=2)+'\n')
