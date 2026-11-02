#!/usr/bin/env python3
"""Build a coherent experimental original APEX/graphics/package cohort, no boot."""
from pathlib import Path
import json,subprocess,shutil,hashlib,sys
r=Path(__file__).resolve().parents[2];out=(r/sys.argv[1]).resolve();out.mkdir()
tracked_inputs=['Cargo.toml','Cargo.lock','crates/archtv-core/Cargo.toml',*[str(p.relative_to(r)) for p in sorted((r/'crates/archtv-core/src').rglob('*.rs'))],'crates/archtv-core/examples/native_supervisor.rs','reports/android16-package-bootstrap/execute-integrated.py','reports/android16-package-bootstrap/integrated-session.sh','reports/android16-apex-bootstrap/run.py','reports/android16-package-bootstrap/build-platform-overlay.py','tools/apk/SignPlatformOverlay.java','runtime/aosp/platform-overlay/AndroidManifest.xml','runtime/aosp/platform-overlay/res/values/config.xml','runtime/aosp/platform-overlay/overlay-config.xml','reports/android16-apex-bootstrap/devices.py','runtime/aosp/linux-services/initial-apk-profile.json','runtime/aosp/linux-services/org/archtv/aosplinux/SelectedServices.java','runtime/aosp/linux-services/install-markor.sh','runtime/aosp/native/linux-property-worker.cpp','runtime/aosp/native/linux-mc1-cohort.h','reports/android16-package-bootstrap/build-integrated.py','runtime/aosp/android16-qpr2/patches/0004-linux-admitted-lazy-services.patch']
source_hashes={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in tracked_inputs}
(out/'source-inputs.json').write_text(json.dumps(source_hashes,indent=2)+'\n')
overlay=r/'dist/aosp16/platform-overlay-build-2'
overlay_record=json.loads((overlay/'build.json').read_text())
assert hashlib.sha256((overlay/'ArchTvPlatform.apk').read_bytes()).hexdigest()==overlay_record['apk_sha256']
for path,digest in overlay_record['inputs_sha256'].items():
 assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
(out/'platform-overlay-input.json').write_text(json.dumps(overlay_record,indent=2)+'\n')
entry=out/'entry'
subprocess.run(['python',str(r/'reports/android16-selected-display/build-entry.py'),'--output',str(entry)],check=True)
rc=(entry/'selected-services.rc').read_text()
# EventHub requires CAP_BLOCK_SUSPEND; original ZygoteInit grants it to system_server.
assert rc.count('    capabilities SYS_NICE\n')==1
# Original ZygoteInit also grants WAKE_ALARM: timerfd ALARM clocks require it.
rc=rc.replace('    capabilities SYS_NICE\n','    capabilities SYS_NICE BLOCK_SUSPEND WAKE_ALARM\n')
# Selected system services open the original netd maps by DAC. Reuse only
# the two original system_server groups needed by network accounting, from
# pinned ZygoteInit --setgroups; no CAP_BPF or global sysctl exception.
assert rc.count('    group system graphics\n')==1
rc=rc.replace('    group system graphics\n','    group system graphics net_bw_stats net_bw_acct\n')
lines=rc.splitlines();lines[0]='service archtv-selected-services /system/bin/app_process64 -Xmx768m -Xnoimage-dex2oat /system/bin --application --nice-name=archtv-selected-services org.archtv.aosplinux.ServiceLauncher --packages'
checkpoint_diagnostic='--checkpoint-diagnostic' in sys.argv[2:]
(out/'build-options.json').write_text(json.dumps({'checkpoint_contract_diagnostic':checkpoint_diagnostic},indent=2)+'\n')
if checkpoint_diagnostic:lines.append('    setenv ARCHTV_CHECKPOINT_DIAGNOSTIC 1')
lines=[l for l in lines if not any(l.startswith('    setenv '+n+' ') for n in ['BOOTCLASSPATH','DEX2OATBOOTCLASSPATH','SYSTEMSERVERCLASSPATH','STANDALONE_SYSTEMSERVER_JARS'])];(entry/'selected-services.rc').write_text('\n'.join(lines)+'\n')
old=r/'dist/aosp16/apex-cohort-build-6';commands=[]
for n in ['graphics-client']:
 p=out/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old/n,p)
