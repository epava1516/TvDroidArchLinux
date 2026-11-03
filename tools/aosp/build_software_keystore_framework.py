#!/usr/bin/env python3
"""Experimental full-original framework DEX profile, not a source rebuild.

Apply the four source-reviewed default selections, preserving instruction sizes,
all class identities and every other original JAR entry. No SDK implementations.
This artifact is not accepted until original Java crypto and negatives execute.
"""
from pathlib import Path
import hashlib,json,subprocess,sys,zipfile,zlib,struct
ROOT=Path(__file__).resolve().parents[2]
out=(ROOT/sys.argv[1]).resolve();out.mkdir()
original=ROOT/'dist/aosp16/factory-inputs-3/root/system/framework/framework.jar'
engine=Path('/home/tv/.local/share/rea/android/jadx-headless-mcp-0.7.1-all.jar')
source=ROOT/'tools/aosp/KeystoreFrameworkProfilePlan.java'
patch=ROOT/'runtime/aosp/android16-qpr2/patches/framework-keystore-linux-software.patch'
base=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/framework-keystore-original')
provenance=json.loads((base/'provenance.json').read_text())
assert provenance['commit']=='45034f0663f960d9ee5fb0a101a4732b71f6e2f4'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
commands=[]
def run(a):
 q=subprocess.run(a,capture_output=True,text=True);commands.append({'argv':list(map(str,a)),'exit':q.returncode,'stderr':q.stderr})
 assert q.returncode==0,q.stderr
 return q.stdout
run(['javac','-cp',str(engine),'-d',str(out),str(source)])
plan=[json.loads(l) for l in run(['java','-Xmx768m','-cp',str(engine)+':'+str(out),'KeystoreFrameworkProfilePlan',str(original)]).splitlines()]
assert len(plan)==4 and {p['dex'] for p in plan}=={'classes3.dex'}
assert len({p['offset'] for p in plan})==4
source_hashes={}
for name,count in [('AndroidKeyStoreKeyGeneratorSpi.java',1),('AndroidKeyStoreKeyPairGeneratorSpi.java',1),('AndroidKeyStoreSpi.java',2)]:
 p=base/'source/frameworks/base/keystore/java/android/security/keystore2'/name
 assert p.read_text().count('SecurityLevel.TRUSTED_ENVIRONMENT')==count
 source_hashes[str(p)]=sha(p)
entries=[]
with zipfile.ZipFile(original) as inp,zipfile.ZipFile(out/'framework.jar','w') as target:
 for info in inp.infolist():
  data=inp.read(info.filename);before=hashlib.sha256(data).hexdigest()
  if info.filename=='classes3.dex':
   old=data;changed=bytearray(data);allowed=set(range(8,32))
   for p in plan:
    at=p['offset'];a=bytes.fromhex(p['before']);b=bytes.fromhex(p['after'])
    assert len(a)==len(b) and data[at:at+len(a)]==a
    changed[at:at+len(a)]=b;allowed.update(range(at,at+len(a)))
   changed[12:32]=hashlib.sha1(changed[32:]).digest()
   struct.pack_into('<I',changed,8,zlib.adler32(changed[12:])&0xffffffff)
   delta={i for i,(a,b) in enumerate(zip(old,changed)) if a!=b}
   assert delta<=allowed and len(old)==len(changed)
   data=bytes(changed)
   assert data[12:32]==hashlib.sha1(data[32:]).digest()
   assert struct.unpack_from('<I',data,8)[0]==zlib.adler32(data[12:])&0xffffffff
  # ART directly mmaps uncompressed DEX only at an aligned file offset.
  # Preserve contents; align via a ZIP extra field, never by editing DEX again.
  if info.filename.endswith('.dex'):
   assert info.compress_type==zipfile.ZIP_STORED
   start=target.fp.tell()+30+len(info.filename.encode('utf-8'))+len(info.extra)
   padding=(-start)%4
   if padding:info.extra+=struct.pack('<HH',0xd935,padding)+bytes(padding)
  target.writestr(info,data)
  entries.append({'name':info.filename,'before_sha256':before,'after_sha256':hashlib.sha256(data).hexdigest()})
alignment=[]
raw=(out/'framework.jar').read_bytes()
with zipfile.ZipFile(out/'framework.jar') as z:
 for info in z.infolist():
  if info.filename.endswith('.dex'):
   filename_length,extra_length=struct.unpack_from('<HH',raw,info.header_offset+26)
   data_offset=info.header_offset+30+filename_length+extra_length
   assert data_offset%4==0
   alignment.append({'name':info.filename,'offset':data_offset,'aligned4':True})
assert [e['name'] for e in entries if e['before_sha256']!=e['after_sha256']]==['classes3.dex']
record={'scope':'Experimental binary profile of complete original framework; not source rebuild or Java execution acceptance','original':{'path':str(original),'sha256':sha(original)},'output':{'path':str(out/'framework.jar'),'sha256':sha(out/'framework.jar')},'plan':plan,'entries':entries,'alignment':alignment,'builder_sha256':sha(Path(__file__)),'source_pin':provenance['commit'],'original_sources_sha256':source_hashes,'source_patch_sha256':sha(patch),'engine_sha256':sha(engine),'planner_sha256':sha(source),'commands':commands,'limits':['Full source rebuild pending; source/DEX correspondence scoped to four selections','All class tables and other instructions byte-identical; ART boot-image coherence must be tested','StrongBox branches retained; hardware metadata/attestation/authentication not fabricated','No JCA, user unlock or Markor result from this build']}
(out/'build.json').write_text(json.dumps(record,indent=2)+'\n');print(out)
