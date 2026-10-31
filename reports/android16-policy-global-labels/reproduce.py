from pathlib import Path
import json,re,hashlib,subprocess,time,sys
root=Path('/home/tv/repositorio-principal');owner=sys.argv[1];assert owner in ('linux','aosp');out=root/('dist/aosp16/policy-global-label-owner-'+owner+'-1');out.mkdir(exist_ok=True)
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
source={k:forms(p.read_text()) for k,p in paths.items()}
def resource_key(form):
 k=key(form)
 if k=='genfscon':
  m=re.match(r'\(genfscon\s+(\S+)\s+(\"(?:\\.|[^\"\\])*\"|\S+)',form);assert m,form;return(k,m[1],m[2])
 if k=='fsuse':
  m=re.match(r'\(fsuse\s+(\S+)\s+(\S+)',form);assert m,form;return(k,m[2])
 return None
owned_resources={resource_key(f):f for f in source[owner] if resource_key(f) is not None}
replaced_resources=[]
classes=json.load(open(root/'reports/android16-linux-policy-namespace/proposed-class-union.json'))['classes'];globals=['(class '+k+' ('+' '.join(v)+'))' for k,v in classes.items()];globals+=['(classorder ('+' '.join(classes)+'))'];seen=set();local=[];counts={};dedup=[];replaced_sid_contexts=[]
for name,statements in source.items():
 counts[name]={'original_statements':len(statements),'neverallow_statements':sum(key(x) in ('neverallow','neverallowx') for x in statements),'replaced_class_declarations':0,'retained':0}
 for form in statements:
  k=key(form)
  rk=resource_key(form)
  if name!=owner and rk is not None and rk in owned_resources:
   replaced_resources.append({'source':name,'key':rk,'statement':form,'selected_owner_original_statement':owned_resources[rk]});continue
  if k=='sidcontext' and name!=owner:
   replaced_sid_contexts.append({'source':name,'statement':form,'selected_global_owner':owner});continue
  if k in ('class','common','classcommon','classorder'):
   counts[name]['replaced_class_declarations']+=1;continue
  if k in ('sensitivity','category','sid','sidorder','handleunknown','mls','policycap'):
   if form in seen:dedup.append({'source':name,'keyword':k,'statement':form});continue
   globals.append(form);seen.add(form)
  elif name=='aosp':globals.append(form)
  else:local.append(form)
  counts[name]['retained']+=1
output=out/'combined.cil';output.write_text('\n'.join(globals)+'\n(block linux\n'+'\n'.join(local)+'\n)\n');tool=root/'dist/aosp16/selinux-tools-host-4/source/secilc/secilc';cmd=['prlimit','--as=2147483648','--cpu=60','--',str(tool),'-m','-M','true','-G','-c','30','-o',str(out/'combined.bin'),'-f',str(out/'combined.fc'),str(output)];record={'scope':'Experimental source composition, Android names retained, Linux local namespace, explicit union expanded classes, identical global declarations deduplicated, all access rules and assertions retained; initial SID contexts and duplicate genfscon/fsuse keys explicitly selected from one owner as a hypothesis, not equivalence; no policy load','input_hashes':{k:hashlib.sha256(p.read_bytes()).hexdigest() for k,p in paths.items()},'counts':counts,'selected_initial_sid_owner':owner,'explicitly_replaced_resource_labels':replaced_resources,'explicitly_replaced_initial_sid_mappings':replaced_sid_contexts,'deduplicated_globals':dedup,'output_sha256':hashlib.sha256(output.read_bytes()).hexdigest(),'argv':cmd};(out/'input.json').write_text(json.dumps(record,indent=2)+'\n');start=time.monotonic()
try:
 p=subprocess.run(cmd,capture_output=True,text=True,timeout=90);record.update(exit_code=p.returncode,stdout=p.stdout,stderr=p.stderr)
except subprocess.TimeoutExpired as e:record.update(exit_code=124,stdout=str(e.stdout),stderr=str(e.stderr),limitation='wall90 limit, not incompatibility proof')
record['elapsed_seconds']=time.monotonic()-start;(out/'results.json').write_text(json.dumps(record,indent=2)+'\n');print(record['exit_code'],record['stderr'][:2500],flush=True)
