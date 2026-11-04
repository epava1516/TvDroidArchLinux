#!/usr/bin/env python3
"""Combine existing real APEX and original graphics factories; no Android boot."""
from pathlib import Path
import sys,ast,json
import xml.etree.ElementTree, hashlib
# Resolve the Linux verification hash provider before entering the chroot.
hashlib.sha256(b"").digest()
r=Path(__file__).resolve().parents[2]
# Scope server-created shared files to this immutable execution, not /run/user.
if len(sys.argv)>1 and sys.argv[1] in ('--prepare-wayland-runtime','--close-wayland-runtime'):
 import os,stat,uuid,ctypes,subprocess
 assert os.geteuid()==0 and len(sys.argv)==3
 cp=Path(sys.argv[2]).resolve();before=json.loads((cp/'before-launch.json').read_text())
 run=str(uuid.UUID(before['id']));assert run==before['id'] and cp.name.startswith(run+'-')
 directory=Path('/run/user/1000')/('archtv-'+run)
 record=cp/'wayland-runtime.json'
 label='linux.system_u:linux.object_r:archtv_wayland_runtime_dir:s0'
 if sys.argv[1]=='--prepare-wayland-runtime':
  assert not directory.exists() and not directory.is_symlink() and not record.exists()
  directory.mkdir(mode=0o700);os.chown(directory,1000,1000)
  lib=ctypes.CDLL(str(r/'dist/aosp16/linux-selinux-handoff-2/libselinux-3.11/src/libselinux.so.1'),use_errno=True)
  lib.setfilecon_raw.argtypes=[ctypes.c_char_p,ctypes.c_char_p]
  assert lib.setfilecon_raw(os.fsencode(directory),label.encode())==0,ctypes.get_errno()
  st=directory.lstat();assert stat.S_ISDIR(st.st_mode) and stat.S_IMODE(st.st_mode)==0o700
  assert os.getxattr(directory,'security.selinux').rstrip(b'\0').decode()==label
  with record.open('x') as f:json.dump({'id':run,'path':str(directory),'dev':st.st_dev,'inode':st.st_ino,'uid':st.st_uid,'gid':st.st_gid,'context':label,'scope':'All regular files created here by Linux.init_t receive runtime_file type; not a keymap-only label. Preparation before enforcing.'},f,indent=2)
  os.chown(record,1000,1000)
 else:
  for unit in ('archtv-markor-session-','archtv-package-runner-'):
   assert subprocess.run(['systemctl','is-active','--quiet',unit+run+'.service']).returncode!=0,'Runtime still active'
  if not record.exists():
   assert not directory.exists() and not directory.is_symlink(),'Unrecorded runtime directory requires diagnosis'
   closed=cp/'wayland-runtime-closed.json';closed.write_text(json.dumps({'id':run,'not_prepared':True,'observed_absent':str(directory),'scope':'Startup did not prepare a runtime; no directory was deleted.'})+'\n');os.chown(closed,1000,1000)
   sys.exit(0)
  expected=json.loads(record.read_text());assert expected['id']==run and expected['path']==str(directory)
  if not directory.exists() and not directory.is_symlink():
   closed=cp/'wayland-runtime-closed.json';closed.write_text(json.dumps({'id':run,'observed_absent_after_units_stopped':str(directory),'scope':'May have been removed by logind after the owned PAM session; no claim this helper unlinked it.'})+'\n');os.chown(closed,1000,1000)
   sys.exit(0)
  st=directory.lstat();assert stat.S_ISDIR(st.st_mode) and (st.st_dev,st.st_ino)==(expected['dev'],expected['inode'])
  assert st.st_uid==1000 and st.st_gid==1000 and stat.S_IMODE(st.st_mode)==0o700
  entries=list(directory.iterdir())
  for entry in entries:
   s=entry.lstat()
   assert entry.name in ('wayland-1','wayland-1.lock','compositor.log','screen.ppm','capture.request') and s.st_uid==1000 and (stat.S_ISSOCK(s.st_mode) or stat.S_ISREG(s.st_mode)),str(entry)
  for entry in entries:entry.unlink()
  directory.rmdir()
  closed=cp/'wayland-runtime-closed.json';closed.write_text(json.dumps({'id':run,'removed':str(directory),'entries':[e.name for e in entries]})+'\n');os.chown(closed,1000,1000)
 sys.exit(0)
