#!/usr/bin/env python3
"""Combine existing real APEX and original graphics factories; no Android boot."""
from pathlib import Path
import sys,ast
import xml.etree.ElementTree, hashlib
# Resolve the Linux verification hash provider before entering the chroot.
hashlib.sha256(b"").digest()
r=Path(__file__).resolve().parents[2]
socket=sys.argv[1];payload=Path(sys.argv[2]).resolve();store=Path(sys.argv[3]).resolve()
# Materialize the existing graphics adapter, then add the tested APEX boundary.
recipe=(r/'reports/android16-hwc3-wayland/execute-graphics.py').read_text()
last="exec(compile(base, '<materialized graphics factory>', 'exec'), {'__name__': '__main__'})"
assert last in recipe
scope={'__name__':'__materialize__','__file__':str(r/'reports/android16-hwc3-wayland/execute-graphics.py')}
saved=sys.argv;sys.argv=[str(r/'reports/android16-hwc3-wayland/execute-graphics.py'),socket,'--observe-logs','--surfaceflinger','--selected-display']
exec(compile(recipe.replace(last,''),'<graphics materialization>','exec'),scope)
text=scope['base'];text=text.replace("('mc3-live-'+str(time.time_ns()))","('apex-live-'+str(time.time_ns()))")
text=text.replace('dist/aosp16/sf-cohort-build-32/payload-2.ext4',str(payload.relative_to(r)))
text=text.replace('len(observed_logs)<512','len(observed_logs)<4096')
text=text.replace("'--display-integration'","'--packages-integration'").replace("'--startup-ms','45000'","'--startup-ms','150000'").replace("'--observe-ms','30000'","'--observe-ms','3000'")
text=text.replace('root.mkdir()\n',"""root.mkdir()
import importlib.util
factory_caps=int(next(l.split(':',1)[1].strip() for l in Path('/proc/self/status').read_text().splitlines() if l.startswith('CapEff:')),16)
spec=importlib.util.spec_from_file_location('apex_devices',r/'reports/android16-apex-bootstrap/devices.py')
devices=importlib.util.module_from_spec(spec);spec.loader.exec_module(devices)
""",1)
text=text.replace("elif p.is_file():shutil.copyfile(p,root/'apex'/p.name)","elif p.is_file() and p.name!='apex-info-list.xml':shutil.copyfile(p,root/'apex'/p.name)")
# Only top-level roots from pinned original init.rc. Vold creates user dirs,
# CE alias mounts and original permission data; no user metadata is seeded.
roots=[('misc/vold',0o700,0,0),('misc/profiles',0o771,1000,1000),('misc/profiles/cur',0o771,1000,1000),('misc/profiles/ref',0o771,1000,1000),('misc/apexdata',0o711,0,0),('system/users',0o775,1000,1000),('media',0o550,1023,1023),('misc_ce',0o551,1000,9998),('system_ce',0o550,1000,1000),('user_de',0o511,1000,1000),('vendor_ce',0o551,0,0),('vendor_de',0o551,0,0)]
root_code="\n".join("p=root/'data'/"+repr(name)+";p.mkdir(parents=True,exist_ok=True);os.chmod(p,"+str(mode)+");os.chown(p,"+str(uid)+","+str(gid)+")" for name,mode,uid,gid in roots)
apk_path=Path('/home/tv/.cache/archtv/apk/real-app-candidates/net.gsantner.markor-v164-2026.10.0-flavorDefault-release.apk')
apk_sha='c105bf5cc9530f7486b984323a185c17086b459a56ec936a5990ceb8da3d8440'
assert hashlib.sha256(apk_path.read_bytes()).hexdigest()==apk_sha
root_code+="\np=root/'data/local/tmp/archtv-mc1/markor-install.txt';p.touch(mode=0o600);os.chown(p,1000,1000)"
root_code+="\nshutil.copyfile(Path("+repr(str(apk_path))+"),root/'data/local/tmp/markor.apk');os.chown(root/'data/local/tmp/markor.apk',2000,2000);os.chmod(root/'data/local/tmp/markor.apk',0o644)"
text=text.replace('label(root)\n',root_code+'\nlabel(root)\n',1)
text=text.replace('label(root)\n',"devices.prepare(root,out,Path("+repr(str(store))+"))\nassert not (root/'apex/apex-info-list.xml').exists()\nlabel(root)\n",1)
text=text.replace("for p in sorted((r/'dist/aosp16/factory-inputs-3').glob('*.payload.img')):","devices.mount_sysfs(root)\nfor p in sorted((r/'dist/aosp16/factory-inputs-3').glob('*.payload.img')):",1)
text=text.replace("mount('-t','proc','proc',root/'proc')","devices.enable_loop_controls(root,out)\nmount('-t','proc','proc',root/'proc')")
text=text.replace("cgbase=Path('/sys/fs/cgroup/system.slice/codex-remote.service/archtv-mc1')", "unit_cgroup=Path('/proc/self/cgroup').read_text().split('0::',1)[1].strip()\nassert unit_cgroup.startswith('/system.slice/archtv-apex-') and unit_cgroup.endswith('.service')\ncgbase=Path('/sys/fs/cgroup'+unit_cgroup)/'archtv-apex'")
text=text.replace("stdin_fd=os.open(root/'dev/null'", "monitor_log=(out/'device-monitor.log').open('w')\nmonitor=subprocess.Popen([sys.executable,str(r/'reports/android16-apex-bootstrap/devices.py'),str(root),str(out),str(os.getpid())],stdout=monitor_log,stderr=subprocess.STDOUT)\nprint('APEX_DEVICE_MONITOR_OWNED pid='+str(monitor.pid),flush=True)\nstdin_fd=os.open(root/'dev/null'",1)
text=text.replace('log_stop=True\n','monitor.terminate();monitor.wait(timeout=3);monitor_log.close()\nlog_stop=True\n',1)
text=text.replace("os.chown(root/'data/local/tmp/archtv-mc1',2000,2000)","os.chown(root/'data/local/tmp/archtv-mc1',2000,1000);os.chmod(root/'data/local/tmp/archtv-mc1',0o750)")
# The existing graphics verifier retains its eight exact service identities.
# Observe apexd identities in the same real /proc sampling branch.
text=text.replace("SELECTED_(SUSPEND|SERVICES|INSTALLD)_STARTED pid=(\\d+)',line)","SELECTED_(SUSPEND|SERVICES|INSTALLD)_STARTED pid=(\\d+)|APEX_(DAEMON|SNAPSHOT)_STARTED pid=(\\d+)',line)")
text=text.replace('(match[5] or match[7])','(match[5] or match[7] or match[9])').replace('int(match[2] or match[4] or match[6] or match[8])','int(match[2] or match[4] or match[6] or match[8] or match[10])')
text=text.replace("'INSTALLD':'u:r:installd:s0'","'INSTALLD':'u:r:installd:s0','DAEMON':'u:r:apexd:s0','SNAPSHOT':'u:r:apexd:s0'")
text=text.replace("identity['kind']=='INSTALLD'","identity['kind'] in ['INSTALLD','DAEMON','SNAPSHOT']")
# Avoid applying installd capabilities to apexd: native exact original RC masks.
text=text.replace("0x2000ff if identity['kind'] in ['INSTALLD','DAEMON','SNAPSHOT'] else", "0x20000f if identity['kind']=='DAEMON' else 0xf if identity['kind']=='SNAPSHOT' else 0x2000ff if identity['kind']=='INSTALLD' else")
text=text.replace("fields['Gid'].split()))==[0 if identity['kind'] in ['INSTALLD','DAEMON','SNAPSHOT']", "fields['Gid'].split()))==[0 if identity['kind']=='INSTALLD'")
text=text.replace('SUSPEND|SERVICES|INSTALLD','SUSPEND|SERVICES|INSTALLD|VOLD')
text=text.replace("'INSTALLD':'u:r:installd:s0'","'INSTALLD':'u:r:installd:s0','VOLD':'u:r:vold:s0'")
text=text.replace("identity['kind'] in ['INSTALLD','DAEMON','SNAPSHOT']","identity['kind'] in ['INSTALLD','DAEMON','SNAPSHOT','VOLD']")
text=text.replace("fields['Gid'].split()))==[0 if identity['kind']=='INSTALLD'","fields['Gid'].split()))==[0 if identity['kind'] in ['INSTALLD','VOLD']")
text=text.replace("0x20000f if identity['kind']=='DAEMON'","factory_caps if identity['kind']=='VOLD' else 0x20000f if identity['kind']=='DAEMON'")
# Preserve actual APEX output on Java/bootstrap failures as well.
marker="if p.returncode!=0:\n failed_output="
text=text.replace(marker,"""for name in ['apex-query.txt','apex-active.txt','classpath','package-query.txt','package-list.txt','vold-query.txt','vold-user0.txt','markor-install.txt','markor-path.txt','markor-dump.txt','activity-query.txt','mount-query.txt']:
 f=Path('/data/local/tmp/archtv-mc1')/name
 if f.is_file():print('PACKAGE_ORIGINAL_OUTPUT '+name+' '+json.dumps(f.read_text()),flush=True)
if p.returncode!=0:
 failed_output=""")
