#!/usr/bin/env python3
"""Existing VT/input/capture observer, made reusable after the real299 race.

The original runtime remains the sole execution/result owner. Captures are
read-only evidence and cannot imply APK readiness or interrupt MAC restoration.
"""
from pathlib import Path
import subprocess,time,json,os,sys,hashlib,re,stat
from session_capture import publish_capture_request
assert os.geteuid()==0
cp=Path(sys.argv[1]).resolve()
assert cp.parent==Path('/home/tv/recuperacion-archtv')
before=json.loads((cp/'before-launch.json').read_text());run=before['id']
assert cp.name.startswith(run+'-')
unit='archtv-markor-session-'+run;runner='archtv-package-runner-'+run
capture_directory_fd=None

def request_capture():
 global capture_directory_fd
 if capture_directory_fd is None:
  runtime=json.loads((cp/'wayland-runtime.json').read_text())
  directory=Path('/run/user/1000')/('archtv-'+run)
  assert runtime['id']==run and runtime['path']==str(directory)
  capture_directory_fd=os.open(directory,os.O_RDONLY|os.O_DIRECTORY|os.O_NOFOLLOW|os.O_CLOEXEC)
  info=os.fstat(capture_directory_fd)
  assert (info.st_dev,info.st_ino,info.st_uid,info.st_gid)==(runtime['dev'],runtime['inode'],1000,1000)
  assert os.getxattr(capture_directory_fd,'security.selinux').rstrip(b'\0').decode()==runtime['context']
 return publish_capture_request(capture_directory_fd,run)


# Capture/input triggers are diagnostics, never APK/security acceptance. Native
# logd is authoritative in this profile; an empty passive log is not silence.
# Preserve logcat provenance explicitly instead of inventing SCM credentials.
display_seen={}
def display_event_lines(factory):
 live=factory/'android-log-live.jsonl'
 rows=live.read_text().splitlines() if live.exists() else []
 if rows:return rows
 source=Path('/home/tv/.local/share/archtv/experimental-userdata/vlc-cycle-277/data/local/tmp/archtv-mc1/original-logcat.txt')
 try:
  st=source.lstat()
  if not stat.S_ISREG(st.st_mode) or st.st_uid!=2000 or st.st_mode&0o022:return []
  with source.open('rb') as f:
   f.seek(max(0,st.st_size-2097152));text=f.read(2097152).decode(errors='replace')
 except OSError:return []
 result=[]
 for line in text.splitlines():
  match=re.match(r'^\d\d-\d\d \S+\s+1000\s+(\d+)\s+\d+\s+I ActivityTaskManager: (Displayed org\.videolan\.vlc/\S+.*)$',line)
  if not match:continue
  observed=display_seen.setdefault(line,time.monotonic())
  result.append(json.dumps({'tag':'ActivityTaskManager','message':match[2],'observed_monotonic':observed,'source':'original-logcat-threadtime','source_log_uid':1000,'logcat_pid_namespace_pid':int(match[1]),'source_path':str(source),'source_line':line,'scope':'Read-only original-log capture trigger; no SCM/SID or APK availability claim'}))
 return result
def original_display_record(event):
 return event.get('actual_sender_pid_uid_gid',[0,0,0])[1:]==[1000,1000] or (event.get('source')=='original-logcat-threadtime' and event.get('source_log_uid')==1000)

assert hashlib.sha256(Path('/home/tv/repositorio-principal/reports/android16-package-bootstrap/execute-integrated.py').read_bytes()).hexdigest()==before['external_executor_sha256']

def host_devices():
 result={}
 for name in ['card0','renderD128']:
  info=(Path('/dev/dri')/name).stat()
  result[name]={'mode':oct(info.st_mode&0o7777),'uid':info.st_uid,'gid':info.st_gid,'rdev':info.st_rdev,'inode':info.st_ino}
 return result