# Host-PID preflight inside the existing transient service, before unshare.
# Connect one typed capability; never grant the HWC ambient host connectto.
if len(sys.argv)>1 and sys.argv[1]=='--prepare-wayland':
 import os,socket as unix_socket,stat,struct,ctypes,subprocess,datetime
 assert os.geteuid()==0 and len(sys.argv)==5
 peer=Path(sys.argv[2]);payload_arg=Path(sys.argv[3]).resolve()
 cp=Path(os.environ['ARCHTV_RUN_CHECKPOINT']);manifest=json.loads((cp/'completion-manifest.json').read_text())
 assert manifest['checkpoint']==str(cp)
 if (cp/'wayland-runtime.json').exists():
  runtime=json.loads((cp/'wayland-runtime.json').read_text());assert runtime['id']==manifest['id']
  assert peer.parent==Path(runtime['path']) and peer.parent.name=='archtv-'+manifest['id']
  rst=peer.parent.lstat();assert (rst.st_dev,rst.st_ino)==(runtime['dev'],runtime['inode']) and rst.st_uid==1000
  assert os.getxattr(peer.parent,'security.selinux').rstrip(b'\0').decode()==runtime['context']
 st=peer.lstat();assert stat.S_ISSOCK(st.st_mode) and st.st_uid==1000
 lib=ctypes.CDLL(str(r/'dist/aosp16/linux-selinux-handoff-2/libselinux-3.11/src/libselinux.so.1'),use_errno=True)
 lib.getsockcreatecon_raw.argtypes=[ctypes.POINTER(ctypes.c_char_p)];lib.setsockcreatecon_raw.argtypes=[ctypes.c_char_p];lib.freecon.argtypes=[ctypes.c_void_p]
 old=ctypes.c_char_p();assert lib.getsockcreatecon_raw(ctypes.byref(old))==0
 try:
  assert lib.setsockcreatecon_raw(b'linux.system_u:linux.object_r:archtv_wayland_channel:s0')==0,ctypes.get_errno()
  channel=unix_socket.socket(unix_socket.AF_UNIX,unix_socket.SOCK_STREAM)
 finally:
  assert lib.setsockcreatecon_raw(old)==0
  if old:lib.freecon(old)
 channel.connect(str(peer))
 pid,uid,gid=struct.unpack('3i',channel.getsockopt(unix_socket.SOL_SOCKET,unix_socket.SO_PEERCRED,12))
 outer='archtv-markor-session-'+manifest['id']+'.service'
 actual=int(subprocess.check_output(['systemctl','show',outer,'-p','MainPID','--value'],text=True).strip())
 assert pid>1 and uid==1000 and gid==1000
 pidfd=os.pidfd_open(pid)
 process=Path('/proc')/str(pid)
 start=process.joinpath('stat').read_text().rsplit(')',1)[1].split()[19]
 # Dedicated frontend is a direct child of the owned PAM session, not the
 # privileged runtime launcher. Validate the actual socket peer, executable,
 # cgroup and parent; a writable PID/status file cannot substitute for these.
 assert process.joinpath('status').read_text().split('PPid:',1)[1].splitlines()[0].strip()==str(actual)
 # pam_systemd can move the owned leader and child into session-N.scope.
 # Bind to the actual owned leader's kernel cgroup, not an assumed unit suffix.
 parent_cgroup=(Path('/proc')/str(actual)/'cgroup').read_text()
 assert parent_cgroup.strip() and process.joinpath('cgroup').read_text()==parent_cgroup
 before=json.loads((cp/'before-launch.json').read_text())
 expected=Path(before['compositor_executable_path'])
 assert expected.is_absolute() and expected.is_relative_to('/opt/archtv/experimental/compositor')
 for node in [expected,*expected.parents]:
  info=node.lstat();assert info.st_uid==0 and not info.st_mode&0o022 and not stat.S_ISLNK(info.st_mode),str(node)
 assert (process/'exe').resolve()==expected.resolve()
 expected_hash=before['compositor_executable_sha256']
 actual_hash=hashlib.sha256((process/'exe').read_bytes()).hexdigest();assert actual_hash==expected_hash
 context=(process/'attr/current').read_text().rstrip(chr(0)+'\n')
 peersec=channel.getsockopt(unix_socket.SOL_SOCKET,unix_socket.SO_PEERSEC,1024).rstrip(b'\0').decode()
 assert context==peersec=='linux.system_u:linux.system_r:archtv_compositor:s0'
 status=dict(line.split(':',1) for line in process.joinpath('status').read_text().splitlines() if ':' in line)
 assert status['NoNewPrivs'].strip()=='1'
 assert all(int(status[key].strip(),16)==0 for key in ['CapInh','CapPrm','CapEff','CapAmb'])
 assert process.joinpath('stat').read_text().rsplit(')',1)[1].split()[19]==start
 now=peer.lstat();assert (st.st_dev,st.st_ino,st.st_uid)==(now.st_dev,now.st_ino,now.st_uid)
 lib.fgetfilecon_raw.argtypes=[ctypes.c_int,ctypes.POINTER(ctypes.c_char_p)];label=ctypes.c_char_p()
 assert lib.fgetfilecon_raw(channel.fileno(),ctypes.byref(label))>=0
 channel_label=label.value.decode();lib.freecon(label)
 assert channel_label=='linux.system_u:linux.object_r:archtv_wayland_channel:s0'
 record={'id':manifest['id'],'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'pid':pid,'pid_starttime':start,'uid':uid,'gid':gid,'exe_sha256':actual_hash,'process_context':context,'SO_PEERSEC':peersec,'socket_inode':[st.st_dev,st.st_ino],'socket_context':os.getxattr(peer,'security.selinux').decode().rstrip(chr(0)),'channel_context':channel_label,'scope':'Actual host-PID/peer validation before namespaces. Connected capability only, not Wayland protocol/pixels acceptance; no peer relabel.'}
 (cp/'wayland-peer.json').write_text(json.dumps(record,indent=2)+'\n');os.chown(cp/'wayland-peer.json',1000,1000)
 os.close(pidfd)
 os.environ['ARCHTV_WAYLAND_CHANNEL_FD']=str(channel.fileno());channel.set_inheritable(True)
 # Preserve the existing namespace topology, but close the connection in
 # its waiting parent instead of letting util-linux unshare retain a copy.
 kernel=ctypes.CDLL(None,use_errno=True)
 parent_pidfd=os.pidfd_open(os.getpid())
 assert kernel.unshare(0x00020000|0x20000000|0x40000000|0x08000000|0x04000000)==0,ctypes.get_errno()
 child=os.fork()
 if child:
  channel.close();os.close(parent_pidfd)
  record['preflight_parent_copy_closed']=True;record['delegated_host_pid']=child
  (cp/'wayland-peer.json').write_text(json.dumps(record,indent=2)+'\n');os.chown(cp/'wayland-peer.json',1000,1000)
  _,status=os.waitpid(child,0);code=os.waitstatus_to_exitcode(status);os._exit(code if code>=0 else 128-code)
 import select
 assert kernel.prctl(1,9,0,0,0)==0,ctypes.get_errno() # PR_SET_PDEATHSIG/SIGKILL
 poll=select.poll();poll.register(parent_pidfd,select.POLLIN)
 if poll.poll(0):os._exit(77)
 os.close(parent_pidfd)
 os.execv('/usr/bin/python',['/usr/bin/python',str(Path(__file__).resolve()),*sys.argv[2:]])

socket=sys.argv[1];payload=Path(sys.argv[2]).resolve();store=Path(sys.argv[3]).resolve()
build_options=json.loads((payload.parent/'build-options.json').read_text())
original_apex_bootstrap=build_options.get('original_apex_bootstrap',False)
assert isinstance(original_apex_bootstrap,bool)
observe_ms=build_options.get('observe_ms',3000)
userdata_name=build_options.get('persistent_userdata_name')
assert isinstance(observe_ms,int) and 3000<=observe_ms<=600000
# Materialize the existing graphics adapter, then add the tested APEX boundary.
recipe=(r/'reports/android16-hwc3-wayland/execute-graphics.py').read_text()
last="exec(compile(base, '<materialized graphics factory>', 'exec'), {'__name__': '__main__'})"
assert last in recipe
scope={'__name__':'__materialize__','__file__':str(r/'reports/android16-hwc3-wayland/execute-graphics.py')}
saved=sys.argv;sys.argv=[str(r/'reports/android16-hwc3-wayland/execute-graphics.py'),socket,'--observe-logs','--surfaceflinger','--selected-display']
exec(compile(recipe.replace(last,''),'<graphics materialization>','exec'),scope)
text=scope['base']
if build_options.get('preconnected_wayland',False):
 import os
 channel_fd=int(os.environ.pop('ARCHTV_WAYLAND_CHANNEL_FD'));assert channel_fd>=3
 ambient="target=root/'dev/socket/archtv-wayland';target.touch();mount('--bind',peer,target)"
 assert text.count(ambient)==1
 text=text.replace(ambient,"print('WAYLAND_AMBIENT_PATH_NOT_EXPOSED capability_only=1',flush=True)")
 os.set_inheritable(channel_fd,False)
 # Retain the capability only in the child Rust supervisor. All other
 # preparation subprocesses keep close_fds=True; parent copy closes on spawn.
 call='env=env,start_new_session=True)'
 assert text.count(call)==1
 text=text.replace(call,'env=env,start_new_session=True,pass_fds=('+str(channel_fd)+',))')
 envline="env={'PATH':'/system/bin:/archtv/bin','ANDROID_ROOT':'/system','ANDROID_DATA':'/data'}"
 assert text.count(envline)==1
 text=text.replace(envline,envline+"\nenv['ARCHTV_WAYLAND_CHANNEL_FD']="+repr(str(channel_fd)))
 marker='errors=[];identities=[]';assert text.count(marker)==1
 text=text.replace(marker,'os.close('+str(channel_fd)+')\n'+marker,1)
if build_options.get('original_logd',False):
 # Original init owns all three original sockets; do not prebind logdw in
 # the Linux Python observer. Legacy candidates keep their passive observer.
 passive="if '--observe-logs' in sys.argv[1:]:"
 assert text.count(passive)==1
 text=text.replace(passive,"if False: # original logd owns logdw",1)
text=text.replace("1<<36 if identity['kind']=='SUSPEND' else","(1<<36)|(1<<35)|(1<<23)|(1<<5) if identity['kind']=='SERVICES' else 1<<36 if identity['kind']=='SUSPEND' else");text=text.replace("('mc3-live-'+str(time.time_ns()))","('apex-live-'+str(time.time_ns()))")
render_setup="p=root/'dev/dri'/node;os.mknod(p,stat.S_IFCHR|0o660,actual.st_rdev);os.chmod(p,0o660);os.chown(p,0,1003)"
assert text.count(render_setup)==1
# Pinned Cuttlefish ueventd uses0666 for these two nodes. The deployed vmwgfx
# dumb-buffer backend requires a primary node even for client-side mapping.
# These are fresh Android-labelled private inodes, not chmod of host nodes.
text=text.replace(render_setup,"p=root/'dev/dri'/node;mode=0o666;os.mknod(p,stat.S_IFCHR|mode,actual.st_rdev);os.chmod(p,mode);os.chown(p,0,1003)")
null_setup="for n,dev in [('null',(1,3)),('urandom',(1,9))]:os.mknod(root/'dev'/n,stat.S_IFCHR|0o666,os.makedev(*dev))"
assert text.count(null_setup)==1
# mknod applies umask; make the intended standard-device mode explicit.
text=text.replace(null_setup,null_setup+";os.chmod(root/'dev'/n,0o666)")
if build_options.get('original_system_dma_heap',False):
 # Original ueventd /dev/dma_heap/system0444 system:system; real kernel heap,
 # fresh private inode only. Never create/chmod a host /dev node.
 heap_setup="""
heap_sysfs=Path('/sys/class/dma_heap/system/dev')
heap_numbers=heap_sysfs.read_text().strip().split(':');assert len(heap_numbers)==2 and all(x.isdecimal() for x in heap_numbers)
heap_major,heap_minor=map(int,heap_numbers);assert heap_major>0
heap_dir=root/'dev/dma_heap';heap_dir.mkdir(mode=0o755)
heap=heap_dir/'system';os.mknod(heap,stat.S_IFCHR|0o444,os.makedev(heap_major,heap_minor));os.chmod(heap,0o444);os.chown(heap,1000,1000)
"""
 text=text.replace(null_setup,heap_setup+'\n'+null_setup,1)
device_metadata="""
for name in ['dev/null','dev/urandom','dev/dri/card0','dev/dri/renderD128']+(['dev/dma_heap/system'] if (root/'dev/dma_heap/system').exists() else []):
 info=(root/name).stat()
 print('PRIVATE_DEVICE_CONTRACT '+json.dumps({'path':'/'+name,'mode':oct(stat.S_IMODE(info.st_mode)),'uid':info.st_uid,'gid':info.st_gid,'rdev':[os.major(info.st_rdev),os.minor(info.st_rdev)],'context':os.getxattr(root/name,'security.selinux').decode().rstrip(chr(0))}),flush=True)
"""
text=text.replace('dist/aosp16/sf-cohort-build-32/payload-2.ext4',str(payload.relative_to(r)))
if (payload.parent/'system-property-profile.json').exists():
 # The root/system_ext symlink is absolute inside the guest. Resolve the
 # physical mountpoint explicitly before pivot; never follow it on the host.
 profile_mount="mount('--bind',gsi/'system',root/'system');mount('-o','remount,bind,ro',root/'system')"
 assert text.count(profile_mount)==1
 text=text.replace(profile_mount,profile_mount+"\nprofile_source=candidate/'system_ext/etc/build.prop';profile_target=root/'system/system_ext/etc/build.prop'\nassert profile_source.is_file() and profile_target.is_file()\nmount('--bind',profile_source,profile_target);mount('-o','remount,bind,ro,nosuid,nodev,noexec',profile_target)\nprint('SYSTEM_PROPERTY_PROFILE_PRIVATE_RO '+str(profile_target),flush=True)",1)

text=text.replace('len(observed_logs)<512','len(observed_logs)<4096')
text=text.replace("'--display-integration'","'--packages-integration'").replace("'--startup-ms','45000'","'--startup-ms','300000'").replace("'--observe-ms','30000'","'--observe-ms',"+repr(str(observe_ms)))
text=text.replace('root.mkdir()\n',"""root.mkdir()
import importlib.util
factory_caps=int(next(l.split(':',1)[1].strip() for l in Path('/proc/self/status').read_text().splitlines() if l.startswith('CapEff:')),16)
# Original early-init RLIMIT_NICE: inherited by original Bionic services/apps.
import resource
resource.setrlimit(resource.RLIMIT_NICE,(40,40))
assert resource.getrlimit(resource.RLIMIT_NICE)==(40,40)
spec=importlib.util.spec_from_file_location('apex_devices',r/'reports/android16-apex-bootstrap/devices.py')
devices=importlib.util.module_from_spec(spec);spec.loader.exec_module(devices)
""",1)
if userdata_name is not None:
 import re
 assert re.fullmatch('[a-z0-9][a-z0-9_-]{0,47}',userdata_name)
 data_boundary="for n in ['system','apex','linkerconfig','data','dev','proc','sys','vendor','odm','archtv']:(root/n).mkdir()"
 assert text.count(data_boundary)==1
 data_setup="""
userdata_spec=importlib.util.spec_from_file_location('linux_userdata',r/'reports/android16-package-bootstrap/userdata.py')
userdata=importlib.util.module_from_spec(userdata_spec);userdata_spec.loader.exec_module(userdata)
userdata_lock,userdata_fd=userdata.prepare(root,out,USERDATA_NAME)
""".replace('USERDATA_NAME',repr(userdata_name))
 text=text.replace(data_boundary,data_boundary+'\n'+data_setup,1)
 text=text.replace("(root/'data'/n).mkdir(mode=0o700 if n in ['property','local/tmp/archtv-mc1'] else 0o755)","(root/'data'/n).mkdir(mode=0o700 if n in ['property','local/tmp/archtv-mc1'] else 0o755,exist_ok=True)")
 text=text.replace("p=root/'data'/name;p.mkdir(parents=True,mode=mode)","p=root/'data'/name;p.mkdir(parents=True,mode=mode,exist_ok=True)")
 text=text.replace("(root/'data/system').mkdir(mode=0o775)","(root/'data/system').mkdir(mode=0o775,exist_ok=True)")
 text=text.replace("(root/'data/misc/surfaceflinger').mkdir(parents=True,mode=0o700)","(root/'data/misc/surfaceflinger').mkdir(parents=True,mode=0o700,exist_ok=True)")

text=text.replace("elif p.is_file():shutil.copyfile(p,root/'apex'/p.name)","elif p.is_file() and p.name!='apex-info-list.xml':shutil.copyfile(p,root/'apex'/p.name)")
# Only top-level roots from pinned original init.rc. Vold creates user dirs,
# CE alias mounts and original permission data; no user metadata is seeded.
roots=[('misc/gatekeeper',0o700,1000,1000),('misc/keystore',0o700,1017,1017),('resource-cache',0o771,1000,1000),('misc/net',0o750,0,2000),('misc/stats-active-metric',0o770,1066,1000),('misc/stats-data',0o770,1066,1000),('misc/stats-data/restricted-data',0o770,1066,1000),('misc/stats-service',0o770,1066,1000),('misc/train-info',0o770,1066,1000),('dalvik-cache',0o771,0,0),('misc/vold',0o700,0,0),('misc/profiles',0o771,1000,1000),('misc/profiles/cur',0o771,1000,1000),('misc/profiles/ref',0o771,1000,1000),('misc/apexdata',0o711,0,0),('system/users',0o775,1000,1000),('media',0o550,1023,1023),('misc_ce',0o551,1000,9998),('system_ce',0o550,1000,1000),('user_de',0o511,1000,1000),('vendor_ce',0o551,0,0),('vendor_de',0o551,0,0)]
roots += [('system/environ',0o700,1000,1000)]
# Exact pinned init.rc roots for original media/crash services; no trace or media state seeded.
roots += [('anr',0o775,1000,1000),('tombstones',0o775,1000,1000),('misc/media',0o700,1013,1013)]
roots += [('user',0o511,1000,1000),('data',0o771,1000,1000),('storage_area',0o551,0,0)]
root_code="\n".join("p=root/'data'/"+repr(name)+";p.mkdir(parents=True,exist_ok=True);os.chmod(p,"+str(mode)+");os.chown(p,"+str(uid)+","+str(gid)+")" for name,mode,uid,gid in roots)
apk_path=Path('/home/tv/.cache/archtv/apk/real-app-candidates/net.gsantner.markor-v164-2026.10.0-flavorDefault-release.apk')
apk_sha='c105bf5cc9530f7486b984323a185c17086b459a56ec936a5990ceb8da3d8440'
assert hashlib.sha256(apk_path.read_bytes()).hexdigest()==apk_sha
# Extend existing private APEX metadata after devices.prepare has created it.
aconfig_code=""
for name,mode in [('metadata',0o755),('metadata/aconfig',0o775),('metadata/aconfig/flags',0o770),('metadata/aconfig/maps',0o775),('metadata/aconfig/boot',0o775)]:
 aconfig_code+="\np=root/"+repr(name)+";p.mkdir(parents=True,exist_ok=True);os.chmod(p,"+str(mode)+");os.chown(p,0,1000)"
# Original init.rc root namespace storage preparation (not a mounted volume or
# an availability claim). Zygote requires a real /storage bind target before
# specializing even an application whose main data is private.
for logical,mode,uid,gid in [('storage',0o755,0,0),('mnt',0o755,0,0),('mnt/expand',0o771,1000,1000),('mnt/user',0o755,0,0),('mnt/user/0',0o755,0,0),('mnt/user/0/self',0o755,0,0),('mnt/user/0/emulated',0o755,0,0),('mnt/user/0/emulated/0',0o755,0,0),('mnt/pass_through',0o700,0,0),('mnt/pass_through/0',0o710,0,1023),('mnt/pass_through/0/self',0o710,0,1023),('mnt/pass_through/0/emulated',0o710,0,1023),('mnt/pass_through/0/emulated/0',0o710,0,1023)]:
 root_code+="\np=root/"+repr(logical)+";p.mkdir(parents=True,exist_ok=True);os.chmod(p,"+str(mode)+");os.chown(p,"+str(uid)+","+str(gid)+")"
for logical,mode in [('mnt/runtime',0o700),('mnt/runtime/default',0o755),('mnt/runtime/default/self',0o755),('mnt/runtime/read',0o755),('mnt/runtime/read/self',0o755),('mnt/runtime/write',0o755),('mnt/runtime/write/self',0o755),('mnt/runtime/full',0o755),('mnt/runtime/full/self',0o755)]:
 root_code+="\np=root/"+repr(logical)+";p.mkdir(parents=True,exist_ok=True);os.chmod(p,"+str(mode)+");os.chown(p,0,0)"
storage_mount_code="""
# Complete original init.rc app-data isolation prerequisites, within the
# private Linux factory only. These bind actual directories; no APK/user
# inventory, CE unlocked state, encryption, FUSE volume or readiness is seeded.
apex_before=(root/'data/apex').stat()
mount('--rbind',root/'data',root/'data');mount('--make-shared',root/'data')
apex_after=(root/'data/apex').stat()
assert (apex_before.st_dev,apex_before.st_ino)==(apex_after.st_dev,apex_after.st_ino), 'Data propagation setup must preserve real APEX child mount'
# Public storage propagation is prepared after pivot_root below. A shared
# root here would make pivot_root fail EINVAL; a /mnt/user/0 self-bind
# would instead be removed by original vold unmountAll (actual268/269).
(root/'data_mirror').mkdir()
mount('-t','tmpfs','-o','nodev,noexec,nosuid,mode=0700,uid=0,gid=1000,fscontext=u:object_r:tmpfs:s0,rootcontext=u:object_r:mirror_data_file:s0','tmpfs',root/'data_mirror')
for name in ['data_ce','data_de','misc_ce','misc_de','storage_area','data_ce/null','data_de/null','misc_ce/null','misc_de/null','cur_profiles','ref_profiles']:
 p=root/'data_mirror'/name;p.mkdir(mode=0o700)
 assert lib.lsetfilecon_raw(str(p).encode(),b'u:object_r:mirror_data_file:s0')==0,ctypes.get_errno()
for source,target in [('user','data_ce/null'),('user_de','data_de/null'),('misc_ce','misc_ce/null'),('misc_de','misc_de/null'),('storage_area','storage_area'),('misc/profiles/cur','cur_profiles'),('misc/profiles/ref','ref_profiles')]:
 mount('--rbind',root/'data'/source,root/'data_mirror'/target)
"""

root_code+="\n(root/'dev/input').mkdir()"
root_code+="""
# Original vold mounts a real private FUSE volume and passes its FD to the
# original ExternalStorageService. Never replace it with a directory alias.
fuse_device=Path('/sys/class/misc/fuse/dev').read_text().strip()
assert fuse_device=='10:229',fuse_device
# Linux private endpoint: only original root vold opens it; MediaProvider
# receives the actual FD through Binder, not permission to open the host node.
os.mknod(root/'dev/fuse',stat.S_IFCHR|0o600,os.makedev(10,229))
os.chown(root/'dev/fuse',0,0)
"""
for name in ['markor-note-before-stop.txt','markor-note-after-relaunch.txt','markor-note-bytes.bin','markor-lifecycle.txt','markor-relaunch.txt','markor-app-data.txt','markor-user-start.txt','markor-resolve.txt','markor-launch.txt','markor-volumes.txt','markor-overlays.txt','markor-sf.png','markor-mountinfo.txt']:
 root_code+="\np=root/'data/local/tmp/archtv-mc1'/"+repr(name)+";p.touch(mode=0o640);os.chown(p,2000,1000);os.chmod(p,0o640)"
root_code+="\np=root/'data/local/tmp/archtv-mc1/selected-failure.txt';p.touch(mode=0o600);os.chown(p,1000,1000)"
root_code+="\np=root/'data/local/tmp/archtv-mc1/ranging-service-info.txt';p.touch(mode=0o600);os.chown(p,1000,1000)"
root_code+="\np=root/'data/local/tmp/archtv-mc1/selected-wait.txt';p.touch(mode=0o600);os.chown(p,1000,1000)"
root_code+="\np=root/'data/local/tmp/archtv-mc1/selected-user-wait.txt';p.touch(mode=0o600);os.chown(p,1000,1000)"
for output_name in ['markor-preinstall-path.txt','markor-preinstall-dump.txt','keymint-component.txt','storage-contract.txt','markor-user-state.txt','markor-bootstrap-home-stop.txt','markor-home-after.txt','markor-boot-before-user.txt','platform-capabilities.txt','linux-application-profile.txt','markor-postcommit-path.txt','markor-postcommit-dump.txt','markor-installed-bytes.txt']:
 uid=2000 if output_name.startswith("markor-") else 1000
 root_code+="\np=root/'data/local/tmp/archtv-mc1'/"+repr(output_name)+";p.touch(mode=0o600);os.chown(p,"+str(uid)+",1000)"

root_code+="\np=root/'data/local/tmp/archtv-mc1/markor-install.txt';p.touch(mode=0o600);os.chown(p,2000,1000)"
root_code+="\nshutil.copyfile(Path("+repr(str(apk_path))+"),root/'data/local/tmp/markor.apk');os.chown(root/'data/local/tmp/markor.apk',2000,2000);os.chmod(root/'data/local/tmp/markor.apk',0o644)"
# Trusted developer CLI inputs belong to shell storage, not vendor policy.
# Copy exact payload bytes before label()/MAC release; do not relabel generic
# vendor files or expand shell/system_server access to them.
root_code+="""
import hashlib
shell_inputs=[]
for relative in ['bin/install-markor.sh','etc/archtv-markor-workflow-token','etc/archtv-markor-workflow-budget']:
 source=root/'vendor'/relative
 if not source.exists():
  assert relative!='bin/install-markor.sh','Missing external installer payload'
  continue
 destination=root/'data/local/tmp/archtv-mc1'/source.name
 shutil.copyfile(source,destination)
 os.chown(destination,2000,2000);os.chmod(destination,0o400)
 digest=hashlib.sha256(source.read_bytes()).hexdigest()
 assert hashlib.sha256(destination.read_bytes()).hexdigest()==digest
 shell_inputs.append({'source':str(source),'destination':str(destination),'sha256':digest,'uid':2000,'gid':2000,'mode':'0400'})
(out/'external-shell-inputs.json').write_text(json.dumps({'scope':'Exact trusted external CLI payload inputs only; no app/user/key/permission/readiness state seeded','files':shell_inputs},indent=2)+'\\n')
"""
text=text.replace('label(root)\n',root_code+'\nlabel(root)\n',1)
mount_marker="for p in sorted((r/'dist/aosp16/factory-inputs-3').glob('*.payload.img')):"
assert mount_marker in text
text=text.replace(mount_marker,storage_mount_code+'\n'+mount_marker,1)
text=text.replace('label(root)\n',"devices.prepare(root,out,Path("+repr(str(store))+"))\n"+aconfig_code+"\nassert not (root/'apex/apex-info-list.xml').exists()\nlabel(root)\n",1)
if userdata_name is not None:
 scaffold={'property','local','local/tmp','local/tmp/archtv-mc1','misc_de','system_de','misc/installd','misc/user','app','app-staging','system','misc/surfaceflinger'}
 for name,_,_,_ in roots:
  q=Path(name)
  while str(q)!='.':scaffold.add(str(q));q=q.parent
 label_walk="dirs[:]=[n for n in dirs if Path(base)/n not in [root/'system',root/'vendor']]"
 assert text.count(label_walk)==1
 text=text.replace(label_walk,label_walk+"\n if Path(base).is_relative_to(root/'data'):continue\n if Path(base)==root:dirs[:]=[n for n in dirs if n!='data']",1)
 label_boundary="for p in sorted((r/'dist/aosp16/factory-inputs-3').glob('*.payload.img')):"
 label_data="label(root/'data')\n"
 for name in sorted(scaffold):label_data+="label(root/'data'/"+repr(name)+")\n"
 # Only the trusted input APK lies outside the diagnostics directory. Apply
 # its original file_contexts label too; never grant access to unlabeled data
 # or recursively relabel application/user storage to make installation pass.
 label_data+="label(root/'data/local/tmp/markor.apk')\n"
 label_data+="for q in (root/'data/local/tmp/archtv-mc1').iterdir():label(q)\n"
 text=text.replace(label_boundary,label_data+label_boundary,1)
 # Sync the real persistent filesystem after original services stop. FD is
 # preopened/CLOEXEC, never passed to Android, and survives private pivot_root.
 sync_code="""
assert kernel.syncfs(userdata_fd)==0,ctypes.get_errno()
print('LINUX_PRIVATE_USERDATA_SYNCED device='+str(os.fstat(userdata_fd).st_dev)+' inode='+str(os.fstat(userdata_fd).st_ino),flush=True)
os.close(userdata_fd) # userdata_lock remains owned until factory process exit
"""
 text=text.replace("if p.returncode!=0:\n",sync_code+"\nif p.returncode!=0:\n",1)
health_mounts="""
# Read-only Linux power_supply class and its exact current device targets.
# No /sys/power controls, fake battery values, or host relabeling.
health_sources=[]
health_class=Path('/sys/class/power_supply')
health_target=root/'sys/class/power_supply';health_target.mkdir(parents=True,exist_ok=True)
mount('--bind',health_class,health_target);mount('-o','remount,bind,ro',health_target)
for node in sorted(health_class.iterdir()):
 source=node.resolve();assert source.is_relative_to('/sys/devices')
 target=root/str(source).lstrip('/');target.mkdir(parents=True,exist_ok=True)
 mount('--bind',source,target);mount('-o','remount,bind,ro',target)
 health_sources.append({'class':str(node),'target':str(source),'readonly':True})
(out/'health-sysfs.json').write_text(json.dumps(health_sources,indent=2)+'\\n')
"""
text=text.replace("for p in sorted((r/'dist/aosp16/factory-inputs-3').glob('*.payload.img')):","devices.mount_sysfs(root)\n"+health_mounts+"\nfor p in sorted((r/'dist/aosp16/factory-inputs-3').glob('*.payload.img')):",1)
proc_mount="mount('-t','proc','proc',root/'proc')"
assert text.count(proc_mount)==1
host_control_guard="""
# SysRq is a real global-kernel control, not a PID-namespaced resource.
# Keep the real inode/label but make ONLY this namespace's alias read-only.
sysrq=root/'proc/sysrq-trigger';before_sysrq=sysrq.stat()
mount('--bind',sysrq,sysrq);mount('-o','remount,bind,ro,nosuid,nodev,noexec',sysrq)
after_sysrq=sysrq.stat();assert (before_sysrq.st_dev,before_sysrq.st_ino)==(after_sysrq.st_dev,after_sysrq.st_ino)
assert os.statvfs(sysrq).f_flag&os.ST_RDONLY
(out/'host-control-proc.json').write_text(json.dumps({'path':'/proc/sysrq-trigger','real_inode_preserved':True,'device':after_sysrq.st_dev,'inode':after_sysrq.st_ino,'context':os.getxattr(sysrq,'security.selinux').decode().rstrip(chr(0)),'readonly_mount':True,'scope':'Real global endpoint, namespace-local read-only alias. No fake file or successful write; no host mount changed.'},indent=2)+'\\n')
"""
text=text.replace(proc_mount,'devices.enable_loop_controls(root,out)\n'+proc_mount+'\n'+host_control_guard,1)
text=text.replace("cgbase=Path('/sys/fs/cgroup/system.slice/codex-remote.service/archtv-mc1')", "unit_cgroup=Path('/proc/self/cgroup').read_text().split('0::',1)[1].strip()\nassert unit_cgroup.startswith('/archtv.slice/archtv-apex-') and unit_cgroup.endswith('.service'),unit_cgroup\ncgbase=Path('/sys/fs/cgroup'+unit_cgroup)/'archtv-apex'")
# Observe the real kernel labels at the same dedicated CG boundary; never
# relabel host cgroups or infer runtime labeling merely from policy source.
cg_observer="print('MC1_FACTORY_PLACED_IN_PRIVATE_CGROUP '+str(cg),flush=True)"
assert text.count(cg_observer)==1
text=text.replace(cg_observer,cg_observer+"""
for observed in [cg,cg/'cgroup.procs',cg/'system',cg/'apps']:
 print('LINUX_PRIVATE_CGROUP_LABEL '+json.dumps({'path':str(observed),'context':os.getxattr(observed,'security.selinux').decode().rstrip(chr(0))}),flush=True)
""")

# Original cgroup-v2 system/app hierarchy for the already owned cohort only.
# CgroupSetup cannot be replayed globally: this Linux factory delegates its
# existing kernel subtree, using the original descriptor mode/identity.
cgroup_marker="(cg/'system').mkdir();os.chmod(cg/'system',0o775);os.chown(cg/'system',1000,1000)"
assert cgroup_marker in text
text=text.replace(cgroup_marker,"""os.chmod(cg,0o775);os.chown(cg,1000,1000)
os.chmod(cg/'cgroup.procs',0o775);os.chown(cg/'cgroup.procs',1000,1000)
for kind in ['system','apps']:
 group=cg/kind;group.mkdir();os.chmod(group,0o775);os.chown(group,1000,1000)
 os.chmod(group/'cgroup.procs',0o775);os.chown(group/'cgroup.procs',1000,1000)
""",1)
network_code="""import importlib.util
network_spec=importlib.util.spec_from_file_location('network_boundary',r/'reports/android16-network-bootstrap/boundary.py')
network=importlib.util.module_from_spec(network_spec);network_spec.loader.exec_module(network)
network.prepare(root,out)
# Real private mountpoints required by original SetupMountNamespaces and
# logwrapper PTY allocation. All remain within this cohort's mount namespace.
(root/'bootstrap-apex').mkdir(exist_ok=True)
for point in ['apex','linkerconfig']:mount('--rbind',root/point,root/point)
assert (root/'apex/com.android.runtime/bin/linker64').is_file(), 'Bootstrap runtime mount hidden'
(root/'dev/pts').mkdir(exist_ok=True)
mount('-t','devpts','-o','newinstance,ptmxmode=0666,mode=0620,gid=5,fscontext=u:object_r:devpts:s0,rootcontext=u:object_r:devpts:s0','devpts',root/'dev/pts')
# The private devpts master is the real /dev/ptmx endpoint. Apply the
# original /dev/ptmx file-context rule to that endpoint, not only its symlink.
private_ptmx=root/'dev/pts/ptmx';ptmx_context=ctypes.c_char_p()
assert lib.selabel_lookup_raw(handle,ctypes.byref(ptmx_context),b'/dev/ptmx',private_ptmx.lstat().st_mode)==0
assert lib.lsetfilecon_raw(os.fsencode(private_ptmx),ptmx_context)==0;lib.freecon(ptmx_context)
assert os.getxattr(private_ptmx,'security.selinux').decode().rstrip(chr(0))=='u:object_r:ptmx_device:s0'
(out/'private-devpts.json').write_text(json.dumps({'root_context':os.getxattr(root/'dev/pts','security.selinux').decode().rstrip(chr(0)),'master_context':os.getxattr(private_ptmx,'security.selinux').decode().rstrip(chr(0)),'rule':'Original /dev/ptmx on private newinstance endpoint; host PTY unchanged'}))
(root/'dev/ptmx').symlink_to('pts/ptmx')
"""
text=text.replace("selinux=root/'sys/fs/selinux';",network_code+"\nselinux=root/'sys/fs/selinux';",1)
text=text.replace("stdin_fd=os.open(root/'dev/null'", "monitor_log=(out/'device-monitor.log').open('w')\nmonitor=subprocess.Popen([sys.executable,str(r/'reports/android16-apex-bootstrap/devices.py'),str(root),str(out),str(os.getpid())],stdout=monitor_log,stderr=subprocess.STDOUT)\nprint('APEX_DEVICE_MONITOR_OWNED pid='+str(monitor.pid),flush=True)\nstdin_fd=os.open(root/'dev/null'",1)
text=text.replace("stdin_fd=os.open(root/'dev/null'",device_metadata+"\nstdin_fd=os.open(root/'dev/null'",1)
text=text.replace("log_observer=None;observed_logs=[];log_stop=False", "live_log=(out/'android-log-live.jsonl').open('w')\nlog_observer=None;observed_logs=[];log_stop=False")
# The inline diagnostic summary must not stop draining the real log stream.
# Keep its memory bound, and persist the late user/launch failure in the
# existing evidence file under a separate explicit byte limit.
text=text.replace('and len(observed_logs)<4096','')
text=text.replace("live_log=(out/'android-log-live.jsonl').open('w')", "live_log=(out/'android-log-live.jsonl').open('w')\nlog_capture_file=(out/'android-log-capture.json').open('w')\nlog_capture={'records':0,'bytes':0,'limit_bytes':67108864,'truncated':False,'inline_limit_records':512}")
text=text.replace("log_capture_file=(out/'android-log-capture.json').open('w')", "log_capture_file=(out/'android-log-capture.json').open('w')\nframe_capture=(out/'markor-sf.png').open('wb')\nos.fchmod(frame_capture.fileno(),0o640);os.fchown(frame_capture.fileno(),2000,1000)")
# Capture actual app-owned bytes while the factory still owns /data. All host
# outputs are preopened before pivot_root; no guest note is created here.
text=text.replace("frame_capture=(out/'markor-sf.png').open('wb')", "workflow_capture=(out/'markor-workflow-evidence.json').open('w')\nframe_capture=(out/'markor-sf.png').open('wb')")
text=text.replace("frame_capture=(out/'markor-sf.png').open('wb')", "mount_capture=(out/'markor-mountinfo.txt').open('wb')\nos.fchmod(mount_capture.fileno(),0o640);os.fchown(mount_capture.fileno(),2000,1000)\nframe_capture=(out/'markor-sf.png').open('wb')")
text=text.replace('observed_logs.append(item)', """item['observed_monotonic']=time.monotonic()
    encoded=json.dumps(item)+'\\n';size=len(encoded.encode())
    if log_capture['bytes']+size<=log_capture['limit_bytes']:
     live_log.write(encoded);live_log.flush();log_capture['bytes']+=size;log_capture['records']+=1
    else:log_capture['truncated']=True
    if len(observed_logs)<log_capture['inline_limit_records']:observed_logs.append(item)""")
if build_options.get('original_logd',False):
 boundary='if p.returncode!=0:\n'
 assert text.count(boundary)==1
 text=text.replace(boundary,"logcat=Path('/data/local/tmp/archtv-mc1/original-logcat.txt');raw_logcat=logcat.read_bytes() if logcat.exists() else b'';print('ORIGINAL_LOGCAT_OUTPUT '+json.dumps({'present':logcat.exists(),'bytes':len(raw_logcat),'sha256':hashlib.sha256(raw_logcat).hexdigest(),'tail_limit_bytes':1048576,'truncated':len(raw_logcat)>1048576,'text':raw_logcat[-1048576:].decode(errors='replace')}),flush=True)\n"+boundary,1)
text=text.replace("if p.returncode!=0:\n", """# Preopened evidence FD survives pivot_root; no host path is reopened here.
try:
 log_capture_file.write(json.dumps(log_capture,indent=2)+'\\n');log_capture_file.flush();log_capture_file.close()
except OSError as error:
 print('LOG_CAPTURE_METADATA_FAILURE '+repr(error),flush=True)
frame_source=Path('/data/local/tmp/archtv-mc1/markor-sf.png')
frame_info={'scope':'Original SurfaceFlinger pixels, not physical display/input/app journey acceptance','present':frame_source.is_file()}
if frame_source.is_file():
 info=frame_source.stat();frame_info.update(bytes=info.st_size,uid=info.st_uid,gid=info.st_gid)
 if 0<info.st_size<=16777216:
  pixels=frame_source.read_bytes();frame_capture.write(pixels);frame_capture.flush()
  frame_info.update(png_signature=pixels.startswith(bytes.fromhex('89504e470d0a1a0a')),sha256=hashlib.sha256(pixels).hexdigest())
workflow={'scope':'Read-only actual note and original lifecycle outputs within one ephemeral cohort; not cross-cohort durability','token':None}
try:
 token_path=Path('/vendor/etc/archtv-markor-workflow-token')
 if token_path.is_file():
  token=token_path.read_text().strip()
  assert len(token)==8 and all(c in '0123456789abcdef' for c in token)
  workflow['token']=token
  note=Path('/data/local/tmp/archtv-mc1/markor-note-bytes.bin')
  workflow['note_source']='Original privileged system_server client cat of actual /data/media/0/Documents/markor/archtv-'+token+'.md before force-stop; evidence copy only'
  workflow['present']=note.is_file()
  if note.is_file():
   st=note.stat();assert st.st_size<=4096
   raw=note.read_bytes()
   workflow['note']={'path':str(note),'bytes_hex':raw.hex(),'sha256':hashlib.sha256(raw).hexdigest(),'size':st.st_size,'uid':st.st_uid,'gid':st.st_gid,'inode':st.st_ino,'mode':oct(st.st_mode & 0o7777),'matches_expected':raw==('archtv note '+token+'\\n').encode()}
  for name in ['markor-lifecycle.txt','markor-relaunch.txt','markor-note-before-stop.txt','markor-note-after-relaunch.txt']:
   src=Path('/data/local/tmp/archtv-mc1')/name
   if src.is_file():
    assert src.stat().st_size<=16384
    workflow[name]=src.read_text()
except Exception as error:
 workflow['capture_error']=repr(error)
workflow_capture.write(json.dumps(workflow,indent=2)+'\\n');workflow_capture.flush();workflow_capture.close()
frame_capture.close()
print('MARKOR_ORIGINAL_SF_CAPTURE '+json.dumps(frame_info),flush=True)
mount_source=Path('/data/local/tmp/archtv-mc1/markor-mountinfo.txt')
if mount_source.is_file() and 0<mount_source.stat().st_size<=1048576:
 mount_bytes=mount_source.read_bytes();mount_capture.write(mount_bytes)
 selected_mounts=[line for line in mount_bytes.decode().splitlines() if line.split()[4].startswith(('/storage','/mnt/user','/mnt/runtime'))]
 print('MARKOR_ORIGINAL_MOUNTINFO '+json.dumps({'scope':'Kernel mountinfo from original installer namespace after launch request, not per-app access or persistence acceptance','sha256':hashlib.sha256(mount_bytes).hexdigest(),'selected':selected_mounts}),flush=True)
mount_capture.close()
if p.returncode!=0:
""",1)

text=text.replace('log_stop=True\n','monitor.terminate();monitor.wait(timeout=12);monitor_log.close()\nlog_stop=True\n',1)
text=text.replace("os.chown(root/'data/local/tmp/archtv-mc1',2000,2000)","os.chown(root/'data/local/tmp/archtv-mc1',2000,1000);os.chmod(root/'data/local/tmp/archtv-mc1',0o750)")
# The existing graphics verifier retains its eight exact service identities.
# Observe apexd identities in the same real /proc sampling branch.
text=text.replace("SELECTED_(SUSPEND|SERVICES|INSTALLD)_STARTED pid=(\\d+)',line)","SELECTED_(SUSPEND|SERVICES|INSTALLD)_STARTED pid=(\\d+)|APEX_(DAEMON|SNAPSHOT)_STARTED pid=(\\d+)',line)")
text=text.replace('(match[5] or match[7])','(match[5] or match[7] or match[9])').replace('int(match[2] or match[4] or match[6] or match[8])','int(match[2] or match[4] or match[6] or match[8] or match[10])')
text=text.replace("'INSTALLD':'u:r:installd:s0'","'INSTALLD':'u:r:installd:s0','DAEMON':'u:r:apexd:s0','SNAPSHOT':'u:r:apexd:s0'")
text=text.replace("identity['kind']=='INSTALLD'","identity['kind'] in ['INSTALLD','DAEMON','SNAPSHOT']")
text=text.replace('APEX_(DAEMON|SNAPSHOT)','APEX_(DAEMON|SNAPSHOT|DERIVE)')
text=text.replace("'SNAPSHOT':'u:r:apexd:s0'","'SNAPSHOT':'u:r:apexd:s0','DERIVE':'u:r:derive_classpath:s0'")

# Avoid applying installd capabilities to apexd: native exact original RC masks.
text=text.replace("0x2000ff if identity['kind'] in ['INSTALLD','DAEMON','SNAPSHOT'] else", "0x20000f if identity['kind']=='DAEMON' else 0xf if identity['kind']=='SNAPSHOT' else 0x2000ff if identity['kind']=='INSTALLD' else")
text=text.replace("fields['Gid'].split()))==[0 if identity['kind'] in ['INSTALLD','DAEMON','SNAPSHOT']", "fields['Gid'].split()))==[0 if identity['kind']=='INSTALLD'")
text=text.replace('SUSPEND|SERVICES|INSTALLD','SUSPEND|SERVICES|INSTALLD|VOLD|ZYGOTE')
text=text.replace("'INSTALLD':'u:r:installd:s0'","'INSTALLD':'u:r:installd:s0','VOLD':'u:r:vold:s0','ZYGOTE':'u:r:zygote:s0'")
text=text.replace("identity['kind'] in ['INSTALLD','DAEMON','SNAPSHOT']","identity['kind'] in ['INSTALLD','DAEMON','SNAPSHOT','VOLD','ZYGOTE']")
text=text.replace("fields['Gid'].split()))==[0 if identity['kind']=='INSTALLD'","fields['Gid'].split()))==[0 if identity['kind'] in ['INSTALLD','VOLD','ZYGOTE']")
text=text.replace("0x20000f if identity['kind']=='DAEMON'","factory_caps if identity['kind'] in ['VOLD','ZYGOTE'] else 0x20000f if identity['kind']=='DAEMON'")
text=text.replace('SUSPEND|SERVICES|INSTALLD|VOLD|ZYGOTE','SUSPEND|SERVICES|INSTALLD|VOLD|ZYGOTE|HEALTH')
text=text.replace("'ZYGOTE':'u:r:zygote:s0'","'ZYGOTE':'u:r:zygote:s0','HEALTH':'u:r:hal_health_default:s0'")
text=text.replace("factory_caps if identity['kind']", "((1<<35)|(1<<36)) if identity['kind']=='HEALTH' else factory_caps if identity['kind']")
text=text.replace('SUSPEND|SERVICES|INSTALLD|VOLD|ZYGOTE|HEALTH','SUSPEND|SERVICES|INSTALLD|VOLD|ZYGOTE|HEALTH|STATSD')
text=text.replace("'HEALTH':'u:r:hal_health_default:s0'","'HEALTH':'u:r:hal_health_default:s0','STATSD':'u:r:statsd:s0'")
text=text.replace("list(map(int,fields['Uid'].split()))==[", "list(map(int,fields['Uid'].split()))==[1066 if identity['kind']=='STATSD' else ")
text=text.replace("list(map(int,fields['Gid'].split()))==[", "list(map(int,fields['Gid'].split()))==[1066 if identity['kind']=='STATSD' else ")
# Reuse the existing namespace-PID observer for original netd/lmkd identities.
text=text.replace('SUSPEND|SERVICES|INSTALLD|VOLD|ZYGOTE|HEALTH|STATSD','SUSPEND|SERVICES|INSTALLD|VOLD|ZYGOTE|HEALTH|STATSD|NETD|LMKD')
text=text.replace("'STATSD':'u:r:statsd:s0'","'STATSD':'u:r:statsd:s0','NETD':'u:r:netd:s0','LMKD':'u:r:lmkd:s0'")
text=text.replace("1066 if identity['kind']=='STATSD' else ","1069 if identity['kind']=='LMKD' else 0 if identity['kind']=='NETD' else 1066 if identity['kind']=='STATSD' else ")
text=text.replace("(((1<<35)|(1<<36)) if identity['kind']=='HEALTH'", "(0x1804022 if identity['kind']=='LMKD' else 0x80000074ef if identity['kind']=='NETD' else ((1<<35)|(1<<36)) if identity['kind']=='HEALTH'")
text=text.replace("fields['NoNewPrivs']=='1'", "fields['NoNewPrivs']=='1'\n if identity['kind']=='SERVICES':assert list(map(int,fields['Groups'].split()))==[1003,1023,3006,3007]")
text=text.replace('NETD|LMKD','NETD|LMKD|ACONFIG_SYSTEM|ACONFIG_MAINLINE')
text=text.replace("'LMKD':'u:r:lmkd:s0'","'LMKD':'u:r:lmkd:s0','ACONFIG_SYSTEM':'u:r:aconfigd:s0','ACONFIG_MAINLINE':'u:r:aconfigd_mainline:s0'")
# Observe actual demand-start PID through the existing namespace observer.
text=text.replace("NETD|LMKD|ACONFIG_SYSTEM|ACONFIG_MAINLINE", "NETD|LMKD|ACONFIG_SYSTEM|ACONFIG_MAINLINE|ARTD")
text=text.replace("'LMKD':'u:r:lmkd:s0'", "'LMKD':'u:r:lmkd:s0','ARTD':'u:r:artd:s0'")
text=text.replace("1069 if identity['kind']=='LMKD' else ", "1082 if identity['kind']=='ARTD' else 1069 if identity['kind']=='LMKD' else ")
text=text.replace("0x1804022 if identity['kind']=='LMKD'", "0xf if identity['kind']=='ARTD' else 0x1804022 if identity['kind']=='LMKD'")
# Normalize only this diagnostic marker; result still requires the actual /proc identity.
text=text.replace("',line)", "',line.replace('LINUX_LAZY_STARTED interface=aidl/artd pid=', 'SELECTED_ARTD_STARTED pid='))")
# Preserve actual APEX output on Java/bootstrap failures as well.
marker="if p.returncode!=0:\n failed_output="
text=text.replace(marker,"""import hashlib
metadata=[];metadata_truncated=False
for file in sorted(Path('/metadata/aconfig').rglob('*')):
 if not file.is_file():continue
 if len(metadata)>=256:metadata_truncated=True;break
 info=file.stat()
 metadata.append({'path':str(file),'uid':info.st_uid,'gid':info.st_gid,'mode':oct(stat.S_IMODE(info.st_mode)),'context':os.getxattr(file,'security.selinux').decode().rstrip(chr(0)),'bytes':info.st_size,'sha256':hashlib.sha256(file.read_bytes()).hexdigest() if info.st_size<=33554432 else None})
print('ACONFIG_ORIGINAL_METADATA_FILES '+json.dumps({'files':metadata,'truncated':metadata_truncated,'scope':'Original daemon outputs, not flag or permission acceptance'}),flush=True)
for name in ['markor-preinstall-path.txt','markor-preinstall-dump.txt','markor-app-data.txt','markor-volumes.txt','markor-overlays.txt','selected-user-wait.txt','keystore-java.txt','keymint-provider.txt','keystore-component.txt','keymint-component.txt','storage-contract.txt','markor-user-state.txt','markor-bootstrap-home-stop.txt','markor-home-after.txt','markor-boot-before-user.txt','platform-capabilities.txt','linux-application-profile.txt','markor-postcommit-path.txt','markor-postcommit-dump.txt','markor-installed-bytes.txt','unadmitted-artd-control.txt','ranging-service-info.txt','ranging-permission.txt','netd-permission-query.txt','netd-query.txt','netd-interfaces.txt','stats-query.txt','selected-failure.txt','selected-wait.txt','health-query.txt','health-dump.txt','apex-query.txt','apex-active.txt','classpath','package-query.txt','package-list.txt','vold-query.txt','vold-user0.txt','markor-install.txt','markor-path.txt','markor-dump.txt','activity-query.txt','mount-query.txt','markor-user-start.txt','markor-resolve.txt','markor-launch.txt']:
 f=Path('/data/system/environ/classpath') if name=='classpath' else (Path('/data/local/tmp/archtv-apex-client') if name in ['apex-query.txt','apex-active.txt'] else Path('/data/local/tmp/archtv-mc1'))/name
 if f.is_file():print('PACKAGE_ORIGINAL_OUTPUT '+name+' '+json.dumps(f.read_text()),flush=True)
if p.returncode!=0:
 failed_output=""")
# Reuse exact accepted native APEX inventory verification (its own identities).
tree=ast.parse((r/'reports/android16-apex-bootstrap/execute.py').read_text())
checks=next(n.value.right.value for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.BinOp) and isinstance(n.value.right,ast.Constant) and isinstance(n.value.right.value,str) and n.value.right.value.startswith('\nfor name in'))
checks=checks.replace('for v in identities','for v in identities if v["kind"] in ["MANAGER","DAEMON","SNAPSHOT","DERIVE"]').replace('for identity in identities:','for identity in [v for v in identities if v["kind"] in ["MANAGER","DAEMON","SNAPSHOT","DERIVE"]]:')
# Preserve independent original inventory verification even if a later Java
# subsystem fails. Never turn that partial success into overall exit0.
checks=checks.replace('if p.returncode!=0:sys.exit(1)','')
# Integrated cohorts may deactivate APEX during original shutdown. Require the
# real live observation; retain identity checks above and closing XML below.
checks=checks[:checks.index("expected={m['name']")] + "assert live_apex_evidence.get('verified') is True,live_apex_evidence\nprint('APEX_ORIGINAL_CLASSPATH_PATHS_VERIFIED NOT_CLASSLOADER_OR_APK_ACCEPTANCE',flush=True)\nprint('APEX_ORIGINAL_COMPLETE_INVENTORY_VERIFIED modules='+str(len(live_apex_evidence['actual']))+' LIVE_XML_AND_MOUNTS_NOT_FRAMEWORK_BINDER_OR_APK_MAC_ACCEPTANCE',flush=True)\n"
if original_apex_bootstrap:
 checks=checks.replace('["MANAGER","DAEMON","SNAPSHOT","DERIVE"]','["MANAGER","DAEMON","SNAPSHOT","DERIVE","BOOTSTRAP"]')
 checks=checks.replace("'DERIVE':'u:r:derive_classpath:s0'}", "'DERIVE':'u:r:derive_classpath:s0','BOOTSTRAP':'u:r:apexd:s0'}")
 checks=checks.replace("'DERIVE':0}","'DERIVE':0,'BOOTSTRAP':0x200000}")


