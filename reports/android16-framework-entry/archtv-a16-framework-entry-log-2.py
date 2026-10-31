from pathlib import Path
import subprocess,os,json,ctypes,sys
repo=Path('/home/tv/repositorio-principal');name=sys.argv[1];out=repo/'dist/aosp16/framework-entry-log-2';runtime=out/'runtime';runtime.mkdir()
def mount(*a):subprocess.run(['/usr/bin/mount',*map(str,a)],check=True,stdout=subprocess.DEVNULL)
mount('--bind',repo/'dist/aosp16/factory-inputs-3/root',runtime);mount('-o','remount,bind,ro',runtime);mount('-t','proc','proc',runtime/'proc');mount('-t','tmpfs','-o','mode=755,size=16m','tmpfs',runtime/'dev')
(runtime/'dev/__properties__').mkdir();mount('--bind','/tmp/archtv-a16-property-area-3/properties-privileged',runtime/'dev/__properties__');mount('-o','remount,bind,ro',runtime/'dev/__properties__')
(runtime/'dev/null').touch();mount('--bind','/dev/null',runtime/'dev/null')
mount('--bind',repo/'dist/aosp16/linkerconfig-2/generated',runtime/'linkerconfig');mount('-o','remount,bind,ro',runtime/'linkerconfig')
mount('-t','tmpfs','-o','mode=1777,size=32m','tmpfs',runtime/'tmp')
mount('--bind',out/'data',runtime/'data')
mount('--bind',out/'app',runtime/'probe');mount('-o','remount,bind,ro',runtime/'probe')
(runtime/'dev/kmsg').touch();mount('--bind',out/'private-kmsg',runtime/'dev/kmsg')
os.chroot(runtime);os.chdir('/data');os.setgroups([]);os.setgid(10000);os.setuid(10000);libc=ctypes.CDLL(None,use_errno=True)
if libc.prctl(38,1,0,0,0):raise OSError(ctypes.get_errno(),'PR_SET_NO_NEW_PRIVS')
print('PREEXEC_STATUS '+json.dumps([x for x in Path('/proc/self/status').read_text().splitlines() if x.startswith(('Uid:','Gid:','Groups:','CapEff:','CapPrm:','NoNewPrivs:'))]),flush=True)
env={'ANDROID_ROOT':'/system','ANDROID_DATA':'/data','ANDROID_ART_ROOT':'/apex/com.android.art','ANDROID_I18N_ROOT':'/apex/com.android.i18n','ANDROID_TZDATA_ROOT':'/apex/com.android.tzdata'}
programs={'linker-list':['/apex/com.android.runtime/bin/linker64','--list','/apex/com.android.art/bin/dalvikvm64'],'art-help':['/apex/com.android.art/bin/dalvikvm64','-help'],'getprop':['/system/bin/getprop','ro.build.version.sdk_full']}
for line in Path('/probe/classpath').read_text().splitlines():
 _,key,value=line.split(' ',2);env[key]=value
env['CLASSPATH']='/probe/markor.apk'
env['LD_PRELOAD']='/data/native-log-diagnostic.so'
argv=['/system/bin/app_process64','-Xint','-Xmx256m','-Xnoimage-dex2oat','/system/bin','--application','android.app.ActivityThread'];os.execve(argv[0],argv,env)
