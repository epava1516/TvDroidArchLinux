import json,sys
from pathlib import Path
# Bounded decoder for packages/modules/common/proto/classpaths.proto, Android 13.
def varint(b,i):
 n=0
 for shift in range(0,70,7):
  if i>=len(b):raise ValueError('Truncated varint')
  v=b[i];i+=1;n|=(v&127)<<shift
  if v<128:return n,i
 raise ValueError('Varint overflow')
def fields(b):
 if len(b)>1048576:raise ValueError('Fragment too large')
 i=0
 while i<len(b):
  key,i=varint(b,i);num,wire=key>>3,key&7
  if num==0:raise ValueError('Zero field')
  if wire==0:v,i=varint(b,i)
  elif wire==2:
   size,i=varint(b,i)
   if size>len(b)-i:raise ValueError('Truncated field')
   v=b[i:i+size];i+=size
  else:raise ValueError('Unsupported field wire type')
  yield num,wire,v
def decode(p):
 out=[]
 for num,wire,b in fields(p.read_bytes()):
  if (num,wire)!=(1,2):raise ValueError('Unknown top level field')
  item={}
  for n,w,v in fields(b):
   if n in (1,3,4) and w==2:item[{1:'path',3:'min_sdk_version',4:'max_sdk_version'}[n]]=v.decode('utf-8')
   elif n==2 and w==0:item['classpath']=v
   else:raise ValueError('Unknown Jar field')
  out.append(item)
 return out
def inventory(system, modules, sdk):
 import hashlib,zipfile
 from apk_inventory import dex_inventory
 fragments=[modules/'com.android.art/etc/classpaths/bootclasspath.pb',system/'classpaths/bootclasspath.pb']
 fragments+=sorted(p for p in modules.glob('*/etc/classpaths/bootclasspath.pb') if p not in fragments)
 jars=[];excluded=[];seen=set()
 for fragment in fragments:
  if not fragment.is_file():raise ValueError('Missing fragment: '+str(fragment))
  for jar in decode(fragment):
   if jar.get('classpath')!=1:continue
   path=jar['path']
   if path in seen:raise ValueError('Duplicate boot jar: '+path)
   seen.add(path)
   for key in ['min_sdk_version','max_sdk_version']:
    if jar.get(key) and not jar[key].isdigit():raise ValueError('Unsupported codename bound: '+jar[key])
   if int(jar.get('min_sdk_version','0'))>sdk or int(jar.get('max_sdk_version',str(sdk)))<sdk:
    excluded.append(jar);continue
   if path.startswith('/system/framework/'):
    local=system/'framework'/path.removeprefix('/system/framework/')
   elif path.startswith('/apex/'):
    local=modules/path.removeprefix('/apex/')
    if fragment.parent.parent.parent!=modules/path.split('/')[2] and fragment!=system/'classpaths/bootclasspath.pb':raise ValueError('Cross-module export')
   else:raise ValueError('Unsupported boot jar path')
   if '..' in Path(path).parts or not local.is_file():raise ValueError('Missing or unsafe jar: '+path)
   types=set();defined=set();dex=[]
   with zipfile.ZipFile(local) as z:
    for name in z.namelist():
     if name.endswith('.dex'):
      t,d,_=dex_inventory(z.read(name));types|=t;defined|=d;dex.append(name)
   if not dex:raise ValueError('No executable DEX: '+path)
   jars.append({**jar,'local_path':str(local.resolve()),'sha256':hashlib.sha256(local.read_bytes()).hexdigest(),'bytes':local.stat().st_size,'dex':dex,'defined_types':len(defined),'defines_tethering_manager':'Landroid/net/TetheringManager;' in defined})
 return {'sdk':sdk,'boot_jars':jars,'excluded_sdk_bounds':excluded,'fragments':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in fragments},'scope':'Original metadata ordering ART/system/sorted APEX; BOOTCLASSPATH only, numeric API bounds. DEX identities are static evidence, not runtime or member compatibility. Unknown schema/codename/path fails explicitly.'}
if __name__=='__main__':
 import argparse
 p=argparse.ArgumentParser(description='Inspect original Android 13 classpath fragments and executable DEX jars without booting Android.')
 p.add_argument('--system',type=Path,required=True);p.add_argument('--modules',type=Path,required=True);p.add_argument('--sdk',type=int,required=True);p.add_argument('--output',type=Path,required=True);a=p.parse_args()
 if a.output.exists():raise SystemExit('Output must be new')
 a.output.write_text(json.dumps(inventory(a.system,a.modules,a.sdk),indent=2)+'\n')
