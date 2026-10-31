from pathlib import Path
import subprocess,os,ctypes,json,sys
r=Path('/home/tv/repositorio-principal');case=sys.argv[1];assert case in ['getprop','framework'];out=r/'dist/aosp16/property-profile-client-3';root=out/('runtime-'+case);root.mkdir();original=r/'dist/aosp16/factory-inputs-3/root'
for n in ['system','apex','linkerconfig','data','dev','proc','probe','tmp']:(root/n).mkdir()
def mount(*a):subprocess.run(['/usr/bin/mount',*map(str,a)],check=True,stdout=subprocess.DEVNULL)
for n in ['system','apex']:
 mount('--bind',original/n,root/n);mount('-o','remount,bind,ro',root/n)
for n in ['product','system_ext']:(root/n).symlink_to('/system/'+n)
(root/'etc').symlink_to('/system/etc');mount('--bind',r/'dist/aosp16/linkerconfig-2/generated',root/'linkerconfig');mount('-o','remount,bind,ro',root/'linkerconfig');mount('--bind',out/'data',root/'data');mount('--bind',out/'app',root/'probe');mount('-o','remount,bind,ro',root/'probe');mount('-t','proc','proc',root/'proc');mount('-t','tmpfs','-o','mode=1777,size=32m','tmpfs',root/'tmp');(root/'dev/__properties__').mkdir();mount('--bind',r/'dist/aosp16/propertyinit-execution-2/root/dev/__properties__',root/'dev/__properties__');mount('-o','remount,bind,ro',root/'dev/__properties__');(root/'dev/null').touch();mount('--bind','/dev/null',root/'dev/null');os.chown(out/'data',10000,10000);os.chroot(root);os.chdir('/data');os.setgroups([]);os.setgid(10000);os.setuid(10000);libc=ctypes.CDLL(None,use_errno=True);assert libc.prctl(38,1,0,0,0)==0
s={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in Path('/proc/self/status').read_text().splitlines()};assert s['Uid'].split()==['10000']*4 and s['Gid'].split()==['10000']*4 and not s['Groups'] and int(s['CapEff'],16)==0 and int(s['CapPrm'],16)==0 and s['NoNewPrivs']=='1';print('PREEXEC_STATUS '+json.dumps({k:s[k] for k in ['Uid','Gid','Groups','CapPrm','CapEff','NoNewPrivs']}),flush=True)
env={'ANDROID_ROOT':'/system','ANDROID_DATA':'/data','ANDROID_ART_ROOT':'/apex/com.android.art','ANDROID_I18N_ROOT':'/apex/com.android.i18n','ANDROID_TZDATA_ROOT':'/apex/com.android.tzdata'}
if case=='getprop':argv=['/system/bin/getprop']
else:
 for line in Path('/probe/classpath').read_text().splitlines():
  _,key,value=line.split(' ',2);env[key]=value
 env['CLASSPATH']='/probe/markor.apk';env['LD_PRELOAD']='/data/native-log-diagnostic.so';argv=['/system/bin/app_process64','-Xint','-Xmx256m','-Xnoimage-dex2oat','/system/bin','--application','android.app.ActivityThread']
os.execve(argv[0],argv,env)
