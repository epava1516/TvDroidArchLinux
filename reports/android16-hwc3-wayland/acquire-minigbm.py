from pathlib import Path
import urllib.request,json,base64,hashlib,time
rev='b7c93249f685222a524c51403719493cc114ff5d';base='https://android.googlesource.com/platform/external/minigbm/+/'+rev+'/';out=Path('/home/tv/.cache/archtv/graphics-candidates-1/minigbm');trees={};rows=[]
def listing(folder):
 if folder not in trees:trees[folder]=json.loads(urllib.request.urlopen(base+folder+'?format=JSON',timeout=25).read()[4:])['entries']
 return trees[folder]
for directory in ['', 'cros_gralloc','cros_gralloc/aidl','cros_gralloc/mapper_stablec','cros_gralloc/gralloc4','external']:
 for e in listing(directory):
  if e['type']!='blob' or not(e['name'].endswith(('.c','.h','.cc','.cpp','.bp','.rc','.xml')) or e['name']=='LICENSE'):continue
  relative=(directory+'/' if directory else '')+e['name'];p=out/relative
  data=p.read_bytes() if p.exists() else base64.b64decode(urllib.request.urlopen(base+relative+'?format=TEXT',timeout=25).read());digest=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert digest==e['id'],relative;p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);rows.append({'path':relative,'git_blob':digest,'sha256':hashlib.sha256(data).hexdigest()})
  (out/'acquisition-progress.json').write_text(json.dumps({'revision':rev,'files_completed':len(rows),'last_path':relative,'terminal':False},indent=2)+'\n');time.sleep(.8)
 print('Verified group',directory or 'root',len(rows),flush=True)
(out/'allocator-source-inventory.json').write_text(json.dumps({'revision':rev,'files':rows,'scope':'Original selected complete core/AIDL allocator/stable-C mapper and gralloc4 helper sources, not execution or driver support'},indent=2)+'\n');print('SOURCE_CLOSURE_VERIFIED',len(rows),flush=True)
