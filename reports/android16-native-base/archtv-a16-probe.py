from pathlib import Path
import subprocess,json,time,hashlib
r=Path('/home/tv/repositorio-principal');root=r/'dist/aosp16/native-inputs-2';out=r/'dist/aosp16/native-probe-1';out.mkdir(exist_ok=False)
for directory in ['proc','dev','tmp','data','linkerconfig','vendor','product','system_ext']:(root/directory).mkdir(exist_ok=True)
(root/'system/bin/linker64').symlink_to('/apex/com.android.runtime/bin/linker64')
libpath=':'.join(['/apex/com.android.art/lib64','/apex/com.android.runtime/lib64/bionic','/system/lib64','/apex/com.android.i18n/lib64','/apex/com.android.conscrypt/lib64'])
base=['/usr/bin/prlimit','--cpu=10','--core=0','--','/usr/bin/setpriv','--inh-caps=-all','--ambient-caps=-all','/usr/bin/bwrap','--unshare-all','--die-with-parent','--new-session','--uid','10000','--gid','10000','--cap-drop','ALL','--ro-bind',str(root),'/','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--tmpfs','/data','--clearenv','--setenv','PATH','/system/bin','--setenv','LD_LIBRARY_PATH',libpath,'--setenv','ANDROID_ROOT','/system','--setenv','ANDROID_ART_ROOT','/apex/com.android.art','--setenv','ANDROID_I18N_ROOT','/apex/com.android.i18n','--setenv','ANDROID_DATA','/data','--chdir','/data','--']
for name,args in [('linker-help',['/apex/com.android.runtime/bin/linker64','--help']),('linker-list',['/apex/com.android.runtime/bin/linker64','--list','/apex/com.android.art/bin/dalvikvm64']),('art-help',['/apex/com.android.art/bin/dalvikvm64','-help'])]:
 start=time.monotonic();command=base+args
 with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:
  try:code=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=20).returncode
  except subprocess.TimeoutExpired:code=124
 (out/(name+'.json')).write_text(json.dumps({'command':command,'exit_code':code,'seconds':time.monotonic()-start,'scope':'Original A16 components, UID10000/unshare-all/readonly/no network/no Android boot. Flattened LD_LIBRARY_PATH diagnostic only; no original linker namespace/config validation, ART semantic execution or APK acceptance.'},indent=2)+'\n');print(name,code,flush=True);print((out/(name+'.stderr')).read_text()[-1500:],flush=True)
