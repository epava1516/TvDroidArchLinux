from pathlib import Path
import urllib.request,json,base64,hashlib
root=Path('/home/tv/.cache/archtv/graphics-candidates-1/hidl-generation-inputs');root.mkdir();commit='aa229558cbf04bc997ed27465c5e7ad497123d1b';base='https://android.googlesource.com/platform/hardware/interfaces/+/'+commit+'/';records=[]
for directory in ['', 'graphics/common/1.0','graphics/common/1.1','graphics/common/1.2','graphics/composer/2.1']:
 j=json.loads(urllib.request.urlopen(base+directory+'/?format=JSON',timeout=40).read()[4:])
 for e in j['entries']:
  if e['type']!='blob' or not (e['name'].endswith('.hal') or e['name']=='current.txt'):continue
  path=directory+'/'+e['name'] if directory else e['name'];d=base64.b64decode(urllib.request.urlopen(base+path+'?format=TEXT',timeout=40).read());assert hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()==e['id'];f=root/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(d);records.append({'path':path,'url':base+path+'?format=TEXT','git_blob':e['id'],'sha256':hashlib.sha256(d).hexdigest(),'git_blob_verified':True})
(root/'provenance.json').write_text(json.dumps({'commit':commit,'files':records},indent=2)+'\n');print('Verified original HAL/current inputs',len(records))
