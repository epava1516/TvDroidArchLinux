from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/tv/repositorio-principal');inputs=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs');core=inputs/'system-core/source/system/core';base=core/'property_service';out=r/'dist/aosp16/property-libs-native-1';out.mkdir();(out/'objects').mkdir();d=json.loads((r/'dist/aosp16/libinit-build-1/epoll-compile-clang21.json').read_text());common=d['argv'][:d['argv'].index('-c')]+['-Wall','-Wextra','-Werror','-I'+str(base/'libpropertyinfoparser/include'),'-I'+str(base/'libpropertyinfoserializer/include')];commands=[];modules={'libpropertyinfoparser':['property_info_parser.cpp'],'libpropertyinfoserializer':['property_info_file.cpp','property_info_serializer.cpp','trie_builder.cpp','trie_serializer.cpp']}
for module,files in modules.items():
 flags=list(common)
 if module=='libpropertyinfoparser':
  # Original Android.bp stl:none: remove both libc++ include directories.
  i=0
  while i<len(flags):
   if flags[i]=='-isystem' and ('/c++/v1' in flags[i+1]):del flags[i:i+2]
   else:i+=1
 objects=[]
 for name in files:
  source=base/module/name;obj=out/'objects'/(module+'-'+name+'.o');argv=flags+['-c',str(source),'-o',str(obj)];p=subprocess.run(argv,text=True,capture_output=True);commands.append({'argv':argv,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()});(out/'commands.json').write_text(json.dumps(commands,indent=2)+'\n');print(module,name,p.returncode,flush=True)
  if p.returncode:raise SystemExit(p.stderr)
  objects.append(str(obj))
 archive=out/(module+'.a');subprocess.run(['ar','rcs',str(archive),*objects],check=True)
(out/'validation.json').write_text(json.dumps({'modules':modules,'original_source_modified':False,'selected_original_clang21':True,'original_Bionic_platform_headers':True,'parser_stl_none_preserved':True,'archive_sha256':{module:hashlib.sha256((out/(module+'.a')).read_bytes()).hexdigest() for module in modules},'scope':'Two complete original static module source sets compiled for Bionic; no link/run/property-service/SELinux/APK acceptance'},indent=2)+'\n');print('Both original native property-info archives built')
