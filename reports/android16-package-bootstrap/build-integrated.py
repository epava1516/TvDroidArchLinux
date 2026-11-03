#!/usr/bin/env python3
"""Build a coherent experimental original APEX/graphics/package cohort, no boot."""
from pathlib import Path
import json,subprocess,shutil,hashlib,sys,re
r=Path(__file__).resolve().parents[2];out=(r/sys.argv[1]).resolve();out.mkdir()
tracked_inputs=['Cargo.toml','Cargo.lock','crates/archtv-core/Cargo.toml',*[str(p.relative_to(r)) for p in sorted((r/'crates/archtv-core/src').rglob('*.rs'))],'crates/archtv-core/examples/native_supervisor.rs','reports/android16-package-bootstrap/execute-integrated.py','reports/android16-package-bootstrap/integrated-session.sh','reports/android16-apex-bootstrap/run.py','reports/android16-package-bootstrap/build-platform-overlay.py','tools/apk/SignPlatformOverlay.java','runtime/aosp/platform-overlay/AndroidManifest.xml','runtime/aosp/platform-overlay/res/values/config.xml','runtime/aosp/platform-overlay/overlay-config.xml','reports/android16-apex-bootstrap/devices.py','runtime/aosp/linux-services/initial-apk-profile.json','runtime/aosp/linux-services/org/archtv/aosplinux/SelectedServices.java','runtime/aosp/linux-services/org/archtv/aosplinux/ServiceLauncher.java','runtime/aosp/linux-services/install-markor.sh','runtime/aosp/native/linux-property-worker.cpp','runtime/aosp/native/linux-mc1-cohort.h','reports/android16-package-bootstrap/build-integrated.py','runtime/aosp/android16-qpr2/patches/0004-linux-admitted-lazy-services.patch','fixtures/aosp-keymint-software/SoftwareCryptoProbe.cpp','runtime/aosp/native/linux-keymint-service.cpp','reports/android16-package-bootstrap/build-keymint-software.py','fixtures/aosp-keystore2-software/BinderClient.rs','runtime/aosp/android16-qpr2/patches/keystore2-linux-software.patch','fixtures/aosp-keystore2-software/OriginalJavaProviderProbe.java','runtime/aosp/android16-qpr2/patches/framework-keystore-linux-software.patch','tools/aosp/KeystoreFrameworkProfilePlan.java','tools/aosp/build_software_keystore_framework.py','reports/android16-package-bootstrap/build-keystore-java-probe.py','reports/android16-package-bootstrap/build-gatekeeper-software.py']
tracked_inputs.append('reports/android16-package-bootstrap/userdata.py')
tracked_inputs.append('reports/android16-package-bootstrap/build-bootstrap-xml.py')
tracked_inputs.append('reports/android16-network-bootstrap/boundary.py')
tracked_inputs.extend(['reports/android16-selected-display/build-entry.py','runtime/aosp/linux-services/org/archtv/aosplinux/WaylandInputBridge.java','runtime/aosp/native/linux-wayland-input.h','runtime/aosp/native/linux-wayland-output.cpp','reports/android16-property-actions/apply-patch-chain.py','reports/android16-property-actions/build-lazy-control.py',*[str(p.relative_to(r)) for p in sorted((r/'runtime/aosp/android16-qpr2/patches').glob('000[1-5]-*.patch'))]])
source_hashes={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in tracked_inputs}
(out/'source-inputs.json').write_text(json.dumps(source_hashes,indent=2)+'\n')
actions_source=r/'dist/aosp16/property-actions-source-4'
actions_application=json.loads((actions_source/'application.json').read_text())
for f in actions_application['files']:
 assert hashlib.sha256((actions_source/f['name']).read_bytes()).hexdigest()==f['sha256'],f['name']
for patch in actions_application['patches']:
 assert hashlib.sha256(Path(patch['path']).read_bytes()).hexdigest()==patch['sha256'],patch['path']
