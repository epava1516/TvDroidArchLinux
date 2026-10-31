from pathlib import Path
import subprocess,time,os,json
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16'/('sf-session-'+str(time.time_ns()));out.mkdir();os.chown(out,1000,1000);unit='archtv-mc3-sf-'+str(time.time_ns());initial=subprocess.check_output(['fgconsole'],text=True).strip();assert initial.isdigit();assert not subprocess.check_output(['loginctl','list-sessions','--no-legend'],text=True).strip()
assert not Path('/run/systemd/system/getty@tty2.service').is_symlink() and not Path('/run/systemd/system/getty@tty2.service').exists()
subprocess.run(['systemctl','stop','getty@tty2.service'],check=True)
subprocess.run(['systemctl','mask','--runtime','getty@tty2.service'],check=True)
try:
 subprocess.run(['systemd-run','--unit='+unit,'--collect','--service-type=exec','--property=User=tv','--property=PAMName=login','--property=TTYPath=/dev/tty2','--property=StandardInput=tty','--property=TTYReset=yes','--property=TTYVHangup=yes','--property=KillMode=control-group','--property=TimeoutStopSec=5','--property=RuntimeMaxSec=110','/usr/bin/bash',str(r/'reports/android16-software-renderer/sf-session.sh'),str(out)],check=True)
 subprocess.run(['chvt','2'],check=True)
 for _ in range(1100):
  time.sleep(.1)
  if subprocess.run(['systemctl','is-active','--quiet',unit+'.service']).returncode!=0:break
finally:
 subprocess.run(['systemctl','stop',unit+'.service']);subprocess.run(['chvt',initial],check=True)
 subprocess.run(['systemctl','unmask','--runtime','getty@tty2.service'],check=True)
log=(out/'compositor.log').read_text() if (out/'compositor.log').exists() else ''
print('SESSION_OUTPUT '+str(out),flush=True);print(log[-18000:],flush=True)
(r/'reports/android16-software-renderer/last-session.json').write_text(json.dumps({'output':str(out),'unit':unit,'initial_vt':initial,'scope':'Original allocator/composer/coordinator integration candidate, permissive only; inspect real logs and pixels; not APK acceptance'},indent=2)+'\n')
assert 'MC3_ORIGINAL_SF_QUERIES_VERIFIED' in log and 'DRM_CAPTURED' in log and 'TV_COMPOSITOR_STOPPED' in log and 'WAYLAND_COMMIT_FAILED' not in log and 'WAYLAND_CONNECT_FAILED' not in log
