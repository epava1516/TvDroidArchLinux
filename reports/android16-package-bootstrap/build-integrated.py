#!/usr/bin/env python3
"""Build a coherent experimental original APEX/graphics/package cohort, no boot."""
from pathlib import Path
import json,subprocess,shutil,hashlib,sys,re
r=Path(__file__).resolve().parents[2]
# Reject typos before creating artifacts: omitted memory/media inputs change the candidate.
allowed_flags = {'--checkpoint-diagnostic', '--keymint-component', '--keystore-component',
                 '--keystore-java-component', '--software-security', '--native-audio',
                 '--audio-write-diagnostic', '--audio-synchronous-pcm', '--audio-production-dynamics', '--coherent-art', '--coherent-art-images',
                 '--memfd-label-original', '--media-test', '--audio-only-media', '--markor-home-launch', '--audio-pcm-observation', '--timecoded-media', '--media-home-launch'}
allowed_values = ('--observe-ms=', '--userdata-name=', '--apk-id=', '--markor-workflow-token=', '--markor-normal-close-token=', '--audio-period-size-multiplier=')
assert all(a in allowed_flags or any(a.startswith(prefix) for prefix in allowed_values)
           for a in sys.argv[2:]), 'Unknown integrated build option'
audio_period_values=[a.split('=',1)[1] for a in sys.argv[2:] if a.startswith('--audio-period-size-multiplier=')]
assert len(audio_period_values)<=1 and all(v in ('1','2','4') for v in audio_period_values), 'Choose one bounded original ALSA period multiplier (1, 2 or 4)'
assert not audio_period_values or '--native-audio' in sys.argv[2:], 'ALSA period profile requires original native audio'
audio_period_size_multiplier=int(audio_period_values[0]) if audio_period_values else 1
audio_pcm_observation='--audio-pcm-observation' in sys.argv[2:]
assert not audio_pcm_observation or all(a in sys.argv[2:] for a in (
    '--native-audio', '--audio-synchronous-pcm', '--media-test', '--apk-id=vlc'))