def run(argv):
 p=subprocess.run(argv,capture_output=True,text=True);commands.append({'argv':argv,'exit':p.returncode,'stderr':p.stderr});(out/'build.json').write_text(json.dumps({'commands':commands},indent=2));assert p.returncode==0,p.stderr
# Build the supervisor from the current frozen Rust inputs; never inherit an
# older executable whose CLI/lifetime contract differs from this candidate.
rust_cache=Path('/home/tv/.cache/archtv/native-supervisor-current')
run(['cargo','rustc','--offline','--locked','--manifest-path',str(r/'Cargo.toml'),'-p','archtv-core','--example','native_supervisor','--target-dir',str(rust_cache),'--','-C','link-arg=-Wl,--dynamic-linker,/archtv/lib/ld-linux-x86-64.so.2','-C','link-arg=-Wl,-rpath,/archtv/lib'])
(out/'cargo/debug/examples').mkdir(parents=True,exist_ok=True)
shutil.copy2(rust_cache/'debug/examples/native_supervisor',out/'cargo/debug/examples/native_supervisor')
assert '/archtv/lib/ld-linux-x86-64.so.2' in subprocess.check_output(['readelf','-l',str(out/'cargo/debug/examples/native_supervisor')],text=True), 'Linux payload interpreter contract missing'
for c in json.loads((old/'build.json').read_text())['commands']:
 argv=[a.replace(str(old),str(out)).replace('property-actions-source-2','property-actions-source-3').replace('property-actions-build-3','property-actions-build-4') for a in c['argv']]
 run(argv)
argv=json.loads((r/'reports/android16-hwmanager-cohort/helper-build.json').read_text())['argv'];argv[argv.index('-o')+1]=str(out/'linux-exec-context-image');run(argv)
(out/'artifacts.json').write_text(json.dumps({n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['graphics-client','cargo/debug/examples/native_supervisor','linux-exec-context-image','property-coordinator']},indent=2))
base=r/'dist/aosp16/sf-cohort-build-32';vendor=json.loads((base/'vendor-inputs.json').read_text())
for key,value in vendor['files'].items():
 if key=='/vendor/framework/archtv-selected-services.jar':value['source']=str(entry/'archtv-selected-services.jar')
 if key=='/vendor/etc/init/archtv-selected-services.rc':value['source']=str(entry/'selected-services.rc')
# This Linux profile runs one real 64-bit Zygote. Preserve GSI bytes, but
# declare the implemented device ABI set through the original property loader.
base_props=Path(vendor['files']['/vendor/build.prop']['source']).read_text()
(out/'linux-build.prop').write_text(base_props+'\nro.product.cpu.abilist=x86_64\nro.product.cpu.abilist64=x86_64\nro.product.cpu.abilist32=\n')
vendor['files']['/vendor/build.prop']['source']=str(out/'linux-build.prop')
vendor['files']['/vendor/overlay/ArchTvPlatform/ArchTvPlatform.apk']={'source':str(overlay/'ArchTvPlatform.apk'),'context':'u:object_r:vendor_overlay_file:s0','mode':0o644}
vendor['files']['/vendor/overlay/config/config.xml']={'source':str(r/'runtime/aosp/platform-overlay/overlay-config.xml'),'context':'u:object_r:vendor_overlay_file:s0','mode':0o644}
profile=json.loads((r/'runtime/aosp/linux-services/initial-apk-profile.json').read_text())
profile_lines=[]
for item in profile['excluded']:
 source=r/'dist/aosp16/factory-inputs-3/root'/item['apk'].lstrip('/')
 assert source.stat().st_size==item['bytes'] and hashlib.file_digest(source.open('rb'),'sha256').hexdigest()==item['sha256'],item['apk']
 profile_lines.append('\t'.join([item['package'],str(Path(item['apk']).parent),Path(item['apk']).name,item['sha256'],str(item['bytes']),str(item['uid']),str(item['gid']),str(item['directory_uid']),str(item['directory_gid'])]))
