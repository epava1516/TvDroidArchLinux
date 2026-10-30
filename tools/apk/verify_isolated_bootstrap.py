#!/usr/bin/env python3
"""Bounded original Markor bootstrap experiment in a read-only, UID-mapped Linux namespace."""
import argparse,hashlib,json,os,socket,subprocess,zipfile
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--output',type=Path,required=True);p.add_argument('--platform-classpath',type=Path);p.add_argument('--platform-resources',type=Path);a=p.parse_args()
if bool(a.platform_classpath)!=bool(a.platform_resources):p.error('Both platform inputs are required together')
root=Path(__file__).resolve().parents[2];out=a.output.resolve();out.mkdir(parents=True,exist_ok=False)
for name in ['classes','dex','data','data/art','data/app']:(out/name).mkdir()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
cache=Path.home()/'.cache/archtv';runtime=cache/'art-host/host/art-13.0.0';system=runtime/'product/redfin/system/framework';tools=cache/'apk-build-tools';reference=cache/'aosp-compile-tools/android-all-13.jar'
assert sha(reference)==json.loads((root/'runtime/aosp/compile-reference.json').read_text())['sha256']
for item in json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())['artifacts']:
 if item['file'] in ['android.jar','r8.jar']:assert sha(tools/item['file'])==item['sha256']
app=next(x for x in json.loads((root/'reports/arquitectura-apk-20261030/compatibility-matrix.json').read_text())['applications'] if x['id']=='markor');apk=Path(app['path_local']);assert sha(apk)==app['sha256']
sources=[root/'fixtures/aosp-isolated-bootstrap/OriginalBootstrapProbe.java',root/'runtime/apk/java/org/archtv/apkruntime/HostProfile.java',root/'runtime/aosp/linux-services/org/archtv/aosplinux/LocalServiceBinder.java',root/'runtime/aosp/linux-services/org/archtv/aosplinux/LinuxServiceRegistry.java'];jdk=Path('/usr/lib/jvm/java-17-openjdk/bin');commands=[]
def run(cmd,name,timeout=60):
 cmd=list(map(str,cmd));commands.append({'name':name,'argv':cmd})
 with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:
  try:return subprocess.run(cmd,stdout=stdout,stderr=stderr,timeout=timeout).returncode
  except subprocess.TimeoutExpired:return 124
for name,cmd in [('javac',[jdk/'javac','--release','8','-classpath',reference,'-d',out/'classes',*sources]),('jar',[jdk/'jar','cf',out/'probe.jar','-C',out/'classes','.']),('dex',[jdk/'java','-cp',tools/'r8.jar','com.android.tools.r8.D8','--release','--min-api','28','--lib',tools/'android.jar','--output',out/'dex',out/'probe.jar'])]:
 if run(cmd,name)!=0:raise SystemExit('Build failed: '+name)
