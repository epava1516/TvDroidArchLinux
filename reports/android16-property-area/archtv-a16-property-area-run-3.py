from pathlib import Path
import subprocess,shutil,json,hashlib,time
repo=Path('/home/tv/repositorio-principal');out=repo/'dist/aosp16/property-area-3';root=Path('/tmp/archtv-a16-native-root');stage=Path('/tmp/archtv-a16-property-area-3');stage.mkdir(exist_ok=False);(stage/'probe').mkdir();shutil.copy2(out/'property-area-probe.so',stage/'probe/property-area-probe.so')
assert hashlib.sha256((root/'system/build.prop').read_bytes()).hexdigest()=='8190df2d4debcb3f2271543435ec49b9951acd59c5ba67dc7556f76fd30be1a0'
libpath=':'.join(['/apex/com.android.art/lib64','/apex/com.android.runtime/lib64/bionic','/system/lib64','/apex/com.android.i18n/lib64','/apex/com.android.conscrypt/lib64','/apex/com.android.os.statsd/lib64'])
def run(name,props,identity='writer',privileged=False,writable_client=False):
 uid='0' if identity=='writer' else '10000'
 ns=['--unshare-ipc','--unshare-pid','--unshare-net','--unshare-uts','--unshare-cgroup'] if privileged else ['--unshare-all']
 command=['/usr/bin/prlimit','--cpu=10','--core=0','--','/usr/bin/bwrap',*ns,'--die-with-parent','--new-session','--uid',uid,'--gid',uid,'--cap-drop','ALL']
 if privileged:command+=['--cap-add','CAP_SYS_ADMIN']
 command+=['--ro-bind',str(root),'/','--proc','/proc','--dev','/dev','--bind' if identity=='writer' or writable_client else '--ro-bind',str(props),'/dev/__properties__','--ro-bind',str(stage/'probe'),'/probe','--tmpfs','/tmp','--tmpfs','/data','--clearenv','--setenv','LD_LIBRARY_PATH',libpath,'--setenv','LD_PRELOAD','/probe/property-area-probe.so','--setenv','ARCHTV_PROPERTY_PROBE_MODE',identity,'--chdir','/data','--','/apex/com.android.art/bin/dalvikvm64','-help']
 start=time.monotonic()
 with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:
  try:code=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=25).returncode
  except subprocess.TimeoutExpired:code=124
 (out/(name+'.json')).write_text(json.dumps({'command':command,'exit_code':code,'seconds':time.monotonic()-start,'scope':'Target-only diagnostic preloaded before launcher main; exits there, no ART/DEX/app execution or property service. Explicit local writer privileges, isolated no-network namespace; clients UID10000 no capabilities. Original Bionic APIs and metadata; security acceptance not implied.'},indent=2)+'\n');print(name,code,flush=True);print((out/(name+'.stdout')).read_text()[:700],flush=True);return code
props=stage/'properties-capless';props.mkdir();shutil.copy2(repo/'dist/aosp16/property-info-host-1/property_info',props/'property_info');(props/'property_info').chmod(0o444)
code=run('writer-capless',props)
if code!=0:
 props=stage/'properties-privileged';props.mkdir();shutil.copy2(repo/'dist/aosp16/property-info-host-1/property_info',props/'property_info');(props/'property_info').chmod(0o444);code=run('writer-privileged',props,privileged=True)
if code==0:
 run('reader-ro',props,'reader');run('reader-dac',props,'reader',writable_client=True)
files={p.name:{'uid':p.stat().st_uid,'gid':p.stat().st_gid,'mode':oct(p.stat().st_mode&0o777),'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'selinux_label':__import__('os').getxattr(p,'security.selinux').decode(errors='replace') if p.name!='property_info' else None} for p in props.iterdir() if p.is_file()};(out/'area-files.json').write_text(json.dumps({'root':str(props),'files':files},indent=2)+'\n')
