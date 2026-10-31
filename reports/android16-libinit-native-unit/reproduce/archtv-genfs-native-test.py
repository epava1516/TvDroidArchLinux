from pathlib import Path
import os,subprocess,shutil,json,hashlib
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/genfslabelsversion-execution-1';(out/'data').mkdir(parents=True);shutil.copy2(r/'dist/aosp16/genfslabelsversion-native-1/probe',out/'data/probe');cases={'missing':(None,202404),'valid':('202512\n',202512),'malformed':('not-a-version\n',202404),'permission-denied':('202512\n',202404)};results=[]
for name,(content,expected) in cases.items():
 vendor=out/('vendor-'+name);(vendor/'etc/selinux').mkdir(parents=True)
 if content is not None:
  f=vendor/'etc/selinux/genfs_labels_version.txt';f.write_text(content);os.chmod(f,0 if name=='permission-denied' else 0o644)
 argv=['unshare','--mount','--pid','--fork','--kill-child','--net','--ipc','--uts','--cgroup','python','/tmp/archtv-genfs-native-execution.py',name];p=subprocess.run(argv,capture_output=True,text=True,timeout=30);row={'case':name,'expected_original_source_result':expected,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr};results.append(row);(out/'results.json').write_text(json.dumps({'scope':'Original Rust FFI/std Bionic filesystem read through C ABI; source-defined version fallback, NOT policy/SELinux success or APK compatibility','results':results},indent=2)+'\n');print(name,p.returncode,p.stdout.splitlines()[-1:] if p.stdout else [],p.stderr[:1000],flush=True);assert p.returncode==0 and p.stdout.splitlines()[-1]==str(expected)
print('All four original Rust/Bionic cases matched source behavior')
