from pathlib import Path
import urllib.request,json,base64,hashlib,time
rev='abd25312f278da5cbeeca6a9b5fc1c5ea6dabc23';base='https://android.googlesource.com/platform/external/libdrm/+/'+rev+'/';out=Path('/home/tv/.cache/archtv/graphics-candidates-1/libdrm');out.mkdir(exist_ok=True);rows=[]
for directory in ['', 'include/drm']:
 entries=json.loads(urllib.request.urlopen(base+directory+'?format=JSON',timeout=25).read()[4:])['entries']
 for e in entries:
  if e['type']!='blob' or not(e['name'].endswith('.h') or e['name'] in ['Android.bp','LICENSE','COPYING']):continue
  relative=(directory+'/' if directory else '')+e['name'];p=out/relative;data=p.read_bytes() if p.exists() else base64.b64decode(urllib.request.urlopen(base+relative+'?format=TEXT',timeout=25).read());h=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest();assert h==e['id'];p.parent.mkdir(parents=True,exist_ok=True);p.write_bytes(data);rows.append({'path':relative,'git_blob':h,'sha256':hashlib.sha256(data).hexdigest()});time.sleep(.8)
(out/'source-inventory.json').write_text(json.dumps({'revision':rev,'files':rows,'scope':'Original headers matched to selected GSI libdrm provider revision by manifest; no Soong binary equivalence or driver execution implied'},indent=2)+'\n');print('DRM_HEADERS_VERIFIED',len(rows),flush=True)