actions_archive=json.loads((r/'dist/aosp16/property-actions-build-5/archive.json').read_text())
assert hashlib.sha256(Path(actions_archive['archive']).read_bytes()).hexdigest()==actions_archive['sha256']
(out/'property-runtime-input.json').write_text(json.dumps({'application':actions_application,'archive':actions_archive},indent=2)+'\n')
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
# Original ZygoteInit also grants WAKE_ALARM and KILL: ALARM clocks and
# original AMS cross-UID process shutdown require them in the private PID namespace.
rc=rc.replace('    capabilities SYS_NICE\n','    capabilities SYS_NICE BLOCK_SUSPEND WAKE_ALARM KILL\n')
# Selected system services open the original netd maps by DAC. Reuse only
# the original media_rw and network-accounting groups, from
# pinned ZygoteInit --setgroups; no CAP_BPF or global sysctl exception.
assert rc.count('    group system graphics\n')==1
rc=rc.replace('    group system graphics\n','    group system graphics media_rw net_bw_stats net_bw_acct\n')
lines=rc.splitlines();lines[0]='service archtv-selected-services /system/bin/app_process64 -Xmx768m -Xnoimage-dex2oat /system/bin --application --nice-name=archtv-selected-services org.archtv.aosplinux.ServiceLauncher --packages'
checkpoint_diagnostic='--checkpoint-diagnostic' in sys.argv[2:]
keymint_component='--keymint-component' in sys.argv[2:]
software_platform='--software-security' in sys.argv[2:]
observe_ms=int(next((a.split('=',1)[1] for a in sys.argv[2:] if a.startswith('--observe-ms=')),'3000'))
assert 3000<=observe_ms<=300000
userdata_name=next((a.split('=',1)[1] for a in sys.argv[2:] if a.startswith('--userdata-name=')),None)
assert userdata_name is None or (software_platform and re.fullmatch('[a-z0-9][a-z0-9_-]{0,47}',userdata_name))
workflow_token=next((a.split('=',1)[1] for a in sys.argv[2:] if a.startswith('--markor-workflow-token=')),None)
assert workflow_token is None or (software_platform and observe_ms>=30000 and re.fullmatch('[0-9a-f]{8}',workflow_token))
workflow_budget_seconds=observe_ms//1000-15 if workflow_token else None
keystore_java='--keystore-java-component' in sys.argv[2:] or software_platform
keystore_component='--keystore-component' in sys.argv[2:] or keystore_java
assert not (keymint_component and keystore_component)
if software_platform:
 lines[0]=lines[0].replace('-Xmx768m','-Xmx512m')
 lines.append('    setenv ARCHTV_SOFTWARE_SECURITY_PROFILE software-platform-v1')
experiment_kind='markor-software-launch' if software_platform else 'keystore-java-component' if keystore_java else 'keystore-component' if keystore_component else ('keymint-component' if keymint_component else 'markor-launch')
(out/'build-options.json').write_text(json.dumps({'checkpoint_contract_diagnostic':checkpoint_diagnostic,'keymint_component_diagnostic':keymint_component,'keystore_component_diagnostic':keystore_component and not software_platform,'software_security_platform':software_platform,'observe_ms':observe_ms,'persistent_userdata_name':userdata_name,'markor_workflow_token':workflow_token,'markor_workflow_budget_seconds':workflow_budget_seconds,'experiment_kind':experiment_kind,'original_apex_bootstrap':True,'original_logd':True},indent=2)+'\n')
if checkpoint_diagnostic:lines.append('    setenv ARCHTV_CHECKPOINT_DIAGNOSTIC 1')
lines=[l for l in lines if not any(l.startswith('    setenv '+n+' ') for n in ['BOOTCLASSPATH','DEX2OATBOOTCLASSPATH','SYSTEMSERVERCLASSPATH','STANDALONE_SYSTEMSERVER_JARS'])];(entry/'selected-services.rc').write_text('\n'.join(lines)+'\n')
old=r/'dist/aosp16/apex-cohort-build-6';commands=[]
for n in ['graphics-client']:
 p=out/n;p.parent.mkdir(parents=True,exist_ok=True);shutil.copy2(old/n,p)
def run(argv):
 p=subprocess.run(argv,capture_output=True,text=True);commands.append({'argv':argv,'exit':p.returncode,'stderr':p.stderr});(out/'build.json').write_text(json.dumps({'commands':commands},indent=2));assert p.returncode==0,p.stderr
# Reuse AOSP's complete static XML variant to avoid an ICU/APEX cycle before
# apexd-bootstrap. Shared system/APP XML and ICU remain original and untouched.
xml_out=r/'dist/aosp16/bootstrap-libxml2-1'
if not (xml_out/'artifact.json').exists():
 assert not xml_out.exists(), 'Preserve failed original XML build; choose a new candidate'
 run(['python',str(r/'reports/android16-package-bootstrap/build-bootstrap-xml.py'),str(xml_out)])
