from pathlib import Path
import subprocess,os,json,ctypes,sys
repo=Path('/home/tv/repositorio-principal');out=repo/'dist/aosp16/property-native-execution-1';mode=sys.argv[1];runtime=out/('runtime-'+mode);runtime.mkdir()
def mount(*args):subprocess.run(['/usr/bin/mount',*map(str,args)],check=True,stdout=subprocess.DEVNULL)
mount('--bind',repo/'dist/aosp16/factory-inputs-3/root',runtime);mount('-o','remount,bind,ro',runtime);mount('-t','proc','proc',runtime/'proc');mount('-t','tmpfs','-o','mode=755,size=16m','tmpfs',runtime/'dev');(runtime/'dev/null').touch();mount('--bind','/dev/null',runtime/'dev/null')
(runtime/'dev/__properties__').mkdir();mount('--bind','/tmp/archtv-a16-property-area-3/properties-privileged',runtime/'dev/__properties__');mount('-o','remount,bind,ro',runtime/'dev/__properties__')
mount('--bind',repo/'dist/aosp16/linkerconfig-2/generated',runtime/'linkerconfig');mount('-o','remount,bind,ro',runtime/'linkerconfig');mount('--bind',out/'data',runtime/'data');mount('--bind',out/'data/property-info',runtime/'data/property-info');mount('-o','remount,bind,ro',runtime/'data/property-info')
os.chroot(runtime);os.chdir('/data');os.setgroups([]);os.setgid(10000);os.setuid(10000);libc=ctypes.CDLL(None,use_errno=True);assert libc.prctl(38,1,0,0,0)==0
status={x.split(':',1)[0]:x.split(':',1)[1].strip() for x in Path('/proc/self/status').read_text().splitlines()};assert status['Uid'].split()==['10000']*4;assert status['Gid'].split()==['10000']*4;assert status['Groups']=='';assert int(status['CapEff'],16)==0 and int(status['CapPrm'],16)==0;assert status['NoNewPrivs']=='1'
print('PREEXEC_STATUS '+json.dumps({x:status[x] for x in ['Uid','Gid','Groups','CapEff','CapPrm','NoNewPrivs']}),flush=True)
if mode.startswith('generate'):argv=['/data/property-info','/data/property_info'+('-repeat' if mode=='generate-repeat' else ''),'/system/etc/selinux/plat_property_contexts','/system_ext/etc/selinux/system_ext_property_contexts','/product/etc/selinux/product_property_contexts']
else:argv=['/data/property-info','--inspect','/data/'+('property_info-host' if mode=='inspect-host' else 'property_info'),*Path('/data/queries').read_text().splitlines()]
os.execve(argv[0],argv,{'ANDROID_ROOT':'/system','ANDROID_DATA':'/data'})