assert not audio_pcm_observation or '--audio-only-media' not in sys.argv[2:]
timecoded_media='--timecoded-media' in sys.argv[2:]
media_home_launch='--media-home-launch' in sys.argv[2:]
assert not media_home_launch or all(a in sys.argv[2:] for a in ('--media-test','--apk-id=vlc'))
assert not timecoded_media or all(a in sys.argv[2:] for a in ('--media-test','--apk-id=vlc'))
assert not timecoded_media or '--audio-only-media' not in sys.argv[2:]
out=(r/sys.argv[1]).resolve();out.mkdir()
tracked_inputs=['Cargo.toml','Cargo.lock','crates/archtv-core/Cargo.toml',*[str(p.relative_to(r)) for p in sorted((r/'crates/archtv-core/src').rglob('*.rs'))],'crates/archtv-core/examples/native_supervisor.rs','reports/android16-package-bootstrap/execute-integrated.py','reports/android16-package-bootstrap/integrated-session.sh','reports/android16-apex-bootstrap/run.py','reports/android16-package-bootstrap/build-platform-overlay.py','tools/apk/SignPlatformOverlay.java','runtime/aosp/platform-overlay/AndroidManifest.xml','runtime/aosp/platform-overlay/res/values/config.xml','runtime/aosp/platform-overlay/overlay-config.xml','reports/android16-apex-bootstrap/devices.py','runtime/aosp/linux-services/initial-apk-profile.json','runtime/aosp/linux-services/org/archtv/aosplinux/SelectedServices.java','runtime/aosp/linux-services/org/archtv/aosplinux/ServiceLauncher.java','runtime/aosp/linux-services/install-markor.sh','runtime/aosp/native/linux-property-worker.cpp','runtime/aosp/native/linux-mc1-cohort.h','reports/android16-package-bootstrap/build-integrated.py','runtime/aosp/android16-qpr2/patches/0004-linux-admitted-lazy-services.patch','fixtures/aosp-keymint-software/SoftwareCryptoProbe.cpp','runtime/aosp/native/linux-keymint-service.cpp','reports/android16-package-bootstrap/build-keymint-software.py','fixtures/aosp-keystore2-software/BinderClient.rs','runtime/aosp/android16-qpr2/patches/keystore2-linux-software.patch','fixtures/aosp-keystore2-software/OriginalJavaProviderProbe.java','runtime/aosp/android16-qpr2/patches/framework-keystore-linux-software.patch','tools/aosp/KeystoreFrameworkProfilePlan.java','tools/aosp/build_software_keystore_framework.py','reports/android16-package-bootstrap/build-keystore-java-probe.py','reports/android16-package-bootstrap/build-gatekeeper-software.py']
tracked_inputs.extend(['reports/android16-package-bootstrap/userdata.py','reports/android16-hwc3-wayland/build-minigbm.py','reports/android16-hwc3-wayland/link-minigbm.py'])
tracked_inputs.append('reports/android16-package-bootstrap/build-bootstrap-xml.py')
tracked_inputs.append('tools/aosp/prepare_host_labels.py')
tracked_inputs.extend(['runtime/aosp/linux-services/archtv/runtime/SelectedRuntime.java','tools/aosp/ZygoteSelectedEntryPlan.java','tools/aosp/build_selected_zygote_framework.py','reports/android16-selected-display/build-entry.py','runtime/aosp/android16-qpr2/patches/framework-zygote-selected-entry.patch'])
tracked_inputs.extend(['runtime/aosp/protocols/archtv-launcher-v1.xml','runtime/aosp/native/linux-launcher-control.h','runtime/aosp/linux-services/org/archtv/aosplinux/LauncherControlBridge.java','runtime/aosp/linux-services/org/archtv/aosplinux/TaskFocusObserver.java','tools/aosp/TaskStackObserverGlue.java','runtime/aosp/native/linux-wayland-task-protocol.h'])
tracked_inputs.append('reports/android16-network-bootstrap/boundary.py')
tracked_inputs.append('scripts/run_completion.py')
tracked_inputs.extend(['reports/android16-package-bootstrap/build-libcutils-memory.py','runtime/aosp/android16-qpr2/patches/libcutils-memfd-original-label.patch','runtime/aosp/android16-qpr2/patches/libcutils-memfd-original-label.json'])
tracked_inputs.extend(['runtime/aosp/native/linux-wayland-frame-composer.cpp','runtime/aosp/native/linux-wayland-frame-composer.h','reports/android16-hwc3-wayland/build-input.py'])
tracked_inputs.extend(['reports/android16-selected-display/build-entry.py','runtime/aosp/linux-services/org/archtv/aosplinux/WaylandInputBridge.java','runtime/aosp/native/linux-wayland-input.h','runtime/aosp/native/linux-wayland-output.cpp','reports/android16-property-actions/apply-patch-chain.py','reports/android16-property-actions/build-lazy-control.py',*[str(p.relative_to(r)) for p in sorted((r/'runtime/aosp/android16-qpr2/patches').glob('000[1-5]-*.patch'))]])
tracked_inputs.append('reports/android16-audio-bootstrap/prepare-linux-profile.py')
tracked_inputs.extend(['reports/android16-audio-bootstrap/build-support.py','reports/android16-audio-bootstrap/link-effect.py'])
tracked_inputs.extend(['reports/android16-audio-bootstrap/build-linux-primary.py','reports/android16-audio-bootstrap/link-linux-core.py','runtime/aosp/android16-qpr2/patches/audio-alsa-write-observation.patch','runtime/aosp/android16-qpr2/patches/audio-alsa-write-observation.json'])
tracked_inputs.extend(['runtime/aosp/android16-qpr2/patches/audio-alsa-synchronous-pcm.patch','runtime/aosp/android16-qpr2/patches/audio-alsa-synchronous-pcm.json'])
tracked_inputs.extend(['runtime/aosp/native/linux-pcm-observation.h','runtime/aosp/android16-qpr2/patches/audio-alsa-pcm-observation.patch','runtime/aosp/android16-qpr2/patches/audio-alsa-pcm-observation.json'])
tracked_inputs.extend(['runtime/aosp/android16-qpr2/patches/odsign-x509-initialization.patch','runtime/aosp/android16-qpr2/patches/odsign-x509-initialization.json','reports/android16-package-bootstrap/build-odsign-software.py','reports/android16-package-bootstrap/link-odsign-software.py','runtime/aosp/android16-qpr2/patches/odsign-explicit-software.patch','runtime/aosp/android16-qpr2/patches/odsign-explicit-software.json'])
tracked_inputs.extend(['reports/android16-package-bootstrap/build-keystore-boot-profile.py','runtime/aosp/android16-qpr2/patches/keystore2-software-boot-level.patch','runtime/aosp/android16-qpr2/patches/keystore2-software-boot-level.json'])
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
overlay=r/'dist/aosp16/platform-overlay-build-3'
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
coherent_art='--coherent-art' in sys.argv[2:]
assert not coherent_art or software_platform
coherent_art_images='--coherent-art-images' in sys.argv[2:]
assert not coherent_art_images or coherent_art
native_audio='--native-audio' in sys.argv[2:]
assert not native_audio or software_platform
audio_write_diagnostic='--audio-write-diagnostic' in sys.argv[2:]
assert not audio_write_diagnostic or native_audio
audio_synchronous_pcm='--audio-synchronous-pcm' in sys.argv[2:]
assert not audio_synchronous_pcm or native_audio
assert not (audio_write_diagnostic and audio_synchronous_pcm)
audio_production_dynamics='--audio-production-dynamics' in sys.argv[2:]
assert not audio_production_dynamics or native_audio
observe_ms=int(next((a.split('=',1)[1] for a in sys.argv[2:] if a.startswith('--observe-ms=')),'3000'))
# Real262 used the entire300s window on original onboarding/storage UI.
# Keep startup separately bounded; allow at most600s of actual interaction.
assert 3000<=observe_ms<=600000
userdata_name=next((a.split('=',1)[1] for a in sys.argv[2:] if a.startswith('--userdata-name=')),None)
assert userdata_name is None or (software_platform and re.fullmatch('[a-z0-9][a-z0-9_-]{0,47}',userdata_name))
assert not coherent_art or userdata_name is not None
# Select an intact real APK from the existing compatibility matrix. This is
# trusted external installer input, never PMS inventory or a permission seed.
apk_id=next((a.split('=',1)[1] for a in sys.argv[2:] if a.startswith('--apk-id=')),'markor')
applications=json.loads((r/'reports/arquitectura-apk-20261030/compatibility-matrix.json').read_text())['applications']
selected=next(a for a in applications if a['id']==apk_id)
apk_target={k:selected[k] for k in ['id','package','path_local','sha256']}
assert re.fullmatch(r'[a-zA-Z][a-zA-Z0-9_]*(?:\.[a-zA-Z][a-zA-Z0-9_]*)+',apk_target['package'])
assert re.fullmatch('[0-9a-f]{64}',apk_target['sha256'])
assert hashlib.sha256(Path(apk_target['path_local']).read_bytes()).hexdigest()==apk_target['sha256']
assert software_platform or apk_id=='markor'
memory_library=None
if '--memfd-label-original' in sys.argv[2:]:
 assert software_platform
 memory_path=r/'dist/aosp16/libcutils-memfd-linux-2/libcutils.so'
 memory_build=json.loads((memory_path.parent/'build.json').read_text())
 assert memory_build['terminal'] and memory_build['sha256']=='c960f7e332b1e6f42f69a8ca73d81b2bc6ffd538bc424e3fdb5ad7701dc99180'
 assert hashlib.sha256(memory_path.read_bytes()).hexdigest()==memory_build['sha256']
 for source,expected in memory_build['inputs'].items():assert hashlib.sha256(Path(source).read_bytes()).hexdigest()==expected,source
 memory_library={'path':str(memory_path),'sha256':memory_build['sha256'],'payload_path':'/bin/archtv-libcutils-memory.so','scope':'Experimental original libcutils memory-label backport; not APK/security acceptance'}
