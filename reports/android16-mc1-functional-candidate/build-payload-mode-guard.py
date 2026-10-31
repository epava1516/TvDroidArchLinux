from pathlib import Path
import json,re,shutil,subprocess,hashlib
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-mc1-functional-candidate';out=r/'dist/aosp16/mc1-functional-candidate-5';tree=out/'payload-tree-2';tree.mkdir()
for name in ['bin','lib']:(tree/name).mkdir(mode=0o700)
entries={};commands=[]
def record(path,source,context,mode):
 dest=tree/path.lstrip('/')
 if source:shutil.copyfile(source,dest);dest.chmod(mode)
 entries[path]={'source':str(source) if source else None,'context':context,'uid':0,'gid':0,'mode':oct(mode),'sha256':hashlib.sha256(dest.read_bytes()).hexdigest() if source else None}
ld='linux.system_u:linux.object_r:'
for name in ['/','/bin','/lib']:record(name,None,ld+'archtv_bundle_dir:s0',0o700)
record('/bin/native-supervisor',out/'cargo/debug/examples/native_supervisor',ld+'archtv_launcher_exec:s0',0o700)
record('/bin/linux-exec-context',out/'linux-exec-context-image',ld+'archtv_exec_context_exec:s0',0o700)
record('/bin/property-coordinator',out/'property-coordinator','u:object_r:init_exec:s0',0o700)
queue=[tree/'bin/native-supervisor',tree/'bin/linux-exec-context'];needed={'ld-linux-x86-64.so.2'};inspected=set();dynamic=[]
while queue or needed:
 if needed:
  name=needed.pop()
  if '/lib/'+name in entries:continue
  if Path(name).name!=name:raise ValueError('nonlocal dependency '+name)
  source=(Path('/usr/lib')/name).resolve(strict=True)
  context=ld+('linux.ld_so_t' if name=='ld-linux-x86-64.so.2' else 'linux.lib_t')+':s0'
  record('/lib/'+name,source,context,0o755 if name=='ld-linux-x86-64.so.2' else 0o644);queue.append(tree/'lib'/name)
 path=queue.pop()
 if str(path) in inspected:continue
 inspected.add(str(path));p=subprocess.run(['/usr/bin/readelf','-d','-l',str(path)],capture_output=True,text=True,check=True)
 dynamic.append({'path':str(path),'stdout':p.stdout})
 needed.update(re.findall(r'Shared library: \[([^\]]+)\]',p.stdout))
image=out/'payload-2.ext4';argv=['/usr/bin/mke2fs','-q','-t','ext4','-F','-O','^has_journal','-d',str(tree),str(image),'32M'];p=subprocess.run(argv,capture_output=True,text=True,check=True);commands.append({'argv':argv,'exit':p.returncode,'stderr':p.stderr})
lines=[]
for i,(path,entry) in enumerate(entries.items()):
 value=out/('label-'+str(i));value.write_bytes(entry['context'].encode()+b'\0')
 lines.extend(['set_inode_field '+path+' uid 0','set_inode_field '+path+' gid 0','set_inode_field '+path+' mode '+('040700' if not entry['source'] else ('0'+format(0o100000|int(entry['mode'],8),'o'))),'ea_set -f '+str(value)+' '+path+' security.selinux'])
recipe=out/'payload-metadata.commands';recipe.write_text('\n'.join(lines)+'\n');argv=['/usr/bin/debugfs','-w','-f',str(recipe),str(image)];p=subprocess.run(argv,capture_output=True,text=True,check=True);commands.append({'argv':argv,'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr})
verify=[]
for path,entry in entries.items():
 p=subprocess.run(['/usr/bin/debugfs','-R','ea_get '+path+' security.selinux',str(image)],capture_output=True,text=True,check=True);assert entry['context'] in p.stdout,(path,p.stdout,p.stderr)
 stat=subprocess.run(['/usr/bin/debugfs','-R','stat '+path,str(image)],capture_output=True,text=True,check=True)
 assert re.search(r'User:\s+0\s+Group:\s+0',stat.stdout),stat.stdout
 actual_mode=re.search(r'Mode:\s+([0-7]+)',stat.stdout);assert actual_mode and int(actual_mode[1],8)==int(entry['mode'],8),(path,stat.stdout)
 if entry['source']:
  dump=out/('verify-'+str(len(verify)))
  subprocess.run(['/usr/bin/debugfs','-R','dump '+path+' '+str(dump),str(image)],capture_output=True,text=True,check=True)
  assert hashlib.sha256(dump.read_bytes()).hexdigest()==entry['sha256'],path
 verify.append({'path':path,'label':p.stdout,'stat':stat.stdout})
p=subprocess.run(['/usr/bin/e2fsck','-fn',str(image)],capture_output=True,text=True);assert p.returncode==0,(p.returncode,p.stdout,p.stderr)
manifest={'scope':'Offline filesystem bytes only: no mount, host xattrs, policy load/enforce or runtime acceptance.','image':str(image),'sha256':hashlib.sha256(image.read_bytes()).hexdigest(),'bytes':image.stat().st_size,'mounted_at':'/archtv in a future prepared process filesystem view','entries':entries,'commands':commands,'verification':verify,'e2fsck':{'exit':p.returncode,'stdout':p.stdout,'stderr':p.stderr},'Linux_dynamic_inventory':dynamic,'limitations':['Exact raw-image byte reproducibility not verified (filesystem UUID/timestamps). Source/binary/content hashes and metadata recorded.','Labels are offline xattr bytes, not live assigned contexts; source trust/RO aliasing/host impact and full factory policy admission remain unverified.','Rust example is a controlled lifetime exerciser, not installed production launcher. Android services/APK not available.']}
(d/'payload-mode-guard.json').write_text(json.dumps(manifest,indent=2)+'\n');image.chmod(0o400);print('PAYLOAD',manifest['sha256'],'entries',len(entries))
