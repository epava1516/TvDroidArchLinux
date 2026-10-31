from pathlib import Path
import re,json,hashlib
r=Path('/home/tv/repositorio-principal');ref=Path('/home/tv/.cache/archtv/refpolicy-review-1/source');aosp=r/'dist/aosp16/factory-inputs-3/root/system/etc/selinux/plat_sepolicy.cil';out=r/'dist/aosp16/policy-contract-comparison-2';out.mkdir();text=aosp.read_text();a={};commons={}
for match in re.finditer(r'^\((class|common) ([\w]+) \(([^()]*)\)\)',text,re.M):
 (a if match[1]=='class' else commons)[match[2]]=match[3].split()
for match in re.finditer(r'^\(classcommon (\w+) (\w+)\)',text,re.M):a[match[1]]=commons[match[2]]+a[match[1]]
avfile=ref/'policy/flask/access_vectors';av=re.sub(r'#[^\n]*','',avfile.read_text());b={};bc={}
tokens=re.findall(r'[A-Za-z_]\w*|[{}]',av);index=0
while index < len(tokens):
 kind=tokens[index];name=tokens[index+1];index+=2;assert kind in ['class','common'],(kind,name,index)
 inherited=None
 if index<len(tokens) and tokens[index]=='inherits':inherited=tokens[index+1];index+=2
 perms=[]
 if index<len(tokens) and tokens[index]=='{':
  index+=1
  while tokens[index]!='}':perms.append(tokens[index]);index+=1
  index+=1
 if kind=='common':assert not inherited;bc[name]=perms
 else:
  assert name not in b; b[name]=(bc[inherited] if inherited else [])+perms
class_file=ref/'policy/flask/security_classes';declared=set(re.findall(r'\bclass\s+(\w+)',re.sub(r'#[^\n]*','',class_file.read_text())))
assert set(b)==declared,{'missing':sorted(declared-set(b)),'extra':sorted(set(b)-declared)}
assert len(a)==len(re.findall(r'^\(class ',text,re.M))
assert a['binder'] and b['binder'];aattrs=set(re.findall(r'^\(typeattribute (\w+)\)',text,re.M));battrs={};sources=[]
for path in (ref/'policy').rglob('*'):
 if path.is_file() and path.suffix in ['.te','.if','.spt']:
  content=re.sub(r'#[^\n]*','',path.read_text(errors='strict'))
  for match in re.finditer(r'\battribute\s+(\w+)\s*;',content):battrs.setdefault(match[1],[]).append(str(path.relative_to(ref)))
shared=sorted(aattrs & battrs.keys());diff=[]
for name in sorted(a.keys() & b.keys()):
 if a[name]!=b[name]:diff.append({'class':name,'aosp_only':sorted(set(a[name])-set(b[name])),'refpolicy_only':sorted(set(b[name])-set(a[name])),'same_members':set(a[name])==set(b[name]),'order_equal':a[name]==b[name]})
result={'refpolicy_declared_class_coverage_complete':True,'scope':'Static literal class/common permission expansion and literal attribute declarations only; no policy merge, decisions or runtime semantics proved. Templates/macros/conditions are not a complete effective attribute inventory.','refpolicy_commit':'878b00a2db5b2ae490aa8cabb4b67ab19368f9d7','input_hashes':{'aosp_platform_cil':hashlib.sha256(aosp.read_bytes()).hexdigest(),'refpolicy_access_vectors':hashlib.sha256(avfile.read_bytes()).hexdigest()},'class_counts':{'aosp':len(a),'refpolicy':len(b)},'aosp_only_classes':sorted(a.keys()-b.keys()),'refpolicy_only_classes':sorted(b.keys()-a.keys()),'differing_shared_classes':diff,'android_service_contracts':{name:{'aosp':a.get(name),'refpolicy':b.get(name)} for name in ['binder','service_manager','hwservice_manager','property_service']},'shared_literal_attributes':{name:battrs[name] for name in shared},'full_expanded_class_inventories':{'aosp':a,'refpolicy':b}}
(out/'comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ['full_expanded_class_inventories','shared_literal_attributes']},indent=2));print('shared attributes',shared)