xml_record=json.loads((xml_out/'artifact.json').read_text());assert xml_record['terminal']
xml_archive=Path(xml_record['archive']);assert hashlib.sha256(xml_archive.read_bytes()).hexdigest()==xml_record['archive_sha256']
for name,digest in xml_record['source_sha256'].items():assert hashlib.sha256((Path(xml_record['source'])/name).read_bytes()).hexdigest()==digest,name
(out/'bootstrap-xml-input.json').write_text(json.dumps(xml_record,indent=2)+'\n')
# Build the supervisor from the current frozen Rust inputs; never inherit an
# older executable whose CLI/lifetime contract differs from this candidate.
rust_cache=Path('/home/tv/.cache/archtv/native-supervisor-current')
run(['cargo','rustc','--offline','--locked','--manifest-path',str(r/'Cargo.toml'),'-p','archtv-core','--example','native_supervisor','--target-dir',str(rust_cache),'--','-C','link-arg=-Wl,--dynamic-linker,/archtv/lib/ld-linux-x86-64.so.2','-C','link-arg=-Wl,-rpath,/archtv/lib'])
(out/'cargo/debug/examples').mkdir(parents=True,exist_ok=True)
shutil.copy2(rust_cache/'debug/examples/native_supervisor',out/'cargo/debug/examples/native_supervisor')
assert '/archtv/lib/ld-linux-x86-64.so.2' in subprocess.check_output(['readelf','-l',str(out/'cargo/debug/examples/native_supervisor')],text=True), 'Linux payload interpreter contract missing'
for c in json.loads((old/'build.json').read_text())['commands']:
 argv=[a.replace(str(old),str(out)).replace('property-actions-source-2','property-actions-source-4').replace('property-actions-source-3','property-actions-source-4').replace('property-actions-build-3','property-actions-build-5').replace('property-actions-build-4','property-actions-build-5') for a in c['argv']]
 if any(a.endswith('/property-coordinator') for a in argv):
  index=argv.index('--dynamic-linker');assert argv[index+1]=='/system/bin/linker64'
  argv[index+1]='/system/bin/bootstrap/linker64'
  xml_slots=[i for i,a in enumerate(argv) if a.endswith('/system/lib64/libxml2.so')];assert len(xml_slots)==1
  argv[xml_slots[0]]=str(xml_archive)
 run(argv)
assert '[Requesting program interpreter: /system/bin/bootstrap/linker64]' in subprocess.check_output(['readelf','-l',str(out/'property-coordinator')],text=True), 'Original bootstrap interpreter contract missing'
argv=json.loads((r/'reports/android16-hwmanager-cohort/helper-build.json').read_text())['argv'];argv[argv.index('-o')+1]=str(out/'linux-exec-context-image');run(argv)
(out/'artifacts.json').write_text(json.dumps({n:hashlib.sha256((out/n).read_bytes()).hexdigest() for n in ['graphics-client','cargo/debug/examples/native_supervisor','linux-exec-context-image','property-coordinator']},indent=2))
base=r/'dist/aosp16/sf-cohort-build-32';vendor=json.loads((base/'vendor-inputs.json').read_text())
input_hwc=r/'dist/aosp16/hwc3-wayland-input-6'
input_record=json.loads((input_hwc/'build.json').read_text());assert input_record['terminal']
assert hashlib.sha256(Path(input_record['executable']).read_bytes()).hexdigest()==input_record['executable_sha256']
for target,value in vendor['files'].items():
 if value.get('source','').endswith('android.hardware.graphics.composer3-service.archtv-display-2'):value['source']=input_record['executable']
