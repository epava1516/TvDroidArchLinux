from pathlib import Path
import subprocess,json,time
repo=Path('/home/tv/repositorio-principal');old=repo/'dist/aosp16/property-area-2';out=repo/'dist/aosp16/property-client-identity-1';out.mkdir(exist_ok=False)
for name in ['reader-ro','reader-dac']:
 command=json.loads((old/(name+'.json')).read_text())['command'];i=command.index('--unshare-all');command[i:i+1]=['--unshare-ipc','--unshare-pid','--unshare-net','--unshare-uts','--unshare-cgroup'];start=time.monotonic()
 with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:
  try:code=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=25).returncode
  except subprocess.TimeoutExpired:code=124
 (out/(name+'.json')).write_text(json.dumps({'command':command,'exit_code':code,'seconds':time.monotonic()-start,'changed':'User namespace omitted; mount/PID/net/IPC/UTS/cgroup namespaces and UID/GID10000/no caps retained. Same original areas and diagnostic binary.','scope':'Property reader and absence/denial diagnostic only; no service, policy/SELinux, DEX or APK acceptance.'},indent=2)+'\n');print(name,code,flush=True);text=(out/(name+'.stdout')).read_text();print(text[:300]+text[-150:],flush=True)
