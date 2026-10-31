#!/usr/bin/env python3
"""Pinned factory filesystem inputs for component research, not an Android installer.

Whole original modules are retained. Derived APEX selection XML is not apexd or
signature validation; copied ownership metadata is not security acceptance.
"""
from pathlib import Path
import subprocess,zipfile,shutil,json,hashlib,re,struct,xml.etree.ElementTree as E,time
import argparse
parser=argparse.ArgumentParser(description='Prepare pinned AOSP16 GSI system/APEX research inputs; never mount or boot Android.')
parser.add_argument('--image',type=Path,required=True)
parser.add_argument('--output',type=Path,required=True)
args=parser.parse_args()
repo=Path(__file__).resolve().parents[2];image=args.image.resolve();out=args.output.resolve()
if not re.fullmatch(r'[A-Za-z0-9_./+-]+',str(out)):raise SystemExit('Unsupported output path')
out.parent.mkdir(parents=True,exist_ok=True)
if shutil.disk_usage(out.parent).free < image.stat().st_size*3:raise SystemExit('Insufficient staging space; use a disk with at least three image sizes free, not the small tmpfs')
expected=json.loads((repo/'runtime/aosp/android16-qpr2/release.json').read_text())['compiled_artifacts']['system_image_sha256']
if out.exists():raise SystemExit('Output must be new')
commands=[];start=time.monotonic()
def digest(p):
 with p.open('rb') as f:return hashlib.file_digest(f,'sha256').hexdigest()
if digest(image)!=expected:raise SystemExit('Pinned image SHA256 mismatch')
out.mkdir(exist_ok=False);root=out/'root';root.mkdir(exist_ok=False)
def run(args):
 commands.append(list(map(str,args)));p=subprocess.run(list(map(str,args)),capture_output=True,text=True,timeout=180);(out/'debugfs.log').open('a').write(p.stdout+p.stderr);p.check_returncode()
 errors=[line for line in p.stderr.splitlines() if line.startswith(('rdump:','dump:','debugfs:')) and 'while changing ownership of' not in line]
 if errors:raise RuntimeError('debugfs reported extraction errors: '+str(errors[:5]))
 return p.stdout
def varint(data,i):
 n=0
 for shift in range(0,70,7):
  if i>=len(data):raise ValueError('Truncated varint')
  v=data[i];i+=1;n|=(v&127)<<shift
  if not v&128:return n,i
 raise ValueError('Varint overflow')
def fields(data):
 assert len(data)<=1048576;i=0
 while i<len(data):
  key,i=varint(data,i);n,w=key>>3,key&7;assert n
  if w==0:v,i=varint(data,i)
  elif w==2:
   size,i=varint(data,i);assert size<=len(data)-i;v=data[i:i+size];i+=size
  else:raise ValueError('Unsupported manifest wire type')
  yield n,w,v
def manifest(data):
 identity={}
 for n,w,v in fields(data):
  if n in [1,5] and w==2:
   assert n not in identity;identity[n]=v.decode()
  elif n in [2,11] and w==0:
   assert n not in identity;identity[n]=v
 assert 1 in identity and 2 in identity
 assert re.fullmatch('[A-Za-z0-9_.-]+',identity[1]) and '..' not in identity[1]
 return identity
for directory in ['apex','dev','proc','tmp','data','linkerconfig','vendor','probe']:(root/directory).mkdir()
run(['debugfs','-R',f'rdump /system {root}',image]);assert (root/'system/etc/linker.config.pb').is_file()
for path in ['product','system_ext']:
 text=run(['debugfs','-R','stat /'+path,image]);link=re.search(r'Fast link dest: "([^"]+)"',text);assert link;target=link.group(1);assert target.startswith('/system/');(root/path).symlink_to(target)
modules=[];archives=sorted((root/'system/apex').glob('*'))
assert len(archives)==36
tree=E.Element('apex-info-list');names=set()
for archive in archives:
 assert archive.suffix in ['.apex','.capex'];actual=archive
 with zipfile.ZipFile(archive) as z:
  if archive.suffix=='.capex':
   actual=out/(archive.stem+'.original.apex')
   with z.open('original_apex') as src,actual.open('xb') as dst:shutil.copyfileobj(src,dst,1024*1024)
 with zipfile.ZipFile(actual) as z:
  raw=z.read('apex_manifest.pb');m=manifest(raw);name=m[1];assert name not in names;names.add(name);dest=root/'apex'/name;dest.mkdir()
  payload=out/(name+'.payload.img')
  with z.open('apex_payload.img') as src,payload.open('xb') as dst:shutil.copyfileobj(src,dst,1024*1024)
  run(['debugfs','-R',f'rdump / {dest}',payload]);assert (dest/'apex_manifest.pb').read_bytes()==raw
  original='/system/apex/'+archive.name
  E.SubElement(tree,'apex-info',{'moduleName':name,'modulePath':original,'preinstalledModulePath':original,'versionCode':str(m[2]),'versionName':m.get(5,''),'isFactory':'true','isActive':'true','provideSharedApexLibs':str(bool(m.get(11,0))).lower(),'partition':'SYSTEM'})
  modules.append({'name':name,'version':m[2],'archive':original,'archive_sha256':digest(archive),'manifest_sha256':hashlib.sha256(raw).hexdigest(),'payload_sha256':digest(payload),'scope':'Original factory module selected in derived research filesystem; not apexd signature/activation/update verification'})
 print('Extracted',name,flush=True)
E.indent(tree);E.ElementTree(tree).write(root/'apex/apex-info-list.xml',encoding='utf-8',xml_declaration=True)
files={}
for p in root.rglob('*'):
 if p.is_file() and not p.is_symlink():files[str(p.relative_to(root))]={'bytes':p.stat().st_size,'sha256':digest(p)}
result={'input_image_sha256':digest(image),'root':str(root),'modules':modules,'files':files,'commands':commands,'derived_apex_info_sha256':digest(root/'apex/apex-info-list.xml'),'seconds':time.monotonic()-start,'scope':'Read-only debugfs extraction and ZIP CRC of exact GSI; full original system inputs plus unmodified APEX payloads. Derived XML factory selection is declared for this filesystem, not apexd execution, signature/security acceptance, Android boot or APK coverage. No host system installation.'}
(out/'provenance.json').write_text(json.dumps(result,indent=2)+'\n');print('COMPLETE',len(modules),len(files),flush=True)