def host_sysrq():
 p=Path('/proc/sysrq-trigger');st=p.stat()
 return {'device':st.st_dev,'inode':st.st_ino,'mode':oct(st.st_mode&0o7777),'uid':st.st_uid,'gid':st.st_gid,'label':os.getxattr(p,'security.selinux').decode().rstrip(chr(0)),'readonly_mount':bool(os.statvfs(p).f_flag&os.ST_RDONLY)}
host_sysrq_before=host_sysrq()
factories_before=set(Path('/home/tv/repositorio-principal/dist/aosp16').glob('apex-live-*'))
capture_triggered=False
interaction=None
trigger_at=None
last_sample=0
samples=[]
last_request=0.0
host_devices_before=host_devices()
fuse_before=sorted(p.name for p in Path('/sys/fs/fuse/connections').iterdir())
subprocess.run(['alsactl','--file',str(cp/'alsa-before.state'),'store','0'],check=True)
initial=subprocess.check_output(['fgconsole'],text=True).strip();assert initial.isdigit();assert not subprocess.check_output(['loginctl','list-sessions','--no-legend'],text=True).strip()
mask=Path('/run/systemd/system/getty@tty2.service');assert not mask.exists() and not mask.is_symlink()
state={'id':run,'outer_unit':unit,'runner_unit':runner,'initial_vt':initial,'root_pid':os.getpid(),'root_boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'result':'pending','fuse_connections_before':fuse_before,'host_devices_before':host_devices_before,'host_sysrq_before':host_sysrq_before};(cp/'session-state.json').write_text(json.dumps(state,indent=2)+'\n');os.chown(cp/'session-state.json',1000,1000)
subprocess.run(['systemctl','stop','getty@tty2.service'],check=True);subprocess.run(['systemctl','mask','--runtime','getty@tty2.service'],check=True)
try:
 subprocess.run(['systemd-run','--unit='+unit,'--collect','--service-type=exec','--property=User=tv','--property=PAMName=login','--property=TTYPath=/dev/tty2','--property=StandardInput=tty','--property=TTYReset=yes','--property=TTYVHangup=yes','--property=KillMode=control-group','--property=TimeoutStopSec=5','--property=RuntimeMaxSec=990','/usr/bin/bash',str(cp/'session.sh'),str(cp)],check=True)
 subprocess.run(['chvt','2'],check=True)
 # Native bounded wait only: no model polling and no queue continuation.
 deadline=time.monotonic()+985
 while True:
  if not capture_triggered:
   factories=set(Path('/home/tv/repositorio-principal/dist/aosp16').glob('apex-live-*'))-factories_before
   assert len(factories)<=1, 'Concurrent unrelated factory'
   if factories:
    factory=next(iter(factories)); live=factory/'android-log-live.jsonl'
    if live.exists():
     for line in display_event_lines(factory):
      try:event=json.loads(line)
      except json.JSONDecodeError:continue
      if event.get('tag')=='ActivityTaskManager' and event.get('message','').startswith('Displayed org.videolan.vlc/') and original_display_record(event):
       (cp/'capture-trigger.json').write_text(json.dumps({'factory':str(factory),'event':event,'scope':'Original displayed event triggers read-only final DRM capture; no UI acceptance until image inspection'},indent=2)+'\n');os.chown(cp/'capture-trigger.json',1000,1000)
       request_capture();capture_triggered=True;trigger_at=time.monotonic();break
  if trigger_at is not None and interaction is None and time.monotonic()-trigger_at>=2:
   interaction=subprocess.Popen(['/usr/bin/python',str(cp/'interaction-test.py')],stdout=open(cp/'interaction-test.log','w'),stderr=subprocess.STDOUT)
  # Physical input is manually queued only after actual UI inspection.
  try:
   if capture_triggered:
    frame=cp/'screen.ppm'; request=cp/'capture.request'
    if frame.exists() and frame.stat().st_mtime_ns!=last_sample and not request.exists():
     last_sample=frame.stat().st_mtime_ns
     contents=frame.read_bytes();digest=hashlib.sha256(contents).hexdigest();archived=cp/('smithay-frame-'+digest+'.ppm')
     if not archived.exists():archived.write_bytes(contents);os.chown(archived,1000,1000)
     samples.append({'path':str(archived),'capture_mtime_ns':last_sample,'observed_monotonic':time.monotonic()})
     (cp/'capture-samples.json').write_text(json.dumps(samples,indent=2)+'\n');os.chown(cp/'capture-samples.json',1000,1000)
    if not request.exists() and time.monotonic()-last_request>.5:
     request_capture();last_request=time.monotonic()
  except OSError as error:
   # An observation failure must not terminate the original runtime or cause
   # final host checks while its enforcing window is still active.
   state['capture_observation_error']=repr(error)
  # Native bounded observer: preserve actual kernel PCM state, never inject
  # readiness or infer audible signal from a playback device being open.
  try:
   pcm={name:Path('/proc/asound/card0/pcm0p/sub0',name).read_text() for name in ['status','hw_params']}
  except OSError as error:pcm={'error':repr(error)}
  if not locals().get('mixer_sampled',False) and 'closed' not in pcm.get('status','closed'):
   sample=subprocess.run(['amixer','-c','0','scontents'],capture_output=True,timeout=5)
   (cp/'mixer-during-PCM.txt').write_bytes(sample.stdout+sample.stderr)
   mixer_sampled=True
  if pcm!=locals().get('last_pcm'):
   with (cp/'pcm-kernel-observations.jsonl').open('a') as f:f.write(json.dumps({'monotonic':time.monotonic(),'observation':pcm,'scope':'Read-only host kernel PCM state; not acoustic signal or APK acceptance'})+'\n')
   last_pcm=pcm
  record=cp/'completion-delivery.json'
  if record.exists():
   try:d=json.loads(record.read_text())
   except json.JSONDecodeError:d={}
   if d.get('id')==run and d.get('state') in ('active_owned','consumed'):
    active=subprocess.run(['systemctl','is-active','--quiet',runner+'.service']).returncode==0
    if not active:
     state['result']='native_result_recorded'
     # Let the owned parent archive its typed runtime before any forced stop.
     close_deadline=time.monotonic()+8
     while subprocess.run(['systemctl','is-active','--quiet',unit+'.service']).returncode==0 and time.monotonic()<close_deadline:time.sleep(.1)
     state['natural_parent_close_observed']=subprocess.run(['systemctl','is-active','--quiet',unit+'.service']).returncode!=0
     state['frontend_archive_observed']=(cp/'frontend-runtime-archive.json').is_file()
     break
  if subprocess.run(['systemctl','is-active','--quiet',unit+'.service']).returncode!=0:
   state['result']='outer_session_ended_before_native_result';break
  if time.monotonic()>deadline:state['result']='native_wait_deadline';break
  time.sleep(.2)
finally:
 # Preserve the single native runner owner and its preopened-FD restoration.
 # Do not kill it or the frontend because a read-only capture raced. Wait for
 # its real service termination before host metadata/recovery verification.
 close_deadline=time.monotonic()+990
 while True:
  observed=subprocess.run(['systemctl','show',runner+'.service','-p','MainPID','-p','ActiveState','-p','LoadState'],capture_output=True,text=True)
  values=dict(line.split('=',1) for line in observed.stdout.splitlines() if '=' in line)
  terminal=values.get('ActiveState') in ('inactive','failed') or values.get('LoadState')=='not-found'
  if terminal and values.get('MainPID','0')=='0':break
  assert time.monotonic()<close_deadline, 'Original runner still alive; retain recovery evidence'
  time.sleep(.2)
 if capture_directory_fd is not None:os.close(capture_directory_fd)
 if subprocess.run(['systemctl','is-active','--quiet',unit+'.service']).returncode==0:subprocess.run(['systemctl','stop',unit+'.service'],check=True)
 subprocess.run(['chvt',initial],check=True);subprocess.run(['systemctl','unmask','--runtime','getty@tty2.service'],check=True)
 if interaction is not None:
  try:state['interaction_exit']=interaction.wait(timeout=8)
  except subprocess.TimeoutExpired:interaction.terminate();state['interaction_exit']=interaction.wait(timeout=5)
 subprocess.run(['alsactl','--file',str(cp/'alsa-before.state'),'restore','0'],check=True)
 subprocess.run(['alsactl','--file',str(cp/'alsa-after.state'),'store','0'],check=True)
 subprocess.run(['systemctl','stop','archtv-audio-rollback-'+run+'.timer'],check=True)
 state['host_sysrq_before']=host_sysrq_before;state['host_sysrq_after']=host_sysrq();state['host_sysrq_metadata_unchanged']=state['host_sysrq_after']==host_sysrq_before
 state['host_devices_after']=host_devices();state['host_device_metadata_unchanged']=state['host_devices_after']==host_devices_before
 state['fuse_connections_after']=sorted(p.name for p in Path('/sys/fs/fuse/connections').iterdir());state['new_fuse_connections']=sorted(set(state['fuse_connections_after'])-set(fuse_before))
 state['final_vt']=subprocess.check_output(['fgconsole'],text=True).strip();state['outer_active']=subprocess.run(['systemctl','is-active','--quiet',unit+'.service']).returncode==0
 state['runner_active']=subprocess.run(['systemctl','is-active','--quiet',runner+'.service']).returncode==0
 if (cp/'wayland-runtime.json').exists():subprocess.run(['/usr/bin/python','/home/tv/repositorio-principal/reports/android16-package-bootstrap/execute-integrated.py','--close-wayland-runtime',str(cp)],check=True)
 (cp/'session-state.json').write_text(json.dumps(state,indent=2)+'\n');os.chown(cp/'session-state.json',1000,1000)
client_evidence={}
source=Path('/home/tv/.local/share/archtv/experimental-userdata/vlc-cycle-277/data/local/tmp/archtv-mc1')
for name in ['media-before.txt','media-id.txt','media-insert.txt','media-write.txt','media-publish.txt','media-published.txt','media-uri.txt','media-bytes.txt','media-query-error.txt','media-read-error.txt','media-readback.mp4','android-ps-before.txt','android-ps-postinstall.txt','android-ps-after.txt','android-ps-error.txt','android-ps-status.txt','android-app-status.txt','markor-install.txt','markor-launch.txt','markor-resolve.txt','markor-app-data.txt','markor-installed-bytes.txt','original-logcat.txt']:
 p=source/name
 try:
  st=p.lstat();assert stat.S_ISREG(st.st_mode) and st.st_uid==2000 and st.st_size<=33554432
  data=p.read_bytes();q=cp/('observed-'+name);q.write_bytes(data);os.chown(q,1000,1000)
  client_evidence[name]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
 except FileNotFoundError:client_evidence[name]={'exists':False}
 except (OSError,AssertionError) as error:client_evidence[name]={'capture_error':str(error)}
(cp/'original-client-evidence.json').write_text(json.dumps(client_evidence,indent=2)+'\n');os.chown(cp/'original-client-evidence.json',1000,1000)
print(json.dumps(state),flush=True)
assert state['host_sysrq_metadata_unchanged'],'Host SysRq metadata changed; stop and diagnose'
for n in ['result.json','completion-delivery.json']:
 p=cp/n
 if p.exists():
  d=json.loads(p.read_text());print(n,json.dumps({k:d.get(k) for k in ['outer_exit','native_complete_inventory_verified','active_loops','final_dm','state']}),flush=True)
if state['result']!='native_result_recorded':
 print(subprocess.check_output(['journalctl','-u',unit+'.service','--no-pager','-n','30'],text=True),flush=True)
 sys.exit(1)