(out/'initial-apk-profile.tsv').write_text('\n'.join(profile_lines)+'\n')
vendor['files']['/vendor/etc/archtv-initial-apk-profile.tsv']={'source':str(out/'initial-apk-profile.tsv'),'context':'u:object_r:vendor_configs_file:s0','mode':0o400}
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
# Original platform loader separated from the Mainline loader for Linux
# coexistence. Keep the original UID, groups, capabilities, kmsg and limits.
network_rc=(r/'dist/aosp16/factory-inputs-3/root/apex/com.android.tethering/etc/netbpfload.35rc').read_text()
assert network_rc.count('service bpfloader /apex/com.android.tethering/bin/netbpfload')==1
network_rc=network_rc.replace('service bpfloader /apex/com.android.tethering/bin/netbpfload','service archtv-platform-bpfloader /archtv/bin/archtv-platform-bpfloader')
(out/'platform-bpfloader.rc').write_text(network_rc)
# Linux entry alias: identical original ELF, original bpfloader_exec type.
# init may enter bpfloader through this type; AOSP neverallow forbids init
# executing bpfloader_platform_exec directly. No new SELinux permission.
vendor['files']['/bin/archtv-platform-bpfloader']={'source':str(r/'dist/aosp16/factory-inputs-3/root/system/bin/bpfloader'),'context':'u:object_r:bpfloader_exec:s0','mode':0o755}
vendor['files']['/vendor/etc/init/archtv-platform-bpfloader.rc']={'source':str(out/'platform-bpfloader.rc'),'context':'u:object_r:vendor_configs_file:s0','mode':0o644}
# Host BPF_UNPRIV_DEFAULT_OFF=2 stays unchanged. netd's original map_create
# contract needs CAP_BPF on this Linux; never add forbidden SYS_ADMIN.
netd_rc=(r/'dist/aosp16/factory-inputs-3/root/system/etc/init/netd.rc').read_text()
assert netd_rc.count('    capabilities ')==1
netd_rc=netd_rc.replace('    capabilities ','    capabilities BPF ',1)
(out/'linux-netd.rc').write_text(netd_rc)
vendor['files']['/vendor/etc/init/archtv-netd.rc']={'source':str(out/'linux-netd.rc'),'context':'u:object_r:vendor_configs_file:s0','mode':0o644}
(out/'vendor-inputs.json').write_text(json.dumps(vendor,indent=2))
text=(base/'build-payload-expanded.py').read_text().replace(str(base),str(out));expected=out/'apex-expected.json';expected.write_text(json.dumps(json.loads((r/'reports/android16-apex-bootstrap/complete-inputs.json').read_text())['modules'],indent=2)+'\n');text=text.replace("image=out/'payload-2.ext4'", "record('/apex-expected.json',out/'apex-expected.json','u:object_r:vendor_configs_file:s0',0o600)\nimage=out/'payload-2.ext4'")
old_parent="record('/'+str(parent.relative_to(tree)),None,'u:object_r:vendor_file:s0',0o755)"
assert old_parent in text
text=text.replace(old_parent,"record('/'+str(parent.relative_to(tree)),None,'u:object_r:vendor_overlay_file:s0' if path.startswith('/vendor/overlay/') else 'u:object_r:vendor_file:s0',0o755)")
recipe=out/'build-payload.py';recipe.write_text(text);subprocess.run(['python',str(recipe)],stdout=open(out/'packager.log','w'),stderr=subprocess.STDOUT,check=True)
assert all(hashlib.sha256((r/n).read_bytes()).hexdigest()==h for n,h in source_hashes.items()), 'Source changed during build'
print(out,flush=True)
