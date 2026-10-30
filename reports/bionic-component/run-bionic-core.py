from pathlib import Path
import subprocess,json,hashlib
r=Path('/home/tv/.cache/archtv/aosp-platform-33/verified-modules-1');out=Path('/home/tv/repositorio-principal/dist/apk/bionic-component-1');root=out/'root';closure=json.loads((out/'closure.json').read_text());profile=json.loads(Path('/home/tv/.cache/archtv/aosp-platform-33/verified-bootclasspath-1.json').read_text());base=json.loads((out/'linker-help-result.json').read_text())['command'];command=base[:base.index('--')+1]
# Base has prlimit separator first; keep its bwrap command through guest separator.
command=base[:-2];i=command.index('--chdir');command[i:i]=['--setenv','LD_LIBRARY_PATH',':'.join(closure['search_paths'])]
data=out/'art-data';data.mkdir(exist_ok=False);command[command.index('--tmpfs',command.index('/proc')):command.index('--tmpfs',command.index('/proc'))] = []
i=command.index('/data');assert command[i-1]=='--tmpfs';command[i-1:i+1]=['--bind',str(data),'/data'];mounts=[];classpath=[];inputs={}
for item in profile['boot_jars']:
 src=Path(item['local_path']);assert hashlib.sha256(src.read_bytes()).hexdigest()==item['sha256'];dest=root/item['path'].removeprefix('/');dest.parent.mkdir(parents=True,exist_ok=True);dest.touch(exist_ok=True);mounts+=['--ro-bind',str(src),item['path']];classpath.append(item['path']);inputs[item['path']]=item['sha256']
for mod,relative in [('com.android.i18n','etc/icu/icudt70l.dat'),('com.android.tzdata','etc/tz/tzdata'),('com.android.tzdata','etc/tz/tz_version')]:
 src=r/'modules'/mod/'payload.img';dst=root/'apex'/mod/relative;dst.parent.mkdir(parents=True,exist_ok=True);p=subprocess.run(['debugfs','-R',f'dump /{relative} {dst}',str(src)],capture_output=True,text=True);assert dst.exists(),p.stderr;inputs['/apex/'+mod+'/'+relative]=hashlib.sha256(dst.read_bytes()).hexdigest()
dex=Path('/home/tv/repositorio-principal/dist/apk/bionic-core-probe-1/dex/classes.dex');(root/'app').mkdir(exist_ok=True);(root/'app/probe.dex').touch();mounts+=['--ro-bind',str(dex),'/app/probe.dex'];inputs['/app/probe.dex']=hashlib.sha256(dex.read_bytes()).hexdigest();i=command.index('--chdir');command[i:i]=mounts
for name,value in [('ANDROID_ROOT','/system'),('ANDROID_ART_ROOT','/apex/com.android.art'),('ANDROID_I18N_ROOT','/apex/com.android.i18n'),('ANDROID_TZDATA_ROOT','/apex/com.android.tzdata'),('ANDROID_DATA','/data'),('ANDROID_LOG_TAGS','*:w')]:
 i=command.index('--chdir');command[i:i]=['--setenv',name,value]
command[command.index('--cpu=10')]='--cpu=30';command+=['/apex/com.android.art/bin/dalvikvm64','-Xint','-Xcheck:jni','-Xmx256m','-Xnoimage-dex2oat','-Xnorelocate','-Xbootclasspath:'+':'.join(classpath),'-cp','/app/probe.dex','org.archtv.runtimeprobe.RuntimeProbe']
with (out/'art-core.stdout').open('wb') as stdout,(out/'art-core.stderr').open('wb') as stderr:
 try:code=subprocess.run(command,stdout=stdout,stderr=stderr,timeout=45).returncode
 except subprocess.TimeoutExpired:code=124
text=(out/'art-core.stdout').read_text();result={'exit_code':code,'dex_semantics_pass':code==0 and 'DEX_SEMANTICS_OK total=9' in text,'full_apk_functional_pass':False,'command':command,'input_sha256':inputs,'scope':'Original target Bionic/ART/libcore/JNI, original 31-jar bootclasspath, simple Java semantic fixture only. LD_LIBRARY_PATH flattened namespace experiment; no Android init/boot, framework services or real app workflow. Not full memory/security/lifetime validation.'};(out/'art-core-result.json').write_text(json.dumps(result,indent=2)+'\n');print(code,text);print((out/'art-core.stderr').read_text()[-5000:])