# Original whole libinput, needed by original KeyLayoutMap/updateMetaState.
# Preserve existing vendor modules; add only the exact missing DT_NEEDED
# closure from this same original GSI. Core Bionic/APEX names keep their
# existing linker namespace resolution, never a copied second libc.
import re
original_libs=r/'dist/aosp16/factory-inputs-3/root/system/lib64'
closure={};pending=['libinput.so'];core={'libc.so','libm.so','libdl.so','libdl_android.so','libc++.so'}
while pending:
 name=pending.pop()
 if name in core or name in closure:continue
 target='/vendor/lib64/'+name
 if target in vendor['files']:continue
 source=original_libs/name;assert source.is_file(),('Original input dependency unavailable',name)
 dependencies=re.findall(r'NEEDED.*\[(.*?)\]',subprocess.check_output(['readelf','-d',str(source)],text=True))
 closure[name]={'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'needed':dependencies}
 vendor['files'][target]={'source':str(source),'context':'u:object_r:vendor_file:s0','mode':0o644}
 pending.extend(dependencies)
 assert len(closure)<=64,'Unexpected input dependency expansion'
(out/'wayland-input-library-closure.json').write_text(json.dumps({'scope':'Exact original GSI DT_NEEDED closure only; no runtime/ABI acceptance','core_existing_resolution':sorted(core),'libraries':closure},indent=2)+'\n')
(out/'wayland-input-build.json').write_text(json.dumps(input_record,indent=2)+'\n')
for key,value in vendor['files'].items():
 if key=='/vendor/framework/archtv-selected-services.jar':value['source']=str(entry/'archtv-selected-services.jar')
 if key=='/vendor/etc/init/archtv-selected-services.rc':value['source']=str(entry/'selected-services.rc')
# This Linux profile runs one real 64-bit Zygote. Preserve GSI bytes, but
# declare the implemented device ABI set through the original property loader.
base_props=Path(vendor['files']['/vendor/build.prop']['source']).read_text()
# Keep Linux's audit receiver and kernel reader authoritative; original logd
# still serves its real logd/logdr/logdw channels and drops unused caps.
base_props+='\nro.logd.kernel=false\nro.logd.auditd=false\n'

if keymint_component:
 # Unknown vendor patch level is explicitly empty/zero, never a claimed patch date.
 # The original loader creates the property; KeyMint keeps its original wait guard.
 base_props+='\nro.vendor.build.security_patch=\n'
 probe=r/'dist/aosp16/keymint-software-build-4/keymint-crypto-probe'
 probe_build=json.loads((probe.parent/'probe-build.json').read_text())
 assert probe_build['probe_compile']['exit']==0 and probe_build['probe_link']['exit']==0
 assert probe_build['source_sha256']==hashlib.sha256((r/'fixtures/aosp-keymint-software/SoftwareCryptoProbe.cpp').read_bytes()).hexdigest()
 assert probe_build['binary_sha256']==hashlib.sha256(probe.read_bytes()).hexdigest()
 profile_file=out/'keymint-component-profile';profile_file.write_text('software-crypto-v1\n')
 vendor['files']['/vendor/etc/archtv-keymint-component']={'source':str(profile_file),'context':'u:object_r:vendor_configs_file:s0','mode':0o444}
 vendor['files']['/bin/archtv-keymint-probe']={'source':str(probe),'context':'u:object_r:vendor_file:s0','mode':0o755}
 (out/'keymint-component-input.json').write_text(json.dumps({'probe_sha256':hashlib.sha256(probe.read_bytes()).hexdigest(),'source_sha256':hashlib.sha256((r/'fixtures/aosp-keymint-software/SoftwareCryptoProbe.cpp').read_bytes()).hexdigest(),'scope':'Original crypto component only; unknown vendor patch0, no Keystore or APK acceptance'},indent=2)+'\n')

if keystore_component:
 base_props+='\nro.vendor.build.security_patch=\n'
 source_root=Path('/home/tv/.cache/archtv/keystore2-source-build-1')
 candidate=json.loads((r/'reports/android16-package-bootstrap/keystore2-source-candidate.json').read_text())
 service=Path(candidate['software_candidate']['path'])
 assert hashlib.sha256(service.read_bytes()).hexdigest()==candidate['software_candidate']['sha256']
 client=source_root/'binder-platform/target/x86_64-linux-android/debug/keystore-binder-client'
 client_build=json.loads((source_root/'keystore-binder-client-build.json').read_text());assert client_build['exit']==0
 assert (source_root/'binder-platform/keystore-binder-client/main.rs').read_bytes()==(r/'fixtures/aosp-keystore2-software/BinderClient.rs').read_bytes()
 provider=r/'dist/aosp16/keymint-software-build-3/archtv-keymint-software'
 provider_build=json.loads((provider.parent/'build.json').read_text())
 assert hashlib.sha256(provider.read_bytes()).hexdigest()==provider_build['binary_sha256']
 for item in provider_build['sources']:assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256']
 native_inputs={}
 for name,binary,context in [('archtv-keystore2-software',service,'keystore_exec'),('archtv-keystore-client',client,'shell_exec'),('archtv-keymint-software',provider,'hal_keymint_default_exec')]:
  stripped=out/name;run(['objcopy','--strip-debug',str(binary),str(stripped)])
  native_inputs[name]={'source':str(binary),'source_sha256':hashlib.sha256(binary.read_bytes()).hexdigest(),'deployed_sha256':hashlib.sha256(stripped.read_bytes()).hexdigest(),'transformation':'objcopy --strip-debug; actual deployed bytes not yet executed'}
  vendor['files']['/bin/'+name]={'source':str(stripped),'context':'u:object_r:'+context+':s0','mode':0o755}
 # Preserve original daemon identity, groups, task profile and memlock contract.
 original_rc=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/security-original-full/source/system/security/keystore2/keystore2.rc').read_text()
 assert original_rc.count('service keystore2 /system/bin/keystore2 ')==1
 (out/'keystore.rc').write_text(original_rc.replace('service keystore2 /system/bin/keystore2 ','service archtv-keystore2 /system/bin/keystore2 '))
 provider_rc=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/security-hal-original/source/hardware/interfaces/security/keymint/aidl/default/android.hardware.security.keymint-service.nonsecure.rc').read_text()
 assert provider_rc.count('service vendor.keymint-default /vendor/bin/hw/android.hardware.security.keymint-service.nonsecure')==1
 (out/'keymint.rc').write_text(provider_rc.replace('service vendor.keymint-default /vendor/bin/hw/android.hardware.security.keymint-service.nonsecure','service archtv-keymint-software /archtv-android/archtv-keymint-software'))
 profile=out/'keystore-component-profile';profile.write_text('software-keystore-v1\n')
 manifest=out/'keymint.xml';manifest.write_text('<manifest version="1.0" type="device"><hal format="aidl"><name>android.hardware.security.keymint</name><version>4</version><fqname>IKeyMintDevice/software</fqname></hal></manifest>\n')
 contexts=out/'software-service-contexts';contexts.write_text('android.hardware.security.keymint.IKeyMintDevice/software u:object_r:hal_keymint_service:s0\n')
 # Preserve any existing vendor context mappings before adding our exact instance.
 existing=vendor['files'].get('/vendor/etc/selinux/vendor_service_contexts')
 if existing:contexts.write_text(Path(existing['source']).read_text()+'\n'+contexts.read_text())
 for target,source in [('/vendor/etc/archtv-keystore-component',profile),('/vendor/etc/init/archtv-keystore-software.rc',out/'keystore.rc'),('/vendor/etc/init/archtv-keymint-software.rc',out/'keymint.rc'),('/vendor/etc/vintf/manifest/archtv-software-keymint.xml',manifest),('/vendor/etc/selinux/vendor_service_contexts',contexts)]:
  vendor['files'][target]={'source':str(source),'context':'u:object_r:vendor_configs_file:s0','mode':0o444}
 (out/'keystore-component-inputs.json').write_text(json.dumps({'native':native_inputs,'scope':'Exact candidate bytes and original contracts, not execution/keys/MAC/APK acceptance.'},indent=2)+'\n')
 if software_platform:
  gatekeeper=r/'dist/aosp16/gatekeeper-software-build-2'
  gatekeeper_build=json.loads((gatekeeper/'build.json').read_text());assert gatekeeper_build['terminal']
  gatekeeper_binary=gatekeeper/'android.hardware.gatekeeper-service.nonsecure'
  assert hashlib.sha256(gatekeeper_binary.read_bytes()).hexdigest()==gatekeeper_build['binary_sha256']
  for item in gatekeeper_build['sources']:assert hashlib.sha256(Path(item['path']).read_bytes()).hexdigest()==item['sha256']
  stripped=out/'archtv-gatekeeper-software';run(['objcopy','--strip-debug',str(gatekeeper_binary),str(stripped)])
  native_inputs['archtv-gatekeeper-software']={'source':str(gatekeeper_binary),'source_sha256':gatekeeper_build['binary_sha256'],'deployed_sha256':hashlib.sha256(stripped.read_bytes()).hexdigest(),'transformation':'objcopy --strip-debug; original complete GateKeeper/SharedSecret service'}
  vendor['files']['/bin/archtv-gatekeeper-software']={'source':str(stripped),'context':'u:object_r:hal_gatekeeper_default_exec:s0','mode':0o755}
  source=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/gatekeeper-aidl-original/source/hardware/interfaces/gatekeeper/aidl/software')
  original_rc=(source/'android.hardware.gatekeeper-service.nonsecure.rc').read_text()
  original_entry='/apex/com.android.hardware.gatekeeper/bin/hw/android.hardware.gatekeeper-service.nonsecure'
  assert original_rc.count(original_entry)==1
  rc_path=out/'gatekeeper.rc';rc_path.write_text(original_rc.replace(original_entry,'/archtv-android/archtv-gatekeeper-software'))
  marker=out/'software-platform-profile';marker.write_text('software-platform-v1\n')
  cf=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/cuttlefish-vendor-policy-original/source/device/google/cuttlefish/shared/sepolicy/vendor/service_contexts')
  mapping=[line for line in cf.read_text().splitlines() if line.startswith('android.hardware.security.sharedsecret.ISharedSecret/gatekeeper ')]
  assert len(mapping)==1 and mapping[0].split()[1]=='u:object_r:hal_gatekeeper_service:s0'
  contexts.write_text(contexts.read_text()+mapping[0]+'\n')
  for target,src in [('/vendor/etc/init/archtv-gatekeeper-software.rc',rc_path),('/vendor/etc/archtv-software-security',marker),('/vendor/etc/vintf/manifest/gatekeeper.xml',source/'android.hardware.gatekeeper-service.nonsecure.xml'),('/vendor/etc/vintf/manifest/gatekeeper-sharedsecret.xml',source/'android.hardware.security.sharedsecret-gatekeeper.xml')]:
   vendor['files'][target]={'source':str(src),'context':'u:object_r:vendor_configs_file:s0','mode':0o444}
  # Same immutable native input record now covers all four actual service/client files.
  (out/'keystore-component-inputs.json').write_text(json.dumps({'native':native_inputs,'scope':'Whole original services; entry alias/VINTF adapted outside original vendor APEX, not invented APEX activation or authentication proof'},indent=2)+'\n')
  (out/'gatekeeper-inputs.json').write_text(json.dumps({'original_build':str(gatekeeper/'build.json'),'binary_sha256':gatekeeper_build['binary_sha256'],'contexts_source':str(cf),'source_service_directory':str(source),'scope':'Original RC identity/groups; only exec entry moved from vendor APEX to Linux private alias. No additional APEX inventory claimed.'},indent=2)+'\n')

 if keystore_java:
  framework=r/('dist/aosp16/keystore-framework-profile-2' if software_platform else 'dist/aosp16/keystore-framework-profile-1')
  framework_build=json.loads((framework/'build.json').read_text())
  assert hashlib.sha256((framework/'framework.jar').read_bytes()).hexdigest()==framework_build['output']['sha256']
  assert hashlib.sha256((r/'runtime/aosp/android16-qpr2/patches/framework-keystore-linux-software.patch').read_bytes()).hexdigest()==framework_build['source_patch_sha256']
  assert hashlib.sha256((r/'tools/aosp/KeystoreFrameworkProfilePlan.java').read_bytes()).hexdigest()==framework_build['planner_sha256']
  probe=r/'dist/aosp16/keystore-java-probe-4';probe_build=json.loads((probe/'build.json').read_text())
  assert all(c['exit']==0 for c in probe_build['commands'])
  assert hashlib.sha256((r/'fixtures/aosp-keystore2-software/OriginalJavaProviderProbe.java').read_bytes()).hexdigest()==probe_build['source_sha256']
  assert hashlib.sha256((probe/'probe.jar').read_bytes()).hexdigest()==probe_build['jar_sha256']
  java_marker=out/'java-profile';java_marker.write_text('software-java-profile-v1\n')
  for target,source,context in [('/bin/archtv-keystore-framework.jar',framework/'framework.jar','system_file'),('/vendor/framework/archtv-keystore-probe.jar',probe/'probe.jar','vendor_file'),('/vendor/etc/archtv-keystore-java',java_marker,'vendor_configs_file')]:
   vendor['files'][target]={'source':str(source),'context':'u:object_r:'+context+':s0','mode':0o444}
  (out/'keystore-java-inputs.json').write_text(json.dumps({'framework_sha256':framework_build['output']['sha256'],'original_framework_sha256':framework_build['original']['sha256'],'probe_sha256':probe_build['jar_sha256'],'scope':'Experimental original framework binary profile, not source rebuild or runtime acceptance'},indent=2)+'\n')


if software_platform:
 # Original AndroidRuntime product-property contract; these are private guest
 # properties, not host RAM changes. Apps retain128MiB growth limit; original
 # system-server entry clears growth limit up to bounded512MiB maximum.
 base_props='\n'.join(line for line in base_props.splitlines() if not line.startswith(('dalvik.vm.heapsize=','dalvik.vm.heapgrowthlimit=')))
 base_props+='\ndalvik.vm.heapsize=512m\ndalvik.vm.heapgrowthlimit=128m\n'
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
if workflow_token is not None:
 (out/'markor-workflow-token').write_text(workflow_token+'\n')
 (out/'markor-workflow-budget').write_text(str(workflow_budget_seconds)+'\n')
 vendor['files']['/vendor/etc/archtv-markor-workflow-budget']={'source':str(out/'markor-workflow-budget'),'context':'u:object_r:vendor_configs_file:s0','mode':0o444}
 vendor['files']['/vendor/etc/archtv-markor-workflow-token']={'source':str(out/'markor-workflow-token'),'context':'u:object_r:vendor_configs_file:s0','mode':0o444}
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
# Original logd first service only: do not import boot-completed auditctl
# triggers into a Linux-owned audit subsystem. Kernel/audit readers disabled
# through original supported properties; keep original kmsg write descriptor.
logd_source=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/logging/source/system/logging/logd')
logd_rc=(logd_source/'logd.rc').read_text().split('\nservice logd-reinit ',1)[0]+'\n'
assert logd_rc.count('    file /proc/kmsg r\n')==1
logd_rc=logd_rc.replace('    file /proc/kmsg r\n','')
assert logd_rc.count('    capabilities SYSLOG AUDIT_CONTROL\n')==1
logd_rc=logd_rc.replace('    capabilities SYSLOG AUDIT_CONTROL\n','    capabilities SYSLOG\n')
(out/'linux-logd.rc').write_text(logd_rc)
vendor['files']['/vendor/etc/init/archtv-logd.rc']={'source':str(out/'linux-logd.rc'),'context':'u:object_r:vendor_configs_file:s0','mode':0o644}
(out/'original-logd-inputs.json').write_text(json.dumps({'sources':{str(logd_source/n):hashlib.sha256((logd_source/n).read_bytes()).hexdigest() for n in ['main.cpp','logd.rc']},'binary':{'path':str(r/'dist/aosp16/factory-inputs-3/root/system/bin/logd'),'sha256':hashlib.sha256((r/'dist/aosp16/factory-inputs-3/root/system/bin/logd').read_bytes()).hexdigest()},'adaptation':'First original service, omit unused kernel-read fd and AUDIT_CONTROL; original ro.logd.kernel/auditd false. No auditctl triggers, no original ELF modification. logd still opens kmsg for its own errors; kernel logging is not claimed.'},indent=2)+'\n')
(out/'vendor-inputs.json').write_text(json.dumps(vendor,indent=2))
text=(base/'build-payload-expanded.py').read_text().replace(str(base),str(out));expected=out/'apex-expected.json';expected.write_text(json.dumps(json.loads((r/'reports/android16-apex-bootstrap/complete-inputs.json').read_text())['modules'],indent=2)+'\n');text=text.replace("image=out/'payload-2.ext4'", "record('/apex-expected.json',out/'apex-expected.json','u:object_r:vendor_configs_file:s0',0o600)\nimage=out/'payload-2.ext4'")
old_parent="record('/'+str(parent.relative_to(tree)),None,'u:object_r:vendor_file:s0',0o755)"
assert old_parent in text
text=text.replace(old_parent,"record('/'+str(parent.relative_to(tree)),None,'u:object_r:vendor_overlay_file:s0' if path.startswith('/vendor/overlay/') else 'u:object_r:vendor_file:s0',0o755)")
recipe=out/'build-payload.py';recipe.write_text(text);subprocess.run(['python',str(recipe)],stdout=open(out/'packager.log','w'),stderr=subprocess.STDOUT,check=True)
assert all(hashlib.sha256((r/n).read_bytes()).hexdigest()==h for n,h in source_hashes.items()), 'Source changed during build'
print(out,flush=True)
