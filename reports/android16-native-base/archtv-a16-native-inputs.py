from pathlib import Path
import subprocess,json,zipfile,hashlib
image=Path('/home/tv/.cache/archtv/aosp16-qpr2/artifact-selection/gsi-original/system.img');out=Path('/home/tv/repositorio-principal/dist/aosp16/native-inputs-1');out.mkdir(parents=True,exist_ok=False);commands=[]
def run(args):
 commands.append(list(map(str,args)));p=subprocess.run(args,capture_output=True,text=True,timeout=90);(out/'debugfs.log').open('a').write(p.stdout+p.stderr);p.check_returncode();return p.stdout
def dump(fs,source,dest):
 dest.parent.mkdir(parents=True,exist_ok=True);run(['debugfs','-R',f'dump {source} {dest}',str(fs)]);assert dest.is_file(),source
for module in ['com.android.runtime','com.android.art','com.android.i18n','com.android.conscrypt']:
 suffix='.capex' if module in ['com.android.art','com.android.conscrypt'] else '.apex';archive=out/'archives'/(module+suffix);dump(image,'/system/apex/'+module+suffix,archive)
 with zipfile.ZipFile(archive) as z:
  if suffix=='.capex':
   actual=archive.with_suffix('.original.apex');actual.write_bytes(z.read('original_apex'))
  else:actual=archive
 dest=out/'apex'/module;dest.mkdir(parents=True)
 with zipfile.ZipFile(actual) as z:
  (dest/'apex_manifest.json').write_bytes(z.read('apex_manifest.json'));payload=out/'archives'/(module+'.payload.img');payload.write_bytes(z.read('apex_payload.img'))
 run(['debugfs','-R',f'rdump / {dest}',str(payload)])
(out/'system').mkdir()
for directory in ['lib64','etc/classpaths','etc/selinux']:
 target=out/'system'/Path(directory).parent;target.mkdir(parents=True,exist_ok=True);run(['debugfs','-R',f'rdump /system/{directory} {target}',str(image)])
for source in ['/system/build.prop','/system/etc/public.libraries.txt','/system/etc/linker.config.pb','/system/bin/linker64','/system/bin/dalvikvm64','/system/bin/surfaceflinger','/init.environ.rc']:
 # dump only regular files, preserve links as evidence separately
 stat=run(['debugfs','-R','stat '+source,str(image)])
 if 'Type: regular' in stat:dump(image,source,out/source.lstrip('/'))
 else:(out/'symlinks.txt').open('a').write(source+'\n'+stat+'\n')
files={str(p.relative_to(out)):{'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()} for p in out.rglob('*') if p.is_file() and not p.is_symlink()}
(out/'provenance.json').write_text(json.dumps({'image_sha256':'c4989f703ac23bbd3bb3da2e33a3633d373bf763afcfcbed3cccc73d5049d656','commands':commands,'files':files,'scope':'Read-only debugfs extraction, ZIP CRC, original files; no mounts, boot, signature verification or app execution. Symlink entries are evidence, not blanket host access.'},indent=2)+'\n');print(out,len(files))
