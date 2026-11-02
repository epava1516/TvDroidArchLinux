#!/usr/bin/env python3
"""Build a coherent experimental original APEX/graphics/package cohort, no boot."""
from pathlib import Path
import json,subprocess,shutil,hashlib,sys
r=Path(__file__).resolve().parents[2];out=(r/sys.argv[1]).resolve();out.mkdir()
entry=out/'entry'
subprocess.run(['python',str(r/'reports/android16-selected-display/build-entry.py'),'--output',str(entry)],check=True)
rc=(entry/'selected-services.rc').read_text()
# EventHub requires CAP_BLOCK_SUSPEND; original ZygoteInit grants it to system_server.
assert rc.count('    capabilities SYS_NICE\n')==1
rc=rc.replace('    capabilities SYS_NICE\n','    capabilities SYS_NICE BLOCK_SUSPEND\n')
lines=rc.splitlines();lines[0]='service archtv-selected-services /system/bin/app_process64 -Xmx768m -Xnoimage-dex2oat /system/bin --application --nice-name=archtv-selected-services org.archtv.aosplinux.ServiceLauncher --packages'
lines=[l for l in lines if not any(l.startswith('    setenv '+n+' ') for n in ['BOOTCLASSPATH','DEX2OATBOOTCLASSPATH','SYSTEMSERVERCLASSPATH','STANDALONE_SYSTEMSERVER_JARS'])];(entry/'selected-services.rc').write_text('\n'.join(lines)+'\n')
old=r/'dist/aosp16/apex-cohort-build-6';commands=[]
for n in ['graphics-client','cargo/debug/examples/native_supervisor']:
 p=out/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old/n,p)
def run(argv):
 p=subprocess.run(argv,capture_output=True,text=True);commands.append({'argv':argv,'exit':p.returncode,'stderr':p.stderr});(out/'build.json').write_text(json.dumps({'commands':commands},indent=2));assert p.returncode==0,p.stderr
for c in json.loads((old/'build.json').read_text())['commands']:run([a.replace(str(old),str(out)) for a in c['argv']])
argv=json.loads((r/'reports/android16-hwmanager-cohort/helper-build.json').read_text())['argv'];argv[argv.index('-o')+1]=str(out/'linux-exec-context-image');run(argv)
(out/'artifacts.json').write_text(json.dumps({n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['graphics-client','cargo/debug/examples/native_supervisor','linux-exec-context-image','property-coordinator']},indent=2))
base=r/'dist/aosp16/sf-cohort-build-32';vendor=json.loads((base/'vendor-inputs.json').read_text())
for key,value in vendor['files'].items():
 if key=='/vendor/framework/archtv-selected-services.jar':value['source']=str(entry/'archtv-selected-services.jar')
 if key=='/vendor/etc/init/archtv-selected-services.rc':value['source']=str(entry/'selected-services.rc')
vendor['files']['/vendor/bin/install-markor.sh']={'source':str(r/'runtime/aosp/linux-services/install-markor.sh'),'context':'u:object_r:vendor_file:s0','mode':0o644}
zygote=(r/'dist/aosp16/factory-inputs-3/root/system/etc/init/hw/init.zygote64.rc').read_text()
assert zygote.count(' --start-system-server')==1
zygote=zygote.replace(' --start-system-server','')
zygote+=''.join('    setenv '+key+' '+value+'\n' for key,value in {'ANDROID_ART_ROOT':'/apex/com.android.art','ANDROID_I18N_ROOT':'/apex/com.android.i18n','ANDROID_TZDATA_ROOT':'/apex/com.android.tzdata'}.items())
(out/'app-zygote.rc').write_text(zygote)
vendor['files']['/vendor/etc/init/archtv-app-zygote.rc']={'source':str(out/'app-zygote.rc'),'context':'u:object_r:vendor_configs_file:s0','mode':0o644}
health=Path('/home/tv/.cache/archtv/aosp16-qpr2/health-original-study-1/hardware-health/aidl/default')
health_rc=(health/'android.hardware.health-service.example.rc').read_text();assert health_rc.count('\nservice vendor.charger ')==1
(out/'health.rc').write_text(health_rc.split('\nservice vendor.charger ',1)[0]+'\n')
# Whole original default provider; offline charger mode is owned by Linux.
for target,source,context,mode in [('/vendor/bin/hw/android.hardware.health-service.example',r/'dist/aosp16/health-original-build-3/android.hardware.health-service.example','u:object_r:hal_health_default_exec:s0',0o755),('/vendor/etc/init/archtv-health.rc',out/'health.rc','u:object_r:vendor_configs_file:s0',0o644),('/vendor/etc/vintf/manifest/health.xml',health/'android.hardware.health-service.example.xml','u:object_r:vendor_configs_file:s0',0o644),('/vendor/lib64/android.hardware.health-V4-ndk.so',r/'dist/aosp16/factory-inputs-3/root/system/lib64/android.hardware.health-V4-ndk.so','u:object_r:vendor_file:s0',0o644)]:
 vendor['files'][target]={'source':str(source),'context':context,'mode':mode}
(out/'vendor-inputs.json').write_text(json.dumps(vendor,indent=2))
text=(base/'build-payload-expanded.py').read_text().replace(str(base),str(out));expected=out/'apex-expected.json';expected.write_text(json.dumps(json.loads((r/'reports/android16-apex-bootstrap/complete-inputs.json').read_text())['modules'],indent=2)+'\n');text=text.replace("image=out/'payload-2.ext4'", "record('/apex-expected.json',out/'apex-expected.json','u:object_r:vendor_configs_file:s0',0o600)\nimage=out/'payload-2.ext4'")
recipe=out/'build-payload.py';recipe.write_text(text);subprocess.run(['python',str(recipe)],stdout=open(out/'packager.log','w'),stderr=subprocess.STDOUT,check=True)
print(out,flush=True)
