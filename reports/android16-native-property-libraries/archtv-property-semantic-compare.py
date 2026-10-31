from pathlib import Path
import subprocess,os,json,hashlib,shutil
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/property-native-execution-1';data=out/'data';root=r/'dist/aosp16/factory-inputs-3/root';queries={'archtv.unknown.property','ro.product.cpu.abilist64','ro.hardware','ro.vendor.api_level'}
for p in [root/'system/etc/selinux/plat_property_contexts',root/'system/system_ext/etc/selinux/system_ext_property_contexts',root/'system/product/etc/selinux/product_property_contexts']:
 for line in p.read_text().splitlines():
  parts=line.split()
  if not parts or parts[0].startswith('#'):continue
  name=parts[0];queries.update([name,name+'.__archtv_probe',name+'__archtv_probe'])
queries=sorted(queries);(data/'queries').write_text('\n'.join(queries)+'\n');shutil.copy2(r/'dist/aosp16/boot-profile-1/property_info',data/'property_info-host')
def run(mode):
 argv=['unshare','--mount','--pid','--fork','--kill-child','--net','--ipc','--uts','--cgroup','python','/tmp/archtv-native-property-execution.py',mode];p=subprocess.run(argv,capture_output=True,text=True,timeout=30);(out/(mode+'.json')).write_text(json.dumps({'argv':argv,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n');print(mode,p.returncode,'lines',len(p.stdout.splitlines()),flush=True);return p
bad=run('inspect-bad-owner');assert bad.returncode==2 and 'rejected input' in bad.stderr
repeat=run('generate-repeat');assert repeat.returncode==0;assert (data/'property_info').read_bytes()==(data/'property_info-repeat').read_bytes()
for p in [data/'property_info',data/'property_info-host']:os.chown(p,0,0);os.chmod(p,0o444)
a=run('inspect-native');b=run('inspect-host');assert a.returncode==b.returncode==0;assert len(a.stdout.splitlines())==len(queries)+1;assert a.stdout.splitlines()[1:]==b.stdout.splitlines()[1:]
argv=[str(r/'dist/aosp16/property-info-host-1/property-info'),'--inspect',str(data/'property_info'),*queries];host=subprocess.run(argv,capture_output=True,text=True,timeout=30);(out/'host-reader-native.json').write_text(json.dumps({'exit_code':host.returncode,'stdout':host.stdout,'stderr':host.stderr},indent=2)+'\n');assert host.returncode==0;assert host.stdout.splitlines()==a.stdout.splitlines()[1:]
result={'queries':len(queries),'native_reader_both_blobs_equal':True,'host_reader_native_blob_equal':True,'native_metadata_repeat_byte_identical':True,'native_and_host_blobs_byte_equal':False,'different_bytes':sum(x!=y for x,y in zip((data/'property_info').read_bytes(),(data/'property_info-host').read_bytes())),'native_blob_sha256':hashlib.sha256((data/'property_info').read_bytes()).hexdigest(),'host_blob_sha256':hashlib.sha256((data/'property_info-host').read_bytes()).hexdigest(),'root_owner_enforcement_native_rejected_UID10000_file':True,'scope':'Original metadata serialization and parser lookup across full declared input names plus suffix variants; not all possible API/service/SELinux policies or APK compatibility'};(out/'semantic-comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
