from pathlib import Path
import urllib.request,json,base64,hashlib,concurrent.futures
root=Path('/home/tv/.cache/archtv/aosp16-qpr2/surfaceflinger-study-1');root.mkdir(exist_ok=True);commit='fcbde2bcff56ca1d7bec9cabf8bdca5e288bf103';base='https://android.googlesource.com/platform/frameworks/native/+/'+commit+'/'
paths=['services/surfaceflinger/main_surfaceflinger.cpp','services/surfaceflinger/SurfaceFlinger.cpp','services/surfaceflinger/DisplayHardware/HWComposer.cpp','services/surfaceflinger/DisplayHardware/AidlComposerHal.cpp','services/surfaceflinger/DisplayHardware/HidlComposerHal.cpp','services/surfaceflinger/DisplayHardware/ComposerHal.cpp','services/surfaceflinger/Android.bp']
dirs={}
for path in sorted({p.rsplit('/',1)[0] for p in paths}):
 data=urllib.request.urlopen(base+path+'/?format=JSON',timeout=40).read();dirs[path]=json.loads(data[4:]);(root/(path.replace('/','__')+'-directory.json')).write_text(json.dumps(dirs[path],indent=2)+'\n')
def fetch(path):
 e=next(x for x in dirs[path.rsplit('/',1)[0]]['entries'] if x['name']==path.rsplit('/',1)[1]);assert e['mode']==33188
 url=base+path+'?format=TEXT';d=base64.b64decode(urllib.request.urlopen(url,timeout=40).read());assert hashlib.sha1(b'blob '+str(len(d)).encode()+b'\0'+d).hexdigest()==e['id'];f=root/path;f.parent.mkdir(parents=True,exist_ok=True);f.write_bytes(d);return {'path':path,'url':url,'sha256':hashlib.sha256(d).hexdigest(),'git_blob':e['id'],'git_blob_verified':True}
with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool: rows=list(pool.map(fetch,paths))
(root/'provenance.json').write_text(json.dumps({'commit':commit,'files':rows},indent=2)+'\n');print('Verified',len(rows),'original AOSP files')