media_test=None
audio_only_media='--audio-only-media' in sys.argv[2:]
assert not audio_only_media or '--media-test' in sys.argv[2:]
if '--media-test' in sys.argv[2:]:
 assert software_platform and apk_id=='vlc'
 media_manifest=Path('/home/tv/.cache/archtv/media-test-assets/archtv-vlc-testsrc2-sine-4s.json')
 media_record=json.loads(media_manifest.read_text())
 media_test={k:media_record[k] for k in ['path','sha256','bytes']}
 assert media_test['sha256']=='30fc8da5b0511c723c434cc13b3635507d7caae0b0d137c1f87aecbe6d1d4e17'
 assert media_test['bytes']==420785 and hashlib.sha256(Path(media_test['path']).read_bytes()).hexdigest()==media_test['sha256']
 if timecoded_media:
  media_manifest=Path('/home/tv/.cache/archtv/media-test-assets/archtv-vlc-chirp-4s.json')
  media_record=json.loads(media_manifest.read_text())
  media_test={k:media_record[k] for k in ['path','sha256','bytes']}
  assert media_test['sha256']=='955fb736cff6316c063a36615962f807bf1c2e41b4ef48f4595141d4483f6dfe'
  assert media_test['bytes']==498232 and hashlib.sha256(Path(media_test['path']).read_bytes()).hexdigest()==media_test['sha256']
  reference=media_record['reference']
  assert reference['sha256']=='122b47920fea0b78e73301660761039b55673a965efdcfdb3e86d5df2a0db75f'
  assert reference['bytes']==768000 and hashlib.sha256(Path(reference['path']).read_bytes()).hexdigest()==reference['sha256']
  media_test['reference_manifest']=str(media_manifest)
  media_test['reference_manifest_sha256']=hashlib.sha256(media_manifest.read_bytes()).hexdigest()
 media_test['display_name']='archtv-test-'+media_test['sha256'][:8]+'.mp4'
 if audio_only_media:
  media_manifest=Path('/home/tv/.cache/archtv/media-test-assets/archtv-vlc-audio-only-4s.json')
  media_record=json.loads(media_manifest.read_text())
  media_test={k:media_record[k] for k in ['path','sha256','bytes']}
  assert media_test['sha256']=='0b0a63604759b9e1a885442117d0ede6c78ab76a80e8426df522198dfef7b2fb'
  assert media_test['bytes']==36483 and hashlib.sha256(Path(media_test['path']).read_bytes()).hexdigest()==media_test['sha256']
  assert media_record['source']['sha256']=='30fc8da5b0511c723c434cc13b3635507d7caae0b0d137c1f87aecbe6d1d4e17'
  assert {x['sha256'] for x in media_record['decoded_pcm_reference']}=={'56a33b919e06bff9aad2b2390a0377bb49130deb25d8bdc5b09451a1019bcb3a'}
  media_test['display_name']='archtv-test-'+media_test['sha256'][:8]+'.m4a'
  media_test['reference_manifest']=str(media_manifest)
  media_test['reference_manifest_sha256']=hashlib.sha256(media_manifest.read_bytes()).hexdigest()

workflow_token=next((a.split('=',1)[1] for a in sys.argv[2:] if a.startswith('--markor-workflow-token=')),None)
assert workflow_token is None or (apk_id=='markor' and software_platform and observe_ms>=30000 and re.fullmatch('[0-9a-f]{8}',workflow_token))
workflow_budget_seconds=observe_ms//1000-15 if workflow_token else None
normal_close_token=next((a.split('=',1)[1] for a in sys.argv[2:] if a.startswith('--markor-normal-close-token=')),None)
assert normal_close_token is None or (apk_id=='markor' and software_platform and observe_ms>=30000 and re.fullmatch('[0-9a-f]{8}',normal_close_token))
assert not (workflow_token and normal_close_token), 'Forced and normal close experiments must remain separate'
normal_close_budget_seconds=observe_ms//1000-15 if normal_close_token else None
home_launch='--markor-home-launch' in sys.argv[2:]
assert not home_launch or normal_close_token is not None
keystore_java='--keystore-java-component' in sys.argv[2:] or software_platform
keystore_component='--keystore-component' in sys.argv[2:] or keystore_java
assert not (keymint_component and keystore_component)
if software_platform:
 lines[0]=lines[0].replace('-Xmx768m','-Xmx512m')
 lines.append('    setenv ARCHTV_SOFTWARE_SECURITY_PROFILE software-platform-v1')
