from pathlib import Path
import shutil,subprocess,json,hashlib,os
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/property-native-execution-1';assert (out/'data/property-info').read_bytes()==(r/'dist/aosp16/property-libs-native-1/property-info').read_bytes();os.chown(out/'data',10000,10000);os.chmod(out/'data',0o700)
argv=['unshare','--mount','--pid','--fork','--kill-child','--net','--ipc','--uts','--cgroup','python','/tmp/archtv-native-property-execution.py','generate'];p=subprocess.run(argv,capture_output=True,text=True,timeout=30);(out/'generate.json').write_text(json.dumps({'argv':argv,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr},indent=2)+'\n');print(p.returncode,p.stdout,p.stderr)
if p.returncode==0:
 data=(out/'data/property_info').read_bytes();reference=(r/'dist/aosp16/boot-profile-1/property_info').read_bytes();print('metadata identical to original host serializer:',data==reference,'sha256',hashlib.sha256(data).hexdigest());assert data==reference