verify_always="try:\n exec(compile("+repr(checks)+",'<original APEX evidence verification>','exec'),globals())\nexcept Exception as apex_failure:\n print('APEX_ORIGINAL_INVENTORY_NOT_VERIFIED '+repr(apex_failure),flush=True)\n if p.returncode==0:raise\n"
assert marker in text
text=text.replace(marker,verify_always+marker,1)

text+="\nassert Path('/data/local/tmp/archtv-mc1/package-query.txt').read_text()=='Service package: found\\n'\npackage_list=Path('/data/local/tmp/archtv-mc1/package-list.txt').read_text().splitlines()\nassert 'package:android' in package_list and all(v.startswith('package:') for v in package_list),package_list\nprint('PACKAGES_ORIGINAL_LIST_VERIFIED NOT_INSTALL_DATA_OR_APK_ACCEPTANCE',flush=True)\n"
text+=r"""
# Original init_user0 invokes VDC itself; no unauthorized shell query gate.
# The native callback records its real result; storage topology follows.
ce_mounts=[line for line in Path('/proc/self/mountinfo').read_text().splitlines() if line.split()[4]=='/data/user/0']
data_mounts=[line for line in Path('/proc/self/mountinfo').read_text().splitlines() if line.split()[4]=='/data']
# vold may stack an identical /data bind on the Linux-owned data mount.
# Accept only equivalent roots/devices for every layer, never an arbitrary first
# mount or a guessed top layer. Actual CE/legacy inode equality remains below.
assert data_mounts and len(ce_mounts)==1,(data_mounts,ce_mounts)
data_backings={(line.split()[2],line.split()[3]) for line in data_mounts}
assert len(data_backings)==1,(data_mounts,ce_mounts)
data_device,data_root=next(iter(data_backings));ce_fields=ce_mounts[0].split()
assert (ce_fields[2],ce_fields[3])==(data_device,data_root.rstrip('/')+'/data'),(data_mounts,ce_mounts)
print('STORAGE_ORIGINAL_CE_ALIAS_MOUNTINFO '+json.dumps(ce_mounts),flush=True)
ce_info=Path('/data/user/0').stat();legacy_info=Path('/data/data').stat()
assert (ce_info.st_dev,ce_info.st_ino)==(legacy_info.st_dev,legacy_info.st_ino)
for path in ['/data/misc/apexdata/com.android.permission/access.abx','/data/misc_de/0/apexdata/com.android.permission/access.abx','/data/misc_de/0/apexdata/com.android.permission/runtime-permissions.xml']:
 f=Path(path);info=f.lstat()
 assert stat.S_ISREG(info.st_mode) and info.st_uid==1000 and 0<info.st_size<16777216,path
 import hashlib
 print('STORAGE_ORIGINAL_PERMISSION_FILE '+json.dumps({'path':path,'uid':info.st_uid,'gid':info.st_gid,'mode':oct(stat.S_IMODE(info.st_mode)),'sha256':hashlib.sha256(f.read_bytes()).hexdigest(),'context':os.getxattr(f,'security.selinux').decode().rstrip('\0')}),flush=True)
print('STORAGE_ORIGINAL_FILES_VERIFIED NOT_REOPEN_FBE_MAC_OR_APK_ACCEPTANCE',flush=True)
"""
text+=r"""
install=Path('/data/local/tmp/archtv-mc1/markor-install.txt').read_text()
assert 'Success' in install.splitlines(),install
paths=Path('/data/local/tmp/archtv-mc1/markor-postcommit-path.txt').read_text().splitlines()
assert len(paths)==1 and paths[0].startswith('package:/data/app/'),paths
installed=Path(paths[0][8:]);assert installed.is_file() and installed.name=='base.apk'
assert hashlib.sha256(installed.read_bytes()).hexdigest()=='c105bf5cc9530f7486b984323a185c17086b459a56ec936a5990ceb8da3d8440'
print('MARKOR_ORIGINAL_INSTALL_BYTES_VERIFIED NOT_LAUNCH_PERSISTENCE_MAC_OR_APK_COMPATIBILITY',flush=True)
"""
# A component-only profile must never inherit Markor/graphics acceptance.
identity_line=next(line for line in text.splitlines() if line.startswith("assert {v['kind']:v['actual_context'] for v in identities}=="))
full_expected=identity_line.split('==',1)[1]
if original_apex_bootstrap:full_expected=repr({**ast.literal_eval(full_expected),'BOOTSTRAP':'u:r:apexd:s0'})
component_expected={'MANAGER':'u:r:servicemanager:s0','HWMANAGER':'u:r:hwservicemanager:s0','VOLD':'u:r:vold:s0','DAEMON':'u:r:apexd:s0','SNAPSHOT':'u:r:apexd:s0','ACONFIG_SYSTEM':'u:r:aconfigd:s0','ACONFIG_MAINLINE':'u:r:aconfigd_mainline:s0','NETD':'u:r:netd:s0'}
text=text.replace(identity_line,"keymint_component_profile=Path('/vendor/etc/archtv-keymint-component').is_file()\nkeystore_component_profile=Path('/vendor/etc/archtv-keystore-component').is_file()\nsoftware_platform_profile=Path('/vendor/etc/archtv-software-security').is_file()\nassert not (keymint_component_profile and keystore_component_profile)\nexpected_identities="+full_expected+"\nif keymint_component_profile:\n assert Path('/vendor/etc/archtv-keymint-component').read_text()=='software-crypto-v1\\n'\n expected_identities="+repr(component_expected)+"\nassert {v['kind']:v['actual_context'] for v in identities}==expected_identities")
# Extend the existing real SID/credentials observer for the two original daemons.
text=text.replace('|ARTD)_STARTED','|ARTD|KEYMINT|KEYSTORE|GATEKEEPER_HAL|GATEKEEPER)_STARTED')
text=text.replace("'ARTD':'u:r:artd:s0'", "'ARTD':'u:r:artd:s0','KEYMINT':'u:r:hal_keymint_default:s0','KEYSTORE':'u:r:keystore:s0','GATEKEEPER_HAL':'u:r:hal_gatekeeper_default:s0','GATEKEEPER':'u:r:gatekeeperd:s0'")
text=text.replace("list(map(int,fields['Uid'].split()))==[", "list(map(int,fields['Uid'].split()))==[9999 if identity['kind']=='KEYMINT' else 1017 if identity['kind']=='KEYSTORE' else ")
text=text.replace("list(map(int,fields['Gid'].split()))==[", "list(map(int,fields['Gid'].split()))==[0 if identity['kind']=='KEYMINT' else 1017 if identity['kind']=='KEYSTORE' else ")
stock_identity_assignment=next(line for line in text.splitlines() if line.startswith('expected_identities='))
text=text.replace(stock_identity_assignment,'expected_identities='+full_expected,1)
text=text.replace("list(map(int,fields['Gid'].split()))==[", "list(map(int,fields['Gid'].split()))==[0 if identity['kind']=='GATEKEEPER' else ")
component_identity_assert="assert {v['kind']:v['actual_context'] for v in identities}==expected_identities"
assert component_identity_assert in text
keystore_expected={**component_expected,'KEYMINT':'u:r:hal_keymint_default:s0','KEYSTORE':'u:r:keystore:s0'}
software_expected={**ast.literal_eval(full_expected),'KEYMINT':'u:r:hal_keymint_default:s0','KEYSTORE':'u:r:keystore:s0','GATEKEEPER_HAL':'u:r:hal_gatekeeper_default:s0','GATEKEEPER':'u:r:gatekeeperd:s0'}
text=text.replace(component_identity_assert,"if keystore_component_profile:\n assert Path('/vendor/etc/archtv-keystore-component').read_text()=='software-keystore-v1\\n'\n expected_identities="+repr(keystore_expected)+"\n if software_platform_profile:\n  assert Path('/vendor/etc/archtv-software-security').read_text()=='software-platform-v1\\n'\n  expected_identities="+repr(software_expected)+"\n"+component_identity_assert)
storage_identities={'STORAGED':'u:r:storaged:s0','IDMAP':'u:r:idmap:s0','SWCODEC':'u:r:mediaswcodec:s0'}
text=text.replace('|GATEKEEPER)_STARTED','|GATEKEEPER|STORAGED|IDMAP|SWCODEC)_STARTED')
text=text.replace("'GATEKEEPER':'u:r:gatekeeperd:s0'", "'GATEKEEPER':'u:r:gatekeeperd:s0',"+repr(storage_identities)[1:-1])
text=text.replace(component_identity_assert,"if not keymint_component_profile and (not keystore_component_profile or software_platform_profile):\n expected_identities.update("+repr(storage_identities)+")\n"+component_identity_assert,1)
text=text.replace("list(map(int,fields['Uid'].split()))==[", "list(map(int,fields['Uid'].split()))==[0 if identity['kind']=='STORAGED' else 1046 if identity['kind']=='SWCODEC' else 1000 if identity['kind']=='IDMAP' else ")
text=text.replace("list(map(int,fields['Gid'].split()))==[", "list(map(int,fields['Gid'].split()))==[1032 if identity['kind']=='STORAGED' else 1006 if identity['kind']=='SWCODEC' else 1000 if identity['kind']=='IDMAP' else ")
for capability in ['CapEff','CapPrm']:
 text=text.replace("int(fields['"+capability+"'],16)==(","int(fields['"+capability+"'],16)==(4 if identity['kind']=='STORAGED' else ")
