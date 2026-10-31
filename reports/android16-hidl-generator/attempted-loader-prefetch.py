import urllib.request,json,base64,hashlib
from pathlib import Path
out=Path('/home/tv/.cache/archtv/graphics-candidates-1/aosp-interfaces');commit='aa229558cbf04bc997ed27465c5e7ad497123d1b';base='https://android.googlesource.com/platform/hardware/interfaces/+/'+commit+'/';records=[]
def fetch_tree(path,depth=0):
 assert depth<8
 j=json.loads(urllib.request.urlopen(base+path+'/?format=JSON',timeout=40).read()[4:])
 for e in j['entries']:
  name=path+'/'+e['name']
  if e['type']=='tree':fetch_tree(name,depth+1)
  elif e['mode']==33188 and (e['name'].endswith(('.h','.cpp','.bp','.rc','.xml'))):
   d=base64.b64decode(urllib.request.urlopen(base+name+'?format=TEXT',timeout=40).read());assert hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()==e['id'];f=out/name;f.parent.mkdir(parents=True,exist_ok=True);assert not f.exists();f.write_bytes(d);records.append({'path':name,'url':base+name+'?format=TEXT','git_blob':e['id'],'sha256':hashlib.sha256(d).hexdigest(),'git_blob_verified':True})
for root in ['graphics/composer/2.1/default','graphics/composer/2.1/utils/hal','graphics/composer/2.1/utils/command-buffer','graphics/composer/2.1/utils/resources','graphics/composer/2.1/utils/hwc2onfbadapter']:fetch_tree(root)
(out/'loader-source-provenance.json').write_text(json.dumps({'commit':commit,'files':records},indent=2)+'\n');print('Original loader/source files verified',len(records))
