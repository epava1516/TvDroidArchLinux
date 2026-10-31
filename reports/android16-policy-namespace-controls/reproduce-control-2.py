from pathlib import Path
import subprocess,json,hashlib,time,re
root=Path('/home/tv/repositorio-principal');out=root/'dist/aosp16/policy-namespace-control-2';out.mkdir(exist_ok=True)
inputs={'aosp':root/'dist/aosp16/factory-inputs-3/root/system/etc/selinux/plat_sepolicy.cil','linux':root/'dist/aosp16/refpolicy-baseline-1/source/policy.cil'};tool=root/'dist/aosp16/selinux-tools-host-4/source/secilc/secilc';rows=[]
for name,path in inputs.items():
 text=path.read_text();forms=[];depth=0;start=None;quote=False;escape=False;comment=False
 for i,ch in enumerate(text):
  if comment:
   if ch=='\n':comment=False
   continue
  if quote:
   if escape:escape=False
   elif ch=='\\':escape=True
   elif ch=='"':quote=False
   continue
  if ch==';':comment=True
  elif ch=='"':quote=True
  elif ch=='(':
   if depth==0:start=i
   depth+=1
  elif ch==')':
   depth-=1
   assert depth>=0
   if depth==0:forms.append(text[start:i+1])
 assert depth==0 and not quote
 global_forms=[];local=[]
 for form in forms:
  keyword=re.match(r'\(\s*([^\s()]+)',form)[1]
  (global_forms if keyword in ('sensitivity','category') else local).append(form)
 dst=out/(name+'.cil');dst.write_text('\n'.join(global_forms)+'\n(block '+name+'\n'+'\n'.join(local)+'\n)\n')
 cmd=['prlimit','--as=2147483648','--cpu=20','--',str(tool),'-m','-M','true','-G','-c','30','-o',str(out/(name+'.bin')),'-f',str(out/(name+'.fc')),str(dst)]
 starttime=time.monotonic()
 try:p=subprocess.run(cmd,capture_output=True,text=True,timeout=25)
 except subprocess.TimeoutExpired as exc:
  p=subprocess.CompletedProcess(cmd,124,(exc.stdout or b'').decode(),(exc.stderr or b'').decode()+'\nObservation: wall-time limit25s reached; no compilation conclusion')
 row={'name':name,'input_sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'output_cil_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'top_level_statements':len(forms),'hoisted_statements':len(global_forms),'retained_statements':len(local),'argv':cmd,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'elapsed_seconds':time.monotonic()-starttime};rows.append(row);print(name,p.returncode,p.stderr[:1600],flush=True)
(out/'results.json').write_text(json.dumps({'scope':'Experimental namespace relocation, only sensitivity/category declarations hoisted; not policy selected or loaded','results':rows},indent=2)+'\n')