keystore_checks="""if software_platform_profile:
 for fixture_output in ['keymint-provider.txt','keystore-component.txt','keystore-ciphertext.bin','keystore-java.txt','java-ciphertext.bin']:
  assert not Path('/data/local/tmp/archtv-mc1/'+fixture_output).exists(), 'Functional startup must not reuse diagnostic fixture output'
 print('SECURITY_FIXTURES_NOT_EXECUTED REQUIRE_ORIGINAL_FUNCTIONAL_CONSUMERS',flush=True)
if keystore_component_profile and not software_platform_profile:
 provider=Path('/data/local/tmp/archtv-mc1/keymint-provider.txt').read_text().splitlines()
 output=Path('/data/local/tmp/archtv-mc1/keystore-component.txt').read_text().splitlines()
 assert len(provider)==1 and re.fullmatch(r'KEYMINT_BINDER_SOFTWARE_V4_OBSERVED pid=[1-9][0-9]* NOT_KEY_OR_APK_ACCEPTANCE',provider[0]),provider
 assert len(output)==2,output
 first=re.fullmatch(r'KEYSTORE_BINDER_GENERATED_ENCRYPTED metadata=SOFTWARE hardware_rejected=2 pid=([1-9][0-9]*) NOT_APK_OR_MAC_ACCEPTANCE',output[0])
 second=re.fullmatch(r'KEYSTORE_BINDER_REOPENED_DECRYPTED tamper_rejected=1 deleted=1 metadata=SOFTWARE pid=([1-9][0-9]*) NOT_APK_OR_MAC_ACCEPTANCE',output[1])
 assert first and second and first[1]!=second[1],output
 if not software_platform_profile:
  assert Path('/data/local/tmp/archtv-mc1/markor-launch.txt').read_text()==''
 if Path('/vendor/etc/archtv-keystore-java').is_file():
  assert Path('/vendor/etc/archtv-keystore-java').read_text()=='software-java-profile-v1\\n'
  java=Path('/data/local/tmp/archtv-mc1/keystore-java.txt').read_text().splitlines()
  first_java=[re.fullmatch(r'ORIGINAL_JCA_ENCRYPTED SOFTWARE strongbox_rejected=1 pid=([1-9][0-9]*) NOT_APK_OR_MAC_ACCEPTANCE',line) for line in java]
  second_java=[re.fullmatch(r'ORIGINAL_JCA_REOPENED SOFTWARE tamper_rejected=1 deleted=1 pid=([1-9][0-9]*) NOT_APK_OR_MAC_ACCEPTANCE',line) for line in java]
  first_java=[m[1] for m in first_java if m];second_java=[m[1] for m in second_java if m]
  assert len(first_java)==len(second_java)==1 and first_java[0]!=second_java[0],java
  print('ORIGINAL_JAVA_KEYSTORE_COMPONENT_VERIFIED NOT_USER_AUTH_MAC_OR_APK_ACCEPTANCE',flush=True)
 print('KEYSTORE_SOFTWARE_BINDER_COMPONENT_VERIFIED NOT_USER_AUTH_MAC_OR_APK_ACCEPTANCE',flush=True)
 if not software_platform_profile:sys.exit(0)
"""
component_checks="""if keymint_component_profile:
 output=Path('/data/local/tmp/archtv-mc1/keymint-component.txt').read_text().splitlines()
 assert output==['KEYMINT_COMPONENT_ENCRYPTED_AND_SAVED SOFTWARE v4 NOT_KEYSTORE_OR_APK_ACCEPTANCE','KEYMINT_COMPONENT_REOPEN_DECRYPT_AND_NEGATIVES_PASSED SOFTWARE v4 NOT_KEYSTORE_OR_APK_ACCEPTANCE'],output
 assert Path('/data/local/tmp/archtv-mc1/markor-launch.txt').read_text()==''
 print('KEYMINT_SOFTWARE_COMPONENT_VERIFIED NOT_KEYSTORE_USER_AUTH_MAC_OR_APK_ACCEPTANCE',flush=True)
 sys.exit(0)
"""
component_boundary="text=Path('/data/local/tmp/archtv-mc1/service-list.txt').read_text()"
assert component_boundary in text
text=text.replace(component_boundary,keystore_checks+component_checks+component_boundary,1)

