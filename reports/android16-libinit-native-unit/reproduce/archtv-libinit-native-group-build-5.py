from pathlib import Path
import json,re,subprocess,hashlib,time,os
r=Path('/home/tv/repositorio-principal');s=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs');core=s/'system-core/source/system/core';init=core/'init';out=r/'dist/aosp16/libinit-native-group-5';out.mkdir();(out/'objects').mkdir();(out/'logs').mkdir()
bp=(init/'Android.bp').read_text();groups={n:re.findall(r'"([^"]+)"',re.search(r'^'+n+r' = \[(.*?)\n\]',bp,re.M|re.S).group(1)) for n in ['init_common_sources','init_device_sources']};files=[x for xs in groups.values() for x in xs if x.endswith('.cpp')];assert len(files)==52
module_flags=re.findall(r'"([^"]+)"',re.search(r'name: "init_defaults".*?cflags: \[(.*?)\n    \]',bp,re.S).group(1));base=json.loads((r/'dist/aosp16/libinit-build-1/epoll-compile-clang21.json').read_text())['argv'];profile=json.loads((r/'dist/aosp16/libinit-native-global-profile-1.json').read_text())['groups'];common=[x for x in base[:base.index('-c')] if x!='-O0'];common += sum((profile[n] for n in ['commonGlobalCflags','deviceGlobalCflags','commonGlobalCppflags','deviceGlobalCppflags']),[])+['-fno-rtti']+module_flags+profile['noOverrideGlobalCflags']+profile['noOverride64GlobalCflags']
includes=[core.parent.parent,core/'libcutils/include',core/'libcutils/include_outside_system',core/'libmodprobe/include',core/'libprocessgroup/include',core/'libutils/include',core/'libvendorsupport/include',core/'fs_mgr/include',core/'fs_mgr/libfstab/include',core/'fs_mgr/liblp/include',core/'fs_mgr/libsnapshot/include',core/'fs_mgr/libfiemap/include',core/'fs_mgr/libdm/include',core/'fs_mgr/libfs_avb/include',core/'property_service/libpropertyinfoparser/include',core/'property_service/libpropertyinfoserializer/include',s/'selinux/source/external/selinux/libselinux/include',s/'libprocinfo/source/system/libprocinfo/include',s/'bootloader-message/source/bootable/recovery/bootloader_message/include',s/'lmkd/source/system/memory/lmkd/include',s/'libcap/source/external/libcap/libcap/include',s/'protobuf/source/external/protobuf/src',s/'abseil/source/external/abseil-cpp',r/'dist/aosp16/init-protobuf-1/generated',r/'dist/aosp16/aconfig-original-1/com.android.apex.flags/generated/include',r/'dist/aosp16/aconfig-original-1/com.android.ueventd.flags/generated/include']
includes += [s/'bionic-libc/source/platform',core/'libsystem/include',s/'avf-cc-flags/source/packages/modules/Virtualization/libs/libavf_cc_flags/include',s/'libfscrypt/source/system/extras/libfscrypt/include',s/'unwindstack-headers/source/system/unwinding/libunwindstack/include',r/'dist/aosp16/snapshot-protobuf-1/generated']
includes += [s/'gsid/source/system/gsid/include',core/'fs_mgr/libsnapshot/snapuserd/include',s/'avb/source/external/avb',s/'logging/source/system/logging/logwrapper/include',s/'sepolicy/source/system/sepolicy/compat/libgenfslabelsversion/include',r/'dist/aosp16/xsdc-host-1/generated/include']
includes += [r/'dist/aosp16/update-protobuf-2/generated']
includes += [core/'libprocessgroup/setup/include']
common += ['-DSEPOLICY_VERSION=30']
for p in includes:assert p.is_dir(),str(p)
common+=['-I'+str(p) for p in includes];state={'source_base_commit':subprocess.check_output(['git','rev-parse','HEAD'],cwd=r,text=True).strip(),'pid_in_namespace':os.getpid(),'status':'running','groups':groups,'module_flags_original':module_flags,'common_argv':common,'source_profile':'Source BP4A flags; GSI configuration parity open. Original52source full set, original headers/codegen, selected clang21. Scoped native construction, not full Soong build equivalence or runtime acceptance.','results':[]};start=time.monotonic()
for i,name in enumerate(files):
 source=init/name;obj=out/'objects'/(name+'.o');argv=common+['-c',str(source),'-o',str(obj)];t=time.monotonic()
 try:
  p=subprocess.run(argv,capture_output=True,text=True,timeout=120);(out/'logs'/(name+'.log')).write_text(p.stdout+p.stderr);row={'source':name,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'exit_code':p.returncode,'seconds':round(time.monotonic()-t,3),'log':'logs/'+name+'.log'}
  if p.returncode==0:row['object_sha256']=hashlib.sha256(obj.read_bytes()).hexdigest()
  else:row['first_error']=next((line for line in p.stderr.splitlines() if 'error:' in line),'See full log')
 except subprocess.TimeoutExpired as e:
  (out/'logs'/(name+'.log')).write_bytes((e.stdout or b'')+(e.stderr or b''));row={'source':name,'timeout':120,'log':'logs/'+name+'.log'}
 state['results'].append(row);(out/'state.json').write_text(json.dumps(state,indent=2)+'\n');print(i+1,52,name,row.get('exit_code','timeout'),flush=True)
state.update(status='terminal',elapsed_seconds=time.monotonic()-start,all_sources_compiled=all(x.get('exit_code')==0 for x in state['results']))
if state['all_sources_compiled']:
 subprocess.run(['ar','rcs',str(out/'libinit.a'),*[str(out/'objects'/(name+'.o')) for name in files]],check=True);state['archive_sha256']=hashlib.sha256((out/'libinit.a').read_bytes()).hexdigest()
(out/'state.json').write_text(json.dumps(state,indent=2)+'\n');print('Native full-group build terminal; success',state['all_sources_compiled'],flush=True)
