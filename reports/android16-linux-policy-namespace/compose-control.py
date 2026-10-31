from pathlib import Path
import json,re,hashlib,subprocess,time
root=Path('/home/tv/repositorio-principal');out=root/'dist/aosp16/policy-composition-control-1';out.mkdir(exist_ok=True)
paths={'aosp':root/'dist/aosp16/factory-inputs-3/root/system/etc/selinux/plat_sepolicy.cil','linux':root/'dist/aosp16/refpolicy-baseline-1/source/policy.cil'}
def forms(text):
 depth=0;start=None;result=[]
 for m in re.finditer(r'"(?:\\.|[^"\\])*"|;[^\n]*|[()]',text):
  ch=m[0]
  if ch=='(':
   if depth==0:start=m.start()
   depth+=1
  elif ch==')':
   depth-=1;assert depth>=0
   if depth==0:result.append(text[start:m.end()])
 assert depth==0
 return result
def key(s):return re.match(r'\(\s*([^\s()]+)',s)[1]
source={k:forms(p.read_text()) for k,p in paths.items()};classes=json.load(open(root/'reports/android16-linux-policy-namespace/proposed-class-union.json'))['classes'];globals=['(class '+k+' ('+' '.join(v)+'))' for k,v in classes.items()];globals+=['(classorder ('+' '.join(classes)+'))'];seen=set();local=[];counts={};dedup=[]
for name,statements in source.items():
 counts[name]={'original_statements':len(statements),'neverallow_statements':sum(key(x) in ('neverallow','neverallowx') for x in statements),'replaced_class_declarations':0,'retained':0}
 for form in statements:
  k=key(form)
  if k in ('class','common','classcommon','classorder'):
   counts[name]['replaced_class_declarations']+=1;continue
  if k in ('sensitivity','category','sid','sidorder','handleunknown','mls','policycap'):
   if form in seen:dedup.append({'source':name,'keyword':k,'statement':form});continue
   globals.append(form);seen.add(form)
  elif name=='aosp':globals.append(form)
  else:local.append(form)
  counts[name]['retained']+=1
output=out/'combined.cil';output.write_text('\n'.join(globals)+'\n(block linux\n'+'\n'.join(local)+'\n)\n');tool=root/'dist/aosp16/selinux-tools-host-4/source/secilc/secilc';cmd=['prlimit','--as=2147483648','--cpu=60','--',str(tool),'-m','-M','true','-G','-c','30','-o',str(out/'combined.bin'),'-f',str(out/'combined.fc'),str(output)];record={'scope':'Experimental source composition, Android names retained, Linux local namespace, explicit union expanded classes, identical global declarations deduplicated, all rules and assertions retained; no policy load','input_hashes':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()},'counts':counts,'deduplicated_globals':dedup,'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'argv':cmd};(out/'input.json').write_text(json.dumps(record,indent=2)+'\n');start=time.monotonic()
try:
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=90);record.update(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)
except subprocess.TimeoutExpired as e:record.update(exit_code=124,stdout=str(e.stdout),stderr=str(e.stderr),limitation='wall90 limit, not incompatibility proof')
record['elapsed_seconds']=time.monotonic()-start;(out/'results.json').write_text(json.dumps(record,indent=2)+'\n');print(record['exit_code'],record['stderr'][:2500],flush=True)