# The Linux helper bundle remains root-only0700. Admit only the three
# hash-bound Android binaries at separate read-only paths for their real UIDs.
if (payload.parent/'keystore-component-inputs.json').exists():
 alias_inputs=json.loads((payload.parent/'keystore-component-inputs.json').read_text())['native']
 aliases={name:{'sha256':item['deployed_sha256'],'context':'u:object_r:'+{'archtv-keymint-software':'hal_keymint_default_exec','archtv-keystore2-software':'keystore_exec','archtv-keystore-client':'shell_exec','archtv-gatekeeper-software':'hal_gatekeeper_default_exec'}[name]+':s0'} for name,item in alias_inputs.items()}
 software_platform=json.loads((payload.parent/'build-options.json').read_text()).get('software_security_platform',False)
 assert set(aliases)==({'archtv-keymint-software','archtv-keystore2-software','archtv-keystore-client'} | ({'archtv-gatekeeper-software'} if software_platform else set()))
 alias_code="""
import hashlib
if (root/'vendor/etc/archtv-keystore-component').is_file():
 android_alias=root/'archtv-android';android_alias.mkdir(mode=0o755)
 assert lib.lsetfilecon_raw(str(android_alias).encode(),b'u:object_r:system_file:s0')==0,ctypes.get_errno()
 for name,expected in ALIAS_INPUTS.items():
  source=candidate/'bin'/name;info=source.lstat()
  assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and stat.S_IMODE(info.st_mode)==0o755
  assert hashlib.sha256(source.read_bytes()).hexdigest()==expected['sha256']
  assert os.getxattr(source,'security.selinux').decode().rstrip('\\0')==expected['context']
  # Original linkerconfig selects system/APEX namespace by executable path.
  # Bind the adapted daemon at its existing original system entry; do not copy
  # ICU out of its APEX or broaden fallback namespace library access.
  target=root/'system/bin/keystore2' if name=='archtv-keystore2-software' else android_alias/name
  if name=='archtv-keystore2-software':assert target.is_file() and not target.is_symlink()
  else:target.touch()
  mount('--bind',source,target);mount('-o','remount,bind,ro',target)
  assert (target.stat().st_dev,target.stat().st_ino)==(info.st_dev,info.st_ino)
  assert os.statvfs(target).f_flag & os.ST_RDONLY
  print('KEYSTORE_LINUX_NATIVE_ALIAS '+json.dumps({'path':'/'+str(target.relative_to(root)),'sha256':expected['sha256'],'context':expected['context'],'readonly':True}),flush=True)
 assert stat.S_IMODE((root/'archtv').stat().st_mode)==0o700
 assert stat.S_IMODE((root/'archtv/bin').stat().st_mode)==0o700
""".replace('ALIAS_INPUTS',repr(aliases))
 if (payload.parent/'keystore-java-inputs.json').exists():
  java_inputs=json.loads((payload.parent/'keystore-java-inputs.json').read_text())
  alias_code+='''
assert (root/'vendor/etc/archtv-keystore-java').read_text()=='software-java-profile-v1\\n'
framework_source=candidate/'bin/archtv-keystore-framework.jar';framework_target=root/'system/framework/framework.jar'
assert hashlib.sha256(framework_source.read_bytes()).hexdigest()==FRAMEWORK_SHA
assert hashlib.sha256(framework_target.read_bytes()).hexdigest()==ORIGINAL_FRAMEWORK_SHA
assert os.getxattr(framework_source,'security.selinux').decode().rstrip('\\0')=='u:object_r:system_file:s0'
mount('--bind',framework_source,framework_target);mount('-o','remount,bind,ro',framework_target)
assert os.statvfs(framework_target).f_flag & os.ST_RDONLY
print('KEYSTORE_ORIGINAL_FRAMEWORK_PROFILE '+json.dumps({'sha256':FRAMEWORK_SHA,'original_sha256':ORIGINAL_FRAMEWORK_SHA,'readonly':True,'scope':'experimental binary profile, not source rebuild or Java execution proof'}),flush=True)
'''.replace('ORIGINAL_FRAMEWORK_SHA',repr(java_inputs['original_framework_sha256'])).replace('FRAMEWORK_SHA',repr(java_inputs['framework_sha256']))
 alias_boundary="mount('--bind',candidate,root/'archtv');mount('-o','remount,bind,ro',root/'archtv')"
 assert text.count(alias_boundary)==1
 text=text.replace(alias_boundary,alias_boundary+'\n'+alias_code)

