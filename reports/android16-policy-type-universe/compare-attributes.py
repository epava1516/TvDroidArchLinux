from pathlib import Path
import re,json,hashlib,subprocess
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/policy-binary-projection-2';combined=r/'dist/aosp16/policy-type-universe-linux-2';result=json.load(open(combined/'results.json'));assert result['exit_code']==0,'Require original compiler success, no partial binary'
cmd=[str(r/'dist/aosp16/checkpolicy-host-2/source/checkpolicy'),'-M','-b','-C','-o',str(out/'combined.cil'),str(combined/'combined.bin')];p=subprocess.run(cmd,capture_output=True,text=True,timeout=30);assert p.returncode==0,p.stderr
def inventory(path):
 text=path.read_text();types=set(re.findall(r'^\(type (\S+)\)$',text,re.M));attributes={x:set() for x in re.findall(r'^\(typeattribute (\S+)\)$',text,re.M)};sets=re.findall(r'^\(typeattributeset (\S+) \(([^()]*)\)\)$',text,re.M);assert len(sets)==len(re.findall(r'^\(typeattributeset ',text,re.M))
 for attr,values in sets:
  assert attr in attributes;members=set(values.split());assert members<=types,(attr,members-types);attributes[attr]|=members
 return types,attributes
ct,ca=inventory(out/'combined.cil');rows=[]
for name,prefix in [('aosp',''),('linux','linux.')]:
 types,attrs=inventory(out/(name+'.cil'));expectedtypes={prefix+t for t in types};missingtypes=expectedtypes-ct;differences=[]
 for attr,members in attrs.items():
  key=prefix+attr;expected={prefix+t for t in members};actual=ca.get(key);missing=actual is None
  if missing or actual!=expected:differences.append({'attribute':attr,'missing':missing,'lost':sorted(expected-(actual or set())),'gained':sorted((actual or set())-expected)})
 rows.append({'policy':name,'original_types':len(types),'original_binary_attributes':len(attrs),'missing_types':sorted(missingtypes),'attribute_differences':differences,'all_binary_attribute_memberships_identical_under_prefix':not missingtypes and not differences})
record={'scope':'All retained binary attribute memberships and concrete type names compared through original compiler export; NOT full access/constraints/transition equivalence, live enforcement, boot/services/APK proof','combined_export_argv':cmd,'inputs':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in [out/'aosp.cil',out/'linux.cil',out/'combined.cil',combined/'combined.bin']},'results':rows};(out/'attribute-comparison.json').write_text(json.dumps(record,indent=2)+'\n')
for row in rows:print(row['policy'],row['all_binary_attribute_memberships_identical_under_prefix'],len(row['attribute_differences']))