# Reuse exact accepted native APEX inventory verification (its own identities).
tree=ast.parse((r/'reports/android16-apex-bootstrap/execute.py').read_text())
checks=next(n.value.right.value for n in tree.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.BinOp) and isinstance(n.value.right,ast.Constant) and isinstance(n.value.right.value,str) and n.value.right.value.startswith('\nfor name in'))
checks=checks.replace('for v in identities','for v in identities if v["kind"] in ["MANAGER","DAEMON","SNAPSHOT"]').replace('for identity in identities:','for identity in [v for v in identities if v["kind"] in ["MANAGER","DAEMON","SNAPSHOT"]]:')
text+='\n'+checks
text+="\nassert Path('/data/local/tmp/archtv-mc1/package-query.txt').read_text()=='Service package: found\\n'\npackage_list=Path('/data/local/tmp/archtv-mc1/package-list.txt').read_text().splitlines()\nassert 'package:android' in package_list and all(v.startswith('package:') for v in package_list),package_list\nprint('PACKAGES_ORIGINAL_LIST_VERIFIED NOT_INSTALL_DATA_OR_APK_ACCEPTANCE',flush=True)\n"
text+=r"""
assert Path('/data/local/tmp/archtv-mc1/vold-query.txt').read_text()=='Service vold: found\n'
ce_mounts=[line for line in Path('/proc/self/mountinfo').read_text().splitlines() if line.split()[4]=='/data/user/0']
assert len(ce_mounts)==1 and ce_mounts[0].split()[3]=='/data/data',ce_mounts
print('STORAGE_ORIGINAL_CE_ALIAS_MOUNTINFO '+json.dumps(ce_mounts),flush=True)
assert Path('/data/user/0').stat().st_ino==Path('/data/data').stat().st_ino
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
paths=Path('/data/local/tmp/archtv-mc1/markor-path.txt').read_text().splitlines()
assert len(paths)==1 and paths[0].startswith('package:/data/app/'),paths
installed=Path(paths[0][8:]);assert installed.is_file() and installed.name=='base.apk'
assert hashlib.sha256(installed.read_bytes()).hexdigest()=='c105bf5cc9530f7486b984323a185c17086b459a56ec936a5990ceb8da3d8440'
print('MARKOR_ORIGINAL_INSTALL_BYTES_VERIFIED NOT_LAUNCH_PERSISTENCE_MAC_OR_APK_COMPATIBILITY',flush=True)
"""
compile(text,'<integrated factory>','exec')
if '--materialize-only' in saved:
 Path('/home/tv/.cache/archtv/integrated-factory-preview.py').write_text(text)
else:
 exec(compile(text,'<integrated factory>','exec'),{'__name__':'__main__'})