# AOSP setns() must operate on an actual namespace root, not a chroot
# into a host-root namespace: setns may reset fs.root to that namespace root.
# Keep the existing Linux observer outside, clone only the factory namespace,
# pivot to its prepared tmpfs, and detach the old host view before Bionic.
text=text.replace("os.chroot(root);os.chdir('/')",'''old_namespace=Path('/proc/self/ns/mnt').stat().st_ino
expected_root=root.stat()
# Share only this private target with the existing device observer before
# cloning. Its owned dm read-ahead binds must reach apexd after pivot_root.
mount('--make-shared',root/'sys/devices/virtual/block')
assert kernel.unshare(0x00020000)==0,ctypes.get_errno() # CLONE_NEWNS
assert Path('/proc/self/ns/mnt').stat().st_ino!=old_namespace
old=root/'.old-root';old.mkdir(mode=0o700)
assert kernel.syscall(155,str(root).encode(),str(old).encode())==0,ctypes.get_errno() # x86_64 pivot_root
os.chdir('/')
assert (Path('/').stat().st_dev,Path('/').stat().st_ino)==(expected_root.st_dev,expected_root.st_ino)
assert kernel.umount2(b'/.old-root',2)==0,ctypes.get_errno()
Path('/.old-root').rmdir()
# Original init order: shared isolated root, then public slave storage bind.
# Do this only after pivot_root detached the host. No disposable self-bind
# below /mnt; original vold's stale-mount cleanup must not strand /storage.
assert kernel.mount(None,b'/',None,1<<20,None)==0,ctypes.get_errno() # MS_SHARED
assert kernel.mount(b'/mnt/user/0',b'/storage',None,4096|16384,None)==0,ctypes.get_errno()
assert kernel.mount(None,b'/storage',None,(1<<19)|16384,None)==0,ctypes.get_errno()
print('LINUX_PUBLIC_STORAGE_SLAVE_PREPARED_AFTER_PIVOT',flush=True)
print('LINUX_PRIVATE_ROOT_PIVOTED old_host_view_detached',flush=True)
''')
# The enforcing boundary is admission, after trusted Linux preparation has
# pivoted and detached the host view. Do not advertise prepared before that.
gate="print('LINUX_PRIVATE_ROOT_PIVOTED old_host_view_detached',flush=True)"
assert text.count(gate)==1
text=text.replace(gate,gate+"""
if os.environ.pop('ARCHTV_MAC_STDIN_GATE',None)=='1':
 print('MAC_FACTORY_PREPARED_AWAITING_RELEASE',flush=True)
 assert os.read(0,1)==b'G', 'MAC controller did not release prepared factory'
""")

