#!/usr/bin/env python3
"""One real VT/session with exact restoration and native completion delivery."""
from pathlib import Path
import subprocess,time,os,json,datetime
r=Path('/home/tv/repositorio-principal');stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');cp=Path('/home/tv/recuperacion-archtv')/(stamp+'-package-integration');cp.mkdir(mode=0o700)
cache=Path('/home/tv/.cache/archtv/kernel-aosp16-1');(cache/'apex-current-checkpoint').write_text(str(cp)+'\n')
out=r/'dist/aosp16'/('package-session-'+str(time.time_ns()));out.mkdir();os.chown(out,1000,1000);unit='archtv-package-display-'+str(time.time_ns());initial=subprocess.check_output(['fgconsole'],text=True).strip();assert initial.isdigit();sessions=subprocess.check_output(['loginctl','list-sessions','--no-legend'],text=True).strip()
for row in sessions.splitlines():
 fields=row.split();assert fields[1]=='1000',row
 info=subprocess.check_output(['loginctl','show-session',fields[0],'-p','Class','-p','Service','-p','TTY'],text=True)
 assert 'Class=manager' in info and 'Service=systemd-user' in info and '\nTTY=\n' in '\n'+info,info

before={'initial_vt':initial,'unit':unit,'output':str(out),'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'head':subprocess.check_output(['runuser','-u','tv','--','git','-C',str(r),'rev-parse','HEAD'],text=True).strip(),'pending':subprocess.check_output(['runuser','-u','tv','--','git','-C',str(r),'status','--short'],text=True)};(cp/'before.json').write_text(json.dumps(before,indent=2)+'\n');(cp/'RETOMAR.txt').write_text('Read before.json, output compositor.log and latest apex-current-checkpoint. External console: stop only archtv-package-display unit named in before.json; chvt initial_vt; systemctl unmask --runtime getty@tty2.service; systemctl start getty@tty2.service. Do not reuse historical PIDs. No policy/enforcing changes. Snapshot restoration has not been rehearsed.\n')
(cp/'pending.patch').write_bytes(subprocess.check_output(['runuser','-u','tv','--','git','-C',str(r),'diff','--binary']))
import hashlib
own=['runtime/aosp/native/linux-exec-context.c','runtime/aosp/native/linux-property-worker.cpp','runtime/aosp/native/linux-mc1-cohort.h','runtime/aosp/linux-services/org/archtv/aosplinux/SelectedServices.java','runtime/aosp/linux-services/install-markor.sh','reports/android16-apex-bootstrap/run.py','reports/android16-apex-bootstrap/execute.py']+[str(n.relative_to(r)) for n in (r/'reports/android16-package-bootstrap').glob('*.py')]+[str(n.relative_to(r)) for n in (r/'reports/android16-package-bootstrap').glob('*.sh')]
for name in own:
 destination=cp/'code'/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes((r/name).read_bytes())
before['own_code_sha256']={n:hashlib.sha256((r/n).read_bytes()).hexdigest() for n in own};before['payload_sha256']=hashlib.file_digest((r/'dist/aosp16/package-cohort-build-20/payload-2.ext4').open('rb'),'sha256').hexdigest();(cp/'before.json').write_text(json.dumps(before,indent=2)+'\n')
assert not Path('/run/systemd/system/getty@tty2.service').exists() and not Path('/run/systemd/system/getty@tty2.service').is_symlink()
subprocess.run(['systemctl','stop','getty@tty2.service'],check=True);subprocess.run(['systemctl','mask','--runtime','getty@tty2.service'],check=True)
try:
 subprocess.run(['systemd-run','--unit='+unit,'--service-type=exec','--property=User=tv','--property=PAMName=login','--property=TTYPath=/dev/tty2','--property=StandardInput=tty','--property=TTYReset=yes','--property=TTYVHangup=yes','--property=KillMode=control-group','--property=RuntimeMaxSec=190','/usr/bin/bash',str(r/'reports/android16-package-bootstrap/integrated-session.sh'),str(out)],check=True)
 subprocess.run(['chvt','2'],check=True)
 # Native bounded waiter only; no model wakeups while unchanged.
 end=time.monotonic()+200
 while time.monotonic()<end:
  if subprocess.run(['systemctl','is-active','--quiet',unit+'.service']).returncode!=0:break
  time.sleep(.25)
finally:
 subprocess.run(['systemctl','stop',unit+'.service']);subprocess.run(['chvt',initial],check=True);subprocess.run(['systemctl','unmask','--runtime','getty@tty2.service'],check=True)
log=(out/'compositor.log').read_text() if (out/'compositor.log').exists() else '';(cp/'session-result.json').write_text(json.dumps({'output':str(out),'unit':unit,'vt_restored':initial,'log_bytes':len(log),'scope':'Native session closed; inspect inner APEX/package results, no APK acceptance'},indent=2)+'\n');print(str(cp),flush=True)

# If no inner runner started, deliver the actual session failure once. The
# independent inner unit otherwise owns completion after device cleanup.
if (cache/'apex-current-checkpoint').read_text().strip()==str(cp):
 subprocess.run(['/usr/bin/python',str(cache/'apex-completion.py')],check=True)