experiment_kind='markor-software-launch' if software_platform else 'keystore-java-component' if keystore_java else 'keystore-component' if keystore_component else ('keymint-component' if keymint_component else 'markor-launch')
(out/'build-options.json').write_text(json.dumps({'apk_target':apk_target,'media_test':media_test,'coherent_art':coherent_art,'coherent_art_images':coherent_art_images,'memory_library':memory_library,'checkpoint_contract_diagnostic':checkpoint_diagnostic,'keymint_component_diagnostic':keymint_component,'keystore_component_diagnostic':keystore_component and not software_platform,'software_security_platform':software_platform,'observe_ms':observe_ms,'persistent_userdata_name':userdata_name,'markor_workflow_token':workflow_token,'markor_workflow_budget_seconds':workflow_budget_seconds,'markor_home_launch':home_launch,'markor_normal_close_token':normal_close_token,'markor_normal_close_budget_seconds':normal_close_budget_seconds,'experiment_kind':experiment_kind,'original_apex_bootstrap':True,'original_logd':True,'preconnected_wayland':True,'original_system_dma_heap':True,'native_audio':native_audio,'audio_write_diagnostic':audio_write_diagnostic,'audio_synchronous_pcm':audio_synchronous_pcm,'audio_production_dynamics':audio_production_dynamics,'audio_period_size_multiplier':audio_period_size_multiplier,'audio_pcm_observation':audio_pcm_observation,'timecoded_media':timecoded_media,'media_home_launch':media_home_launch},indent=2)+'\n')
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
input_hwc=r/'dist/aosp16/hwc3-launcher-356b'
input_record=json.loads((input_hwc/'build.json').read_text());assert input_record['terminal']
assert hashlib.sha256(Path(input_record['executable']).read_bytes()).hexdigest()==input_record['executable_sha256']
for source,digest in input_record['inputs'].items():
 if Path(source).is_relative_to(r/'runtime/aosp'):
  assert hashlib.sha256(Path(source).read_bytes()).hexdigest()==digest,source
for target,value in vendor['files'].items():
 if value.get('source','').endswith('android.hardware.graphics.composer3-service.archtv-display-2'):value['source']=input_record['executable']
# The Linux seat HAL uses the original complete KeyLayoutMap implementation.
# Actual265 correctly denied its access to generic system_file/Generic.kl.
# Supply identical original GSI data as readonly device configuration, using
# the existing vendor_configs_file contract; never grant generic system reads
# or replace the original table/parser with a handwritten keycode map.
keylayout=r/'dist/aosp16/factory-inputs-3/root/system/usr/keylayout/Generic.kl'
keylayout_target='/vendor/usr/keylayout/Generic.kl'
assert keylayout.is_file() and keylayout_target not in vendor['files']
vendor['files'][keylayout_target]={'source':str(keylayout),'context':'u:object_r:vendor_configs_file:s0','mode':0o444}
(out/'original-keylayout-input.json').write_text(json.dumps({'source':str(keylayout),'sha256':hashlib.sha256(keylayout.read_bytes()).hexdigest(),'target':keylayout_target,'context':'u:object_r:vendor_configs_file:s0','mode':'0444','scope':'Original AOSP Generic.kl bytes unchanged; original KeyLayoutMap, readonly vendor device configuration, not keyboard execution acceptance'},indent=2)+'\n')
# Preserve original generic minigbm heap path, all four modules from one build.
minigbm=r/'dist/aosp16/minigbm-native-link-6'
minigbm_record=json.loads((minigbm/'link.json').read_text());assert minigbm_record['terminal']
source_build=minigbm_record['source_build'];assert source_build['original_generic_dma_heap']
assert hashlib.sha256(Path(source_build['path']).read_bytes()).hexdigest()==source_build['sha256']
for row in minigbm_record['artifacts']:
 assert hashlib.sha256(Path(row['path']).read_bytes()).hexdigest()==row['sha256']
 name=Path(row['path']).name
 target='/vendor/bin/hw/'+name if not name.endswith('.so') else '/vendor/lib64/'+('hw/' if name=='mapper.minigbm.so' else '')+name
 assert target in vendor['files'],target
 vendor['files'][target]['source']=row['path']