text=text.replace("'PATH':'/system/bin:/archtv/bin'","'PATH':'/system/bin'")
# Observe at the original export event while the Linux supervisor still runs. This is a
# single read-only sample in the existing stderr collector, not a readiness
# writer, monitor service, queue producer or permission substitute.
text=text.replace('errors=[];identities=[]','errors=[];identities=[];live_apex_evidence={}',1)
live_sample="""
  if 'PACKAGES_ORIGINAL_LOAD_EXPORTS_RETURNED ' in line and not live_apex_evidence:
   sample={'scope':'Original live XML, mounts and exported paths only; not Binder availability or APK/MAC acceptance','started_monotonic':time.monotonic(),'linux_supervisor_pid':p.pid}
   try:
    assert p.poll() is None,'Linux supervisor already terminal'
    import xml.etree.ElementTree as ET
    xml_path=Path('/apex/apex-info-list.xml');xml_bytes=xml_path.read_bytes();assert len(xml_bytes)<=262144
    elements=[e for e in ET.fromstring(xml_bytes) if e.attrib.get('isActive')=='true']
    actual={e.attrib['moduleName']:int(e.attrib['versionCode']) for e in elements}
    sample.update(xml_utf8=xml_bytes.decode(),xml_sha256=hashlib.sha256(xml_bytes).hexdigest(),active_modules=actual)
    expected={m['name']:m['version'] for m in json.loads(Path('/archtv/apex-expected.json').read_text())}
    assert len(elements)==len(actual) and actual==expected,{'actual':actual,'expected':expected}
    mounts={}
    for name,version in actual.items():
     for path in ['/apex/'+name,'/apex/'+name+'@'+str(version)]:
      node=Path(path);assert node.is_mount(),path
      st=node.stat();mounts[path]={'device':st.st_dev,'inode':st.st_ino}
    exports=Path('/data/system/environ/classpath').read_text();variables=set();jars=[]
    for row in exports.splitlines():
     export,name,value=row.split(' ',2)
     assert export=='export' and name in ['BOOTCLASSPATH','DEX2OATBOOTCLASSPATH','SYSTEMSERVERCLASSPATH','STANDALONE_SYSTEMSERVER_JARS'] and name not in variables
     variables.add(name)
     for jar in value.split(':'):
      assert jar.startswith(('/apex/','/system/')) and Path(jar).is_file(),jar
      jars.append(jar)
    assert len(variables)==4
    assert xml_path.read_bytes()==xml_bytes and p.poll() is None,'Linux supervisor or XML changed during sample'
    for path,identity in mounts.items():
     st=Path(path).stat();assert Path(path).is_mount() and [st.st_dev,st.st_ino]==[identity['device'],identity['inode']],path
    sample.update(verified=True,actual=actual,mounts=mounts,xml_utf8=xml_bytes.decode(),xml_sha256=hashlib.sha256(xml_bytes).hexdigest(),classpath=exports,jar_paths=jars)
   except Exception as error:sample.update(verified=False,error=repr(error))
   sample['finished_monotonic']=time.monotonic();live_apex_evidence.update(sample)
   print('APEX_LIVE_ORIGINAL_OBSERVATION '+json.dumps(sample),flush=True)
"""
assert text.count('  errors.append(line)\n')==1
text=text.replace('  errors.append(line)\n','  errors.append(line)\n'+('' if original_apex_bootstrap else live_sample),1)


