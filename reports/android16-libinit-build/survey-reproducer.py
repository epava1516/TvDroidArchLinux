from pathlib import Path
import json,re,subprocess,time,hashlib
repo=Path('/home/tv/repositorio-principal');inputs=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs');init=inputs/'init-2/source/system/core/init';out=repo/'dist/aosp16/libinit-survey-1';out.mkdir();(out/'objects').mkdir();(out/'logs').mkdir()
old=json.loads((repo/'dist/aosp16/libinit-build-1/epoll-compile-2.json').read_text());common=old['argv'][:old['argv'].index('-c')];common=[a for a in common if a!='-D__ANDROID_APEX__=0'];common[common.index('-std=gnu++23')]='-std=gnu++20'
bp=(init/'Android.bp').read_text();groups={n:re.findall(r'"([^"]+)"',re.search(r'^'+n+r' = \[(.*?)\n\]',bp,re.M|re.S).group(1)) for n in ['init_common_sources','init_device_sources']}
files=[x for xs in groups.values() for x in xs if x.endswith('.cpp')];result={'source_groups':groups,'compiler':subprocess.check_output(['clang++','--version'],text=True),'common_argv':common,'scope':'Whole declared libinit source-set build survey only; hostclang23 vs selected21, incomplete include/generated/product flags. Not Soong equivalence, no link, no execution or subsystem/API acceptance. Original files unchanged. No source omitted from survey.','results':[]}
for i,name in enumerate(files):
 argv=common+['-c',str(init/name),'-o',str(out/'objects'/(name+'.o'))];start=time.monotonic()
 try:
  p=subprocess.run(argv,text=True,capture_output=True,timeout=90);(out/'logs'/(name+'.log')).write_text(p.stdout+p.stderr);row={'source':name,'source_sha256':hashlib.sha256((init/name).read_bytes()).hexdigest(),'exit_code':p.returncode,'seconds':round(time.monotonic()-start,3),'log':'logs/'+name+'.log'}
  if p.returncode==0:row['object_sha256']=hashlib.sha256((out/'objects'/(name+'.o')).read_bytes()).hexdigest()
  else:row['first_fatal_error']=next((s for s in p.stderr.splitlines() if 'fatal error:' in s),'See original log')
 except subprocess.TimeoutExpired as e:
  (out/'logs'/(name+'.log')).write_bytes((e.stdout or b'')+(e.stderr or b''));row={'source':name,'timeout':90,'log':'logs/'+name+'.log'}
 result['results'].append(row);(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(i+1,len(files),name,row.get('exit_code','timeout'),flush=True)
print('Survey terminal',flush=True)
