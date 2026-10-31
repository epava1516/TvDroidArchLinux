from pathlib import Path
import subprocess,json,time,os
repo=Path('/home/tv/repositorio-principal');old=repo/'dist/aosp16/property-area-2';out=repo/'dist/aosp16/property-mapped-client-1';out.mkdir(exist_ok=False)
nscommand=['/usr/bin/unshare','--user','--map-users=0:0:65536','--map-groups=0:0:65536','--','/usr/bin/sleep','60'];holder=subprocess.Popen(nscommand,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True);fd=None;info={'holder_pid':holder.pid,'command':nscommand}
try:
 for _ in range(100):
  if holder.poll() is not None:raise RuntimeError('Namespace helper exited: '+holder.communicate()[1])
  mapping=Path(f'/proc/{holder.pid}/uid_map').read_text()
  if '65536' in mapping:break
  time.sleep(0.02)
 else:raise RuntimeError('Namespace mappings not ready')
 info['uid_map']=mapping;info['gid_map']=Path(f'/proc/{holder.pid}/gid_map').read_text();fd=os.open(f'/proc/{holder.pid}/ns/user',os.O_RDONLY)
 for name in ['reader-ro','reader-dac']:
  command=json.loads((old/(name+'.json')).read_text())['command'];i=command.index('--unshare-all');command[i:i+1]=['--userns',str(fd),'--unshare-ipc','--unshare-pid','--unshare-net','--unshare-uts','--unshare-cgroup'];start=time.monotonic()
  with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:
   try:code=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=25,pass_fds=(fd,)).returncode
   except subprocess.TimeoutExpired:code=124
  (out/(name+'.json')).write_text(json.dumps({'command':command,'exit_code':code,'seconds':time.monotonic()-start,'scope':'Same areas/probe, explicit full UID/GID namespace mapping preserves root and app UID. Namespace holder is a Linux tool, not Android boot. No property service/SELinux/ART/DEX/APK acceptance.'},indent=2)+'\n');print(name,code,flush=True);text=(out/(name+'.stdout')).read_text();print(text[:300]+text[-150:],flush=True)
finally:
 if fd is not None:os.close(fd)
 if holder.poll() is None:holder.terminate()
 try:holder.wait(timeout=5)
 except subprocess.TimeoutExpired:holder.kill();holder.wait()
 info['terminal_returncode']=holder.returncode;(out/'namespace.json').write_text(json.dumps(info,indent=2)+'\n')