with zipfile.ZipFile(out/'probe.jar') as z:assert not any(n.startswith('android/') for n in z.namelist())
readonly=out/'readonly';readonly.write_text('READ_ONLY_INPUT\n');canary=socket.socket();canary.bind(('127.0.0.1',0));canary.listen(1)
bwrap=['setpriv','--inh-caps=-all','--ambient-caps=-all','bwrap','--unshare-all','--die-with-parent','--new-session','--uid','10000','--gid','10000','--cap-drop','ALL','--ro-bind','/usr','/usr','--symlink','usr/bin','/bin','--symlink','usr/lib','/lib','--symlink','usr/lib','/lib64','--proc','/proc','--dev','/dev','--tmpfs','/tmp','--bind',str(out/'data'),'/data','--dir','/input','--ro-bind',str(readonly),'/input/readonly','--clearenv','--setenv','PATH','/usr/bin','--setenv','HOME','/data','--chdir','/data']
namespace=root/'fixtures/aosp-isolated-bootstrap/NamespaceProbe.py'
code=run([*bwrap,'--ro-bind',namespace,'/namespace.py','--setenv','HOST_CANARY_PORT',str(canary.getsockname()[1]),'--','/usr/bin/python','/namespace.py'],'namespace');canary.close();assert code==0,(out/'namespace.stderr')
preflight=json.loads((out/'namespace.stdout').read_text());assert preflight['isolation_preflight_pass'];assert readonly.read_text()=='READ_ONLY_INPUT\n' and (out/'data/persist.txt').read_text()=='namespace-data'
linux=cache/'smithay/target/debug/libarchtv_aosp_linux.so';resources=root/'dist/apk/androidfw-apk-metadata-4/libarchtv_resources_linux.so';binder=root/'dist/apk/binder-service-context-1/libarchtv_binder_holder.so'
assert sha(resources)==json.loads((root/'dist/apk/androidfw-apk-metadata-4/provenance.json').read_text())['jni_library_sha256']
assert sha(binder)==json.loads((root/'dist/apk/binder-service-context-1/result.json').read_text())['library_sha256']
mounts=['--dir','/runtime','--dir','/runtime/host','--ro-bind',str(runtime),'/runtime/host/art-13.0.0','--dir','/system','--dir','/system/framework','--ro-bind',str(system/'framework-res.apk'),'/system/framework/framework-res.apk','--dir','/app','--ro-bind',str(apk),'/app/app.apk','--ro-bind',str(system/'framework.jar'),'/app/framework.jar','--ro-bind',str(system/'framework-graphics.jar'),'/app/framework-graphics.jar','--ro-bind',str(out/'dex/classes.dex'),'/app/probe.dex','--dir','/native']
platform_inputs=[];platform_profile=None
classpath='/app/framework.jar:/app/framework-graphics.jar:/app/app.apk:/app/probe.dex'
if a.platform_classpath:
 platform_profile=json.loads(a.platform_classpath.read_text());core_names={'core-oj.jar','core-libart.jar','okhttp.jar','bouncycastle.jar','apache-xml.jar','core-icu4j.jar','conscrypt.jar'};selected=[]
 # Host ART core classes stay paired with host JNI libraries. All non-core platform
 # jars/resources come from one image build. This cross-build boundary is experimental.
 mounts=['--dir','/runtime','--dir','/runtime/host','--ro-bind',str(runtime),'/runtime/host/art-13.0.0','--dir','/system','--dir','/system/framework','--ro-bind',str(a.platform_resources.resolve()),'/system/framework/framework-res.apk','--dir','/app','--ro-bind',str(apk),'/app/app.apk','--ro-bind',str(out/'dex/classes.dex'),'/app/probe.dex','--dir','/native','--dir','/platform']
 for item in platform_profile['boot_jars']:
  source=Path(item['local_path']);assert sha(source)==item['sha256']
  if source.name in core_names:continue
  dest='/platform/'+str(len(selected))+'.jar';mounts+=['--ro-bind',str(source),dest];selected.append(dest);platform_inputs.append(source)
 assert selected
 classpath=':'.join([*selected,'/app/app.apk','/app/probe.dex']);platform_inputs+=[a.platform_classpath,a.platform_resources]
for source,dest in [(linux,'linux.so'),(resources,'resources.so'),(binder,'binder.so')]:mounts+=['--ro-bind',str(source),'/native/'+dest]
cmd=[*bwrap,*mounts,'--setenv','ANDROID_DATA','/data/art','--setenv','ANDROID_LOG_TAGS','*:w','--','/usr/bin/prlimit','--core=0','--cpu=45','--fsize=67108864','--','/runtime/host/art-13.0.0/bin/art','--64','--no-compile','--verbose','--','-Xint','-Xcheck:jni','-Xmx256m','-cp',classpath,'org.archtv.apkruntime.OriginalBootstrapProbe',app['declared_application']]
code=run(cmd,'bootstrap');stdout=(out/'bootstrap.stdout').read_text();stderr=(out/'bootstrap.stderr').read_text();stages=[x.removeprefix('BOOTSTRAP_STAGE ') for x in stdout.splitlines() if x.startswith('BOOTSTRAP_STAGE ')];blocked=[x for x in stderr.splitlines() if x.startswith('BOOTSTRAP_BLOCKED ')]
inputs=[*platform_inputs,apk,system/'framework.jar',system/'framework-graphics.jar',system/'framework-res.apk',runtime/'bin/art',linux,resources,binder,*sources,namespace]
result={'platform_profile':str(a.platform_classpath) if a.platform_classpath else None,'core_boundary':'R8 ART13 host core/JNI; optional non-core SDK image framework is a different Android13 build, experimental, not coherent whole platform runtime','isolation_preflight_pass':True,'preflight':preflight,'application_on_create_pass':code==0 and 'APPLICATION_ONCREATE_OK '+app['declared_application'] in stdout,'full_apk_functional_pass':False,'actual_uid_pass':'BOOTSTRAP_ACTUAL_UID_OK 10000' in stdout,'last_stage':stages[-1] if stages else None,'blocked':blocked,'exit_code':code,'commands':commands,'input_sha256':{str(x):sha(x) for x in inputs},'verifier_sha256':sha(Path(__file__)),'scope':'Namespace preflight plus original ActivityThread/ContextImpl/PackageParser/LoadedApk/Instrumentation path toward real Markor Application.onCreate. No prototype android.* or skipped Application.attach. No Activity launch/UI/input/persistence success implied. Namespace checks are not a complete sandbox/security, Binder IPC or resource-budget audit.'};(out/'result.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:result[k] for k in ['isolation_preflight_pass','actual_uid_pass','application_on_create_pass','last_stage','blocked','exit_code']}))
