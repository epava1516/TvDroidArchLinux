from pathlib import Path
import urllib.request,json,hashlib,base64,time,sys
cache=Path('/home/tv/.cache/archtv/graphics-candidates-1')
for name,rev,dirs,files in [('wayland','bdb389207f7113c752e8e6fee1c2897168ba473b',['src'],['Android.bp','config.h','COPYING','LICENSE','protocol/wayland.xml','protocol/wayland.dtd']),('libffi','30e76ea6cdd84cbbaa5dd5e5bbfce29538328fb4',['include','linux-x86','src/x86'],['Android.bp','linux-x86_64','LICENSE','LICENSE-BUILDTOOLS','gen_ffi_header.sh','src/closures.c','src/debug.c','src/java_raw_api.c','src/prep_cif.c','src/raw_api.c','src/types.c'])]:
 if len(sys.argv)>1 and name!=sys.argv[1]:continue
 out=cache/name;out.mkdir(exist_ok=True);base='https://android.googlesource.com/platform/external/'+name+'/+/'+rev+'/';rows=[];trees={}
 def listing(p):
  if p not in trees:trees[p]=json.loads(urllib.request.urlopen(base+p+'?format=JSON',timeout=25).read()[4:])['entries']
  return trees[p]
 def get(p):
  parent,_,filename=p.rpartition('/');e=next(e for e in listing(parent) if e['name']==filename);dest=out/p
  if dest.is_symlink():b=dest.readlink().as_posix().encode()
  elif dest.exists():b=dest.read_bytes()
  else:
   b=base64.b64decode(urllib.request.urlopen(base+p+'?format=TEXT',timeout=25).read());time.sleep(.8)
  h=hashlib.sha1(b'blob '+str(len(b)).encode()+b'\0'+b).hexdigest();assert h==e['id'],p;dest.parent.mkdir(parents=True,exist_ok=True);
  if not dest.is_symlink():dest.write_bytes(b)

  if e['mode']==40960:
   target=b.decode();assert target=='linux-x86' and p=='linux-x86_64';dest.unlink();dest.symlink_to(target)
  rows.append({'path':p,'git_blob':h,'sha256':hashlib.sha256(b).hexdigest()})
 for folder in dirs:
  for e in listing(folder):
   if e['type']=='blob':get(folder+'/'+e['name'])
 for p in files:get(p)
 (out/'source-inventory.json').write_text(json.dumps({'project':'platform/external/'+name,'revision':rev,'files':rows,'scope':'Selected complete Android.bp client/x86_64 implementation source closure; not all project sources or execution'},indent=2)+'\n');print(name,'verified',len(rows),'files',flush=True)
