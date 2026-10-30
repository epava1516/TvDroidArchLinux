from pathlib import Path
import subprocess,json,re,hashlib
r=Path('/home/tv/.cache/archtv/aosp-platform-33/verified-modules-1');out=Path('/home/tv/repositorio-principal/dist/apk/bionic-component-1');root=out/'root';proof=json.loads((r/'provenance.json').read_text());locations=[(r/'modules/com.android.art/payload.img','/lib64','/apex/com.android.art/lib64'),(r/'modules/com.android.runtime/payload.img','/lib64/bionic','/apex/com.android.runtime/lib64/bionic'),(r/'logical-system.img','/system/lib64','/system/lib64'),(r/'modules/com.android.i18n/payload.img','/lib64','/apex/com.android.i18n/lib64'),(r/'modules/com.android.conscrypt/payload.img','/lib64','/apex/com.android.conscrypt/lib64'),(r/'modules/com.android.os.statsd/payload.img','/lib64','/apex/com.android.os.statsd/lib64')];index={}
for image,directory,dest in locations:
 h=hashlib.file_digest(image.open('rb'),'sha256').hexdigest();assert h==proof['files'][str(image.relative_to(r))]['sha256']
 lines=subprocess.check_output(['debugfs','-R','ls -p '+directory,str(image)],text=True,stderr=subprocess.DEVNULL)
 for line in lines.splitlines():
  fields=line.split('/')
  if len(fields)>6 and fields[2].startswith('10') and fields[5].endswith('.so'):index.setdefault(fields[5],[]).append((image,directory,dest,h))
queue=['libart.so','libjavacore.so','libopenjdk.so','libopenjdkjvm.so','libicu_jni.so','libjavacrypto.so','libartpalette-system.so'];seen={};missing=[]
# Include dependencies of the actual VM launcher as well.
launcher=root/'apex/com.android.art/bin/dalvikvm64';data=subprocess.check_output(['readelf','-d',str(launcher)],text=True);queue+=re.findall(r'\(NEEDED\).*\[(.*?)\]',data)
while queue:
 name=queue.pop(0)
 if name in seen or name in missing:continue
 if name not in index:missing.append(name);continue
 image,directory,dest,imagehash=index[name][0];target=root/(dest+'/'+name).removeprefix('/');target.parent.mkdir(parents=True,exist_ok=True)
 if not target.exists():
  p=subprocess.run(['debugfs','-R',f'dump {directory}/{name} {target}',str(image)],capture_output=True,text=True);assert target.exists(),p.stderr
 data=subprocess.check_output(['readelf','-h','-d',str(target)],text=True);assert 'Advanced Micro Devices X86-64' in data
 needed=re.findall(r'\(NEEDED\).*\[(.*?)\]',data);queue+=needed
 seen[name]={'path':dest+'/'+name,'sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'bytes':target.stat().st_size,'needed':needed,'image_sha256':imagehash,'candidate_count':len(index[name])}
print('libraries',len(seen),'missing',missing,flush=True)
(out/'closure.json').write_text(json.dumps({'libraries':seen,'missing':missing,'search_paths':[x[2] for x in locations],'scope':'Static DT_NEEDED closure of launcher/ART/core JNI seeds, first explicit candidate per SONAME. Multiple candidates and dlopen/namespace/config/runtime behavior remain unproven. No host glibc or adapted JNI included.'},indent=2)+'\n')