(out/'minigbm-input.json').write_text(json.dumps(minigbm_record,indent=2)+'\n')
# Original whole libinput, needed by original KeyLayoutMap/updateMetaState.
# Preserve existing vendor modules; add only the exact missing DT_NEEDED
# closure from this same original GSI. Core Bionic/APEX names keep their
# existing linker namespace resolution, never a copied second libc.
import re
original_libs=r/'dist/aosp16/factory-inputs-3/root/system/lib64'
closure={};pending=['libinput.so','libdmabufheap.so'];core={'libc.so','libm.so','libdl.so','libdl_android.so','libc++.so'}
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
# The mapper executes inside framework clients. Its complete vendor-side
# dependency closure shares the existing SP-HAL code role, never vendor_file.
# In particular the newly active heap library must not get an ambient SF grant.
sphal={};pending=['mapper.minigbm.so']
while pending:
 name=pending.pop()
 if name in core or name in sphal:continue
 target='/vendor/lib64/'+('hw/' if name=='mapper.minigbm.so' else '')+name
 if target not in vendor['files']:continue # existing shared system namespace
 item=vendor['files'][target];source=Path(item['source'])
 needed=re.findall(r'NEEDED.*\[(.*?)\]',subprocess.check_output(['readelf','-d',str(source)],text=True))
 sphal[name]={'target':target,'source':str(source),'sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'previous_context':item['context'],'needed':needed}
 item['context']='u:object_r:same_process_hal_file:s0'
 pending.extend(needed)
 assert len(sphal)<=64,'Unexpected mapper dependency expansion'
assert 'libdmabufheap.so' in sphal,'Original heap provider not in mapper closure'
(out/'mapper-library-role.json').write_text(json.dumps({'scope':'Complete vendor SP-HAL code dependency role; original HAL client policy remains unchanged, no runtime or ABI acceptance inferred.','libraries':sphal},indent=2)+'\n')
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
 if coherent_art:
  boot_record_path=r/'dist/aosp16/keystore-boot-profile-build-2/build.json'
  boot_record=json.loads(boot_record_path.read_text())
  assert boot_record['exit']==0 and boot_record['workspace_sources_restored']
  boot_patch=r/'runtime/aosp/android16-qpr2/patches/keystore2-software-boot-level.patch'
  assert hashlib.sha256(boot_patch.read_bytes()).hexdigest()==boot_record['patch_sha256']
  for source,digest in boot_record['sources'].items():
   assert hashlib.sha256((boot_record_path.parent/Path(source).name).read_bytes()).hexdigest()==digest
  service=Path(boot_record['binary'])
  assert hashlib.sha256(service.read_bytes()).hexdigest()==boot_record['binary_sha256']
  (out/'keystore-boot-input.json').write_text(json.dumps(boot_record,indent=2)+'\n')

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
  if software_platform:
   composition=r/'dist/aosp16/selected-zygote-framework-7'
   composed=json.loads((composition/'build.json').read_text())
   assert composed['parent_sha256']==framework_build['output']['sha256']
   assert hashlib.sha256((composition/'framework.jar').read_bytes()).hexdigest()==composed['output_sha256']
   assert hashlib.sha256((r/'tools/aosp/build_selected_zygote_framework.py').read_bytes()).hexdigest()==composed['builder_sha256']
   assert hashlib.sha256((r/'tools/aosp/ZygoteSelectedEntryPlan.java').read_bytes()).hexdigest()==composed['planner_sha256']
   framework=composition
   framework_build={**framework_build,'output':{'sha256':composed['output_sha256'],'path':str(composition/'framework.jar')}}
   (out/'selected-zygote-framework.json').write_text(json.dumps(composed,indent=2)+'\n')
   assert composed['changes'][0]['after']=='archtv.runtime.SelectedRuntime'
   marker=out/'selected-systemserver-profile';marker.write_text('selected-zygote-entry-v1\narchtv.runtime.SelectedRuntime\n')
   vendor['files']['/vendor/etc/archtv-selected-systemserver-profile']={'source':str(marker),'context':'u:object_r:vendor_configs_file:s0','mode':0o444}
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
# System-owned ABI globals must enter through an original system partition
# property source, not vendor_init. Preserve the original system_ext profile.
abi_properties={'ro.product.cpu.abilist':'x86_64','ro.product.cpu.abilist64':'x86_64',
                'ro.product.cpu.abilist32':'','ro.zygote':'zygote64',
                'service.sf.prime_shader_cache':'false'}
# Original libalsautils owns this property and real PCM negotiation. The default
# stays absent/1; a larger private device ring never changes errors, clocks or
# the number of frames actually written. Host358 small/large controls motivate
# testing 4, but cannot establish Android playback or source-signal continuity.
audio_period_contract=None
if audio_period_size_multiplier!=1:
 support=json.loads((r/'dist/aosp16/audio-support-build-2/build.json').read_text())
 profiles=[s for s in support['sources'] if s['path'].endswith('/alsa_device_profile.c')]
 assert len(profiles)==1
 audio_period_contract=profiles[0]
 assert hashlib.sha256(Path(audio_period_contract['path']).read_bytes()).hexdigest()==audio_period_contract['sha256']
 assert '"ro.hardware.audio.tinyalsa.period_size_multiplier", 1' in Path(audio_period_contract['path']).read_text()
 abi_properties['ro.hardware.audio.tinyalsa.period_size_multiplier']=str(audio_period_size_multiplier)
base_props='\n'.join(line for line in base_props.splitlines() if line.partition('=')[0] not in abi_properties)
(out/'linux-build.prop').write_text(base_props+'\n')
original_props=r/'dist/aosp16/factory-inputs-3/root/system/system_ext/etc/build.prop'
original_bytes=original_props.read_bytes()
assert not any(line.partition('=')[0] in abi_properties for line in original_bytes.decode().splitlines())
profile_bytes=original_bytes+b'\n# Linux private single64 device profile; no 32-bit/ARM execution claimed.\n'+''.join(k+'='+v+'\n' for k,v in abi_properties.items()).encode()
(out/'system-ext-build.prop').write_bytes(profile_bytes)
vendor['files']['/system_ext/etc/build.prop']={'source':str(out/'system-ext-build.prop'),'context':'u:object_r:system_file:s0','mode':0o444}
(out/'system-property-profile.json').write_text(json.dumps({'original':str(original_props),'original_sha256':hashlib.sha256(original_bytes).hexdigest(),'profile_sha256':hashlib.sha256(profile_bytes).hexdigest(),'properties':abi_properties,'audio_period_contract':audio_period_contract,'scope':'Private Linux device profile through original PropertyLoadBootDefaults canonical system_ext source; no host properties, policy grants, APK or 32-bit compatibility acceptance.'},indent=2)+'\n')
vendor['files']['/vendor/build.prop']['source']=str(out/'linux-build.prop')
vendor['files']['/vendor/overlay/ArchTvPlatform/ArchTvPlatform.apk']={'source':str(overlay/'ArchTvPlatform.apk'),'context':'u:object_r:vendor_overlay_file:s0','mode':0o644}
vendor['files']['/vendor/overlay/config/config.xml']={'source':str(r/'runtime/aosp/platform-overlay/overlay-config.xml'),'context':'u:object_r:vendor_overlay_file:s0','mode':0o644}
vendor['files']['/vendor/framework/archtv-selected-services.jar']['context']='u:object_r:system_file:s0'
profile=json.loads((r/'runtime/aosp/linux-services/initial-apk-profile.json').read_text())
profile_lines=[]
for item in profile['excluded']:
 source=r/'dist/aosp16/factory-inputs-3/root'/item['apk'].lstrip('/')
 assert source.stat().st_size==item['bytes'] and hashlib.file_digest(source.open('rb'),'sha256').hexdigest()==item['sha256'],item['apk']
 profile_lines.append('\t'.join([item['package'],str(Path(item['apk']).parent),Path(item['apk']).name,item['sha256'],str(item['bytes']),str(item['uid']),str(item['gid']),str(item['directory_uid']),str(item['directory_gid'])]))
(out/'initial-apk-profile.tsv').write_text('\n'.join(profile_lines)+'\n')
vendor['files']['/vendor/etc/archtv-initial-apk-profile.tsv']={'source':str(out/'initial-apk-profile.tsv'),'context':'u:object_r:vendor_configs_file:s0','mode':0o400}
for experiment,token,budget in [('workflow',workflow_token,workflow_budget_seconds),('normal-close',normal_close_token,normal_close_budget_seconds)]:
 if token is not None:
  for field,value in [('token',token),('budget',str(budget))]:
   name='markor-'+experiment+'-'+field
   (out/name).write_text(value+'\n')
   vendor['files']['/vendor/etc/archtv-'+name]={'source':str(out/name),'context':'u:object_r:vendor_configs_file:s0','mode':0o444}
if home_launch:
 (out/'markor-home-launch').write_text('1\n')
 vendor['files']['/vendor/etc/archtv-markor-home-launch']={'source':str(out/'markor-home-launch'),'context':'u:object_r:vendor_configs_file:s0','mode':0o444}
if memory_library is not None:
 vendor['files'][memory_library['payload_path']]={'source':memory_library['path'],'context':'u:object_r:system_lib_file:s0','mode':0o444}
if media_home_launch:
 (out/'media-home-launch').write_text('1\n')
 vendor['files']['/vendor/etc/archtv-media-home-launch']={'source':str(out/'media-home-launch'),'context':'u:object_r:vendor_configs_file:s0','mode':0o444}
if media_test is not None:
 (out/'media-test-name').write_text(media_test['display_name']+'\n')
 vendor['files']['/vendor/etc/archtv-media-test-name']={'source':str(out/'media-test-name'),'context':'u:object_r:vendor_configs_file:s0','mode':0o444}
(out/'install-package').write_text(apk_target['package']+'\n')
vendor['files']['/vendor/etc/archtv-install-package']={'source':str(out/'install-package'),'context':'u:object_r:vendor_configs_file:s0','mode':0o444}
if coherent_art:
 art_link=r/'dist/aosp16/odsign-software-link-3'
 art_record=json.loads((art_link/'link.json').read_text())
 assert art_record['status']=='linked_not_executed'
 assert hashlib.sha256(Path(art_record['source_build']).read_bytes()).hexdigest()==art_record['source_build_sha256']
 assert len(art_record['source_corrections'])==1
 assert art_record['source_corrections'][0]['patch_sha256']==hashlib.sha256((r/'runtime/aosp/android16-qpr2/patches/odsign-x509-initialization.patch').read_bytes()).hexdigest()
 art_binary=Path(art_record['binary'])
 assert hashlib.sha256(art_binary.read_bytes()).hexdigest()==art_record['binary_sha256']
 for path,digest in art_record['inputs'].items():assert hashlib.sha256(Path(path).read_bytes()).hexdigest()==digest,path
 fc=r/'dist/aosp16/factory-inputs-3/root/system/etc/selinux/plat_file_contexts'
 fc_lines=[l.split() for l in fc.read_text().splitlines() if l.strip() and not l.lstrip().startswith('#')]
 roots=[]
 for path,mode,uid,gid,original_type in [('misc/odrefresh',0o777,1000,1000,'odrefresh_data_file'),('misc/odsign',0o710,0,1000,'odsign_data_file'),('misc/odsign/metrics',0o770,0,1000,'odsign_metrics_file'),('misc/apexdata/com.android.art',0o700,0,0,'apex_art_data_file')]:
  context='u:object_r:'+original_type+':s0'
  rows=[l for l in fc_lines if l[-1]==context and l[0].startswith('/data/misc/')]
  assert len(rows)==1,(path,rows)
  roots.append({'path':path,'mode':mode,'uid':uid,'gid':gid,'context':context,'original_regex':rows[0][0]})
 art_record['private_data_roots']=roots
 art_record['file_contexts_source']={'path':str(fc),'sha256':hashlib.sha256(fc.read_bytes()).hexdigest()}
 (out/'coherent-art-input.json').write_text(json.dumps(art_record,indent=2)+'\n')
 if coherent_art_images:
  # Reuse the original profman-produced profile; never rewrite DEX checksums.
  profile_result=r/'dist/aosp16/art-profile-coherence-1/profile-result.json'
  profile_record=json.loads(profile_result.read_text())
  assert profile_record['original_descriptors']==profile_record['roundtrip_descriptors']==52539
  assert not profile_record['missing_descriptors'] and not profile_record['extra_descriptors']
  assert len(profile_record['dex_checks'])==18 and all(x['matches'] for x in profile_record['dex_checks'])
  for original in profile_record['original_apks']:
   assert hashlib.sha256(Path(original['path']).read_bytes()).hexdigest()==original['sha256'],original['path']
  generated=Path(profile_record['profile'])
  assert hashlib.sha256(generated.read_bytes()).hexdigest()==profile_record['profile_sha256']
  adapted=profile_record['adapted_framework']
  assert hashlib.sha256(Path(adapted['path']).read_bytes()).hexdigest()==adapted['sha256']
  assert vendor['files']['/bin/archtv-keystore-framework.jar']['source']==adapted['path']
  (out/'regenerated-art-profile-input.json').write_text(json.dumps({'result':str(profile_result),'result_sha256':hashlib.sha256(profile_result.read_bytes()).hexdigest(),'profile_sha256':profile_record['profile_sha256'],'framework_sha256':adapted['sha256'],'scope':'Profile artifact only; original odrefresh must generate/sign/load images at runtime; no acceptance from packaging'},indent=2)+'\n')
  vendor['files']['/bin/archtv-framework-boot-image.prof']={'source':str(generated),'context':'u:object_r:system_file:s0','mode':0o444}
 (out/'coherent-art-profile').write_text('software-signed-cache-v1\n')
 vendor['files']['/bin/archtv-odsign-software']={'source':str(art_binary),'context':'u:object_r:odsign_exec:s0','mode':0o755}
 vendor['files']['/vendor/etc/archtv-coherent-art']={'source':str(out/'coherent-art-profile'),'context':'u:object_r:vendor_configs_file:s0','mode':0o444}
vendor['files']['/vendor/bin/install-markor.sh']={'source':str(r/'runtime/aosp/linux-services/install-markor.sh'),'context':'u:object_r:vendor_file:s0','mode':0o644}
zygote=(r/'dist/aosp16/factory-inputs-3/root/system/etc/init/hw/init.zygote64.rc').read_text()
assert zygote.count(' --start-system-server')==1
# Preserve original system-server fork; pinned framework profile selects only our entry.
if not software_platform:zygote=zygote.replace(' --start-system-server','')
zygote+=''.join('    setenv '+key+' '+value+'\n' for key,value in {'ANDROID_ART_ROOT':'/apex/com.android.art','ANDROID_I18N_ROOT':'/apex/com.android.i18n','ANDROID_TZDATA_ROOT':'/apex/com.android.tzdata'}.items())
zygote+='    setenv ARCHTV_SOFTWARE_SECURITY_PROFILE software-platform-v1\n'
# SelectedRuntime and its launcher bridge run in the original zygote child.
# A variable on the auxiliary service RC cannot reach that process.
if timecoded_media:zygote+='    setenv ARCHTV_OBSERVE_LAUNCHER_CATALOG 1\n'
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
# Device configuration for the actual native mapper5 library/instance.
# This is an explicit Linux device mapping, not a claimed upstream row copy.
# Original AOSP already permits its graphics allocator clients to find this
# original service type; do not override isDeclared or add a Binder service.
import xml.etree.ElementTree as ET
mapper_xml=Path(vendor['files']['/vendor/etc/vintf/manifest/mapper.xml']['source'])
mapper_tree=ET.parse(mapper_xml).getroot()
mapper_hal=[node for node in mapper_tree.findall('hal') if node.get('format')=='native' and node.findtext('name')=='mapper']
assert len(mapper_hal)==1 and mapper_hal[0].findtext('version')=='5.0'
mapper_instances=[node.text for node in mapper_hal[0].findall('interface/instance')]
assert mapper_instances==['minigbm']
mapper_name='mapper/'+mapper_instances[0]
policy_source=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/sepolicy/source/system/sepolicy')
assert 'type hal_graphics_mapper_service, hal_service_type, service_manager_type;' in (policy_source/'public/service.te').read_text()
assert 'allow hal_graphics_allocator_client hal_graphics_mapper_service:service_manager find;' in (policy_source/'private/hal_graphics_allocator.te').read_text()
assert 'hal_client_domain(surfaceflinger, hal_graphics_allocator)' in (policy_source/'private/surfaceflinger.te').read_text()
existing_contexts=vendor['files'].get('/vendor/etc/selinux/vendor_service_contexts')
previous_contexts=Path(existing_contexts['source']).read_text() if existing_contexts else ''
assert not any(row.split() and row.split()[0]==mapper_name for row in previous_contexts.splitlines())
mapper_mapping=mapper_name+' u:object_r:hal_graphics_mapper_service:s0'
mapper_contexts=out/'graphics-service-contexts'
mapper_contexts.write_text(previous_contexts.rstrip('\n')+'\n'+mapper_mapping+'\n')
vendor['files']['/vendor/etc/selinux/vendor_service_contexts']={'source':str(mapper_contexts),'context':'u:object_r:vendor_configs_file:s0','mode':0o444}
(out/'native-mapper-context-contract.json').write_text(json.dumps({'mapping':mapper_mapping,'xml':str(mapper_xml),'xml_sha256':hashlib.sha256(mapper_xml.read_bytes()).hexdigest(),'previous_contexts_sha256':hashlib.sha256(previous_contexts.encode()).hexdigest(),'original_policy_sources':{n:hashlib.sha256((policy_source/n).read_bytes()).hexdigest() for n in ['public/service.te','private/hal_graphics_allocator.te','private/surfaceflinger.te']},'scope':'Explicit device mapping for actual native VINTF instance/library using original AOSP type/client rules. No upstream row copy claimed, no new policy permission, Binder implementation or isDeclared result.'},indent=2)+'\n')
(out/'vendor-inputs.json').write_text(json.dumps(vendor,indent=2))
if native_audio:run(['python',str(r/'reports/android16-audio-bootstrap/prepare-linux-profile.py'),str(out)]+(['--audio-write-diagnostic'] if audio_write_diagnostic else [])+(['--audio-synchronous-pcm'] if audio_synchronous_pcm else [])+(['--audio-production-dynamics'] if audio_production_dynamics else [])+(['--audio-pcm-observation'] if audio_pcm_observation else []))
text=(base/'build-payload-expanded.py').read_text().replace(str(base),str(out));expected=out/'apex-expected.json';expected.write_text(json.dumps(json.loads((r/'reports/android16-apex-bootstrap/complete-inputs.json').read_text())['modules'],indent=2)+'\n');text=text.replace("image=out/'payload-2.ext4'", "record('/apex-expected.json',out/'apex-expected.json','u:object_r:vendor_configs_file:s0',0o600)\nimage=out/'payload-2.ext4'")
old_parent="record('/'+str(parent.relative_to(tree)),None,'u:object_r:vendor_file:s0',0o755)"
assert old_parent in text
# Pinned original file_contexts requires configs labels on vendor/etc and
# every descendant directory. Generic vendor_file blocks real VINTF readers.
# Preserve explicit leaf labels and the separately selected overlay tree.
parent_contexts=r/'dist/aosp16/factory-inputs-3/root/system/etc/selinux/plat_file_contexts'
original_rule=[line.split() for line in parent_contexts.read_text().splitlines() if line.split() and line.split()[0]=='/(vendor|system/vendor)/etc(/.*)?']
assert original_rule==[['/(vendor|system/vendor)/etc(/.*)?','u:object_r:vendor_configs_file:s0']]
(out/'vendor-parent-context-contract.json').write_text(json.dumps({'source':str(parent_contexts),'source_sha256':hashlib.sha256(parent_contexts.read_bytes()).hexdigest(),'original_rule':original_rule[0],'scope':'Only directory parents in immutable payload /vendor/etc; explicit leaf/overlay contexts retained. No host labels or policy changes.'},indent=2)+'\n')
text=text.replace(old_parent,"record('/'+str(parent.relative_to(tree)),None,'u:object_r:vendor_configs_file:s0' if ('/'+str(parent.relative_to(tree))=='/vendor/etc' or ('/'+str(parent.relative_to(tree))).startswith('/vendor/etc/')) else 'u:object_r:vendor_overlay_file:s0' if path.startswith('/vendor/overlay/') else 'u:object_r:vendor_file:s0',0o755)")
# The complete debug audio closure exceeds the old128MiB factory image.
# Keep this explicit development size separate from production lightness.
if native_audio:
 assert text.count("'128M'")==1
 text=text.replace("'128M'","'256M'")
# Retain immutable images, manifests and failed extraction evidence. Successful
# verification dumps duplicate immutable source/image bytes and consume scarce
# disk per build; remove only each newly verified dump after its hash matches.
# Historical builds/dumps are never touched by this recipe.
verified_dump="assert hashlib.sha256(dump.read_bytes()).hexdigest()==entry['sha256'],path"
assert text.count(verified_dump)==1
text=text.replace(verified_dump,verified_dump+"\n  dump.unlink() # Successful ephemeral extraction only; source/image retained")
recipe=out/'build-payload.py';recipe.write_text(text);subprocess.run(['python',str(recipe)],stdout=open(out/'packager.log','w'),stderr=subprocess.STDOUT,check=True)
assert all(hashlib.sha256((r/n).read_bytes()).hexdigest()==h for n,h in source_hashes.items()), 'Source changed during build'
# Fresh successful staging duplicates immutable original sources and the image.
# This exact cleanup already ran manually for292/297 to unblock real PMS space
# checks. Never delete failed staging, historical artifacts or source inputs.
packed=json.loads((out/'payload.json').read_text())
image=Path(packed['image'])
with image.open('rb') as stream:
 assert hashlib.file_digest(stream,'sha256').hexdigest()==packed['sha256']
staging=out/'payload-tree-2'
assert not staging.is_symlink() and staging.resolve()==out.resolve()/'payload-tree-2'
verified=[]
for item in staging.rglob('*'):
 assert not item.is_symlink() and (item.is_dir() or item.is_file()),str(item)
 if not item.is_file():continue
 logical='/'+str(item.relative_to(staging));entry=packed['entries'][logical]
 assert hashlib.sha256(item.read_bytes()).hexdigest()==entry['sha256'],logical
 original=Path(entry['source'])
 assert not original.is_relative_to(staging) and original.is_file(),logical
 assert hashlib.sha256(original.read_bytes()).hexdigest()==entry['sha256'],logical
 verified.append({'path':logical,'sha256':entry['sha256'],'bytes':item.stat().st_size})
(out/'verified-staging-cleanup.json').write_text(json.dumps({'scope':'Only newly generated successful staging duplicate removed after source/image checks. Immutable source/image/manifests and failed/historical work retained.','image_sha256':packed['sha256'],'removed_tree':str(staging),'bytes':sum(row['bytes'] for row in verified),'files':verified},indent=2)+'\n')
shutil.rmtree(staging)
print(out,flush=True)