if original_apex_bootstrap:
 candidate_mount="mount('-o','loop,ro,noload',r/"+repr(str(payload.relative_to(r)))+",candidate)"
 assert text.count(candidate_mount)==1
 text=text.replace(candidate_mount,"devices.mount_backing_image(r/"+repr(str(payload.relative_to(r)))+",candidate,128,out)",1)
 gsi_mount="mount('-o','loop,ro,noload','/home/tv/.cache/archtv/aosp16-qpr2/artifact-selection/gsi-original/system.img',gsi)"
 assert text.count(gsi_mount)==1
 text=text.replace(gsi_mount,"devices.mount_backing_image(Path('/home/tv/.cache/archtv/aosp16-qpr2/artifact-selection/gsi-original/system.img'),gsi,129,out)",1)
 old_prepare="devices.prepare(root,out,Path('/home/tv/.cache/archtv/aosp16-qpr2/apex-data-store-1'))"
 assert text.count(old_prepare)==1;text=text.replace(old_prepare,old_prepare[:-1]+",bootstrap=True)",1)
 # Empty mountpoints get their identity from original apexd creation/restorecon.
 # Do not pre-create aliases or pre-mount extracted APEX image roots from Linux.
 precreate="for p in (r/'dist/aosp16/factory-inputs-3/root/apex').iterdir():\n if p.is_dir():(root/'apex'/p.name).mkdir()\n elif p.is_file() and p.name!='apex-info-list.xml':shutil.copyfile(p,root/'apex'/p.name)\n"
 assert text.count(precreate)==1
 text=text.replace(precreate,"assert not any((root/'apex').iterdir()), 'Original APEX must start empty'\n",1)
 preview="for p in sorted((r/'dist/aosp16/factory-inputs-3').glob('*.payload.img')):\n target=root/'apex'/p.name.removesuffix('.payload.img');assert target.is_dir()\n kind=subprocess.check_output(['blkid','-p','-s','TYPE','-o','value',str(p)],text=True).strip()\n mount('-o','loop,ro,noload' if kind=='ext4' else 'loop,ro',p,target)\n"
 assert text.count(preview)==1;text=text.replace(preview,'',1)
 text=text.replace("(root/'bootstrap-apex').mkdir(exist_ok=True)","(root/'bootstrap-apex').mkdir(exist_ok=True);label(root/'bootstrap-apex')",1)
 text=text.replace("assert (root/'apex/com.android.runtime/bin/linker64').is_file(), 'Bootstrap runtime mount hidden'","assert (root/'system/bin/bootstrap/linker64').is_file() and not any((root/'apex').iterdir()), 'Original bootstrap entry requires empty APEX'",1)
 text=text.replace('APEX_(DAEMON|SNAPSHOT|DERIVE)','APEX_(DAEMON|SNAPSHOT|DERIVE|BOOTSTRAP)')
 text=text.replace("'DERIVE':'u:r:derive_classpath:s0'","'DERIVE':'u:r:derive_classpath:s0','BOOTSTRAP':'u:r:apexd:s0'")
 # Original RC: user root, group system, CAP_SYS_ADMIN, NNP remains1.
 loop="for identity in identities:\n fields="
 assert text.count(loop)==1
 text=text.replace(loop,"""for identity in identities:
 if identity['kind']=='BOOTSTRAP':
  fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in identity['status']}
  assert list(map(int,fields['Uid'].split()))==[0]*4 and list(map(int,fields['Gid'].split()))==[1000]*4
  assert int(fields['CapEff'],16)==0x200000 and int(fields['CapPrm'],16)==0x200000 and fields['NoNewPrivs']=='1'
  continue
 fields=""",1)
 # Read-only evidence bridge from the original worker's default namespace.
 # Original producers/kernel supply all bytes/stats. No service/API substitute.
 native_parse="""
try:
 native_stderr=''.join(errors)
 complete=re.findall(r'^APEX_NATIVE_EVIDENCE_COMPLETE pid=(\\d+) enforcing=([01]) NS_DEFAULT_NOT_BINDER_OR_APK_ACCEPTANCE$',native_stderr,re.M)
 assert len(complete)==1,'Missing unique original default-namespace evidence'
 worker,mode=complete[0];parts={}
 for kind in ['XML','MOUNTS']:
  matches=list(re.finditer(r'^APEX_NATIVE_'+kind+r'_BEGIN pid=(\\d+) enforcing=([01]) bytes=(\\d+)\\n(.*?)^APEX_NATIVE_'+kind+r'_END$',native_stderr,re.M|re.S))
  assert len(matches)==1,kind
  match=matches[0];assert match[1]==worker and match[2]==mode
  raw=match[4].encode();length=int(match[3]);assert 0<length<=1048576 and raw[length:] in [b'',b'\\n']
  parts[kind]=raw[:length]
 import xml.etree.ElementTree as ET
 elements=[e for e in ET.fromstring(parts['XML']) if e.attrib.get('isActive')=='true']
 actual={e.attrib['moduleName']:int(e.attrib['versionCode']) for e in elements}
 expected={m['name']:m['version'] for m in json.loads(Path('/archtv/apex-expected.json').read_text())}
 assert len(elements)==len(actual) and actual==expected,{'actual':actual,'expected':expected}
 mounts={line.split()[4] for line in parts['MOUNTS'].decode().splitlines()}
 for name,version in actual.items():
  assert '/apex/'+name in mounts and '/apex/'+name+'@'+str(version) in mounts,name
 jars={}
 for path,device,inode,size in re.findall(r'^APEX_NATIVE_JAR path=(\\S+) device=(\\d+) inode=(\\d+) size=(\\d+)$',native_stderr,re.M):
  value=[int(device),int(inode),int(size)];assert value[1]>0
  assert path not in jars or jars[path]==value,'JAR changed during snapshot'
  jars[path]=value
 exports=Path('/data/system/environ/classpath').read_text();variables=set();paths=set()
 for row in exports.splitlines():
  op,name,value=row.split(' ',2)
  assert op=='export' and name in ['BOOTCLASSPATH','DEX2OATBOOTCLASSPATH','SYSTEMSERVERCLASSPATH','STANDALONE_SYSTEMSERVER_JARS'] and name not in variables
  variables.add(name);paths.update(value.split(':'))
 assert len(variables)==4 and paths==set(jars),{'exports':paths,'native_jars':set(jars)}
 live_apex_evidence.update(verified=True,actual=actual,source='Original worker NS_DEFAULT read-only XML/mountinfo/JAR stat bridge',worker_pid=int(worker),enforcing=int(mode),xml_utf8=parts['XML'].decode(),mountinfo_utf8=parts['MOUNTS'].decode(),jar_stats=jars,classpath=exports)
except Exception as error:live_apex_evidence.update(verified=False,error=repr(error),source='Original worker namespace bridge; incomplete is not acceptance')
print('APEX_NATIVE_NAMESPACE_OBSERVATION '+json.dumps(live_apex_evidence),flush=True)
"""
 marker="print('MC1_RESULT '+json.dumps("
 assert text.count(marker)==1;text=text.replace(marker,native_parse+'\n'+marker,1)

compile(text,'<integrated factory>','exec')
if '--materialize-only' in saved:
 Path('/home/tv/.cache/archtv/integrated-factory-preview.py').write_text(text)
else:
 # Preserve the exact composed source per immutable execution before entering
 # any private runtime view; a mutable preview cannot locate a later traceback.
 import os
 if os.environ.get('ARCHTV_RUN_CHECKPOINT'):
  execution=Path(os.environ['ARCHTV_RUN_CHECKPOINT']).resolve()
  assert execution.parent==Path('/home/tv/recuperacion-archtv')
  if original_apex_bootstrap:
   import uuid
   manifest=json.loads((execution/'completion-manifest.json').read_text());run_id=manifest['id'];assert str(uuid.UUID(run_id))==run_id
   assert manifest['checkpoint']==str(execution)
   factory_name='apex-live-'+uuid.UUID(run_id).hex
   factory=r/'dist/aosp16'/factory_name
   assert len(str(factory/'root/dev/socket/logdw').encode())<=107, 'Private Unix socket path exceeds Linux limit'
   text=text.replace("('apex-live-'+str(time.time_ns()))",repr(factory_name),1)
   with (execution/'factory-path.json').open('x') as binding:json.dump({'id':run_id,'checkpoint':str(execution),'factory':str(factory)},binding)
  with (execution/'factory-materialized.py').open('x') as materialized:
   materialized.write(text);materialized.flush();os.fsync(materialized.fileno())
 exec(compile(text,'<integrated factory>','exec'),{'__name__':'__main__'})
