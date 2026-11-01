#!/usr/bin/env python3
"""Combine existing real APEX and original graphics factories; no Android boot."""
from pathlib import Path
import sys,ast
import xml.etree.ElementTree
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
spec=importlib.util.spec_from_file_location('apex_devices',r/'reports/android16-apex-bootstrap/devices.py')
devices=importlib.util.module_from_spec(spec);spec.loader.exec_module(devices)
""",1)
text=text.replace("elif p.is_file():shutil.copyfile(p,root/'apex'/p.name)","elif p.is_file() and p.name!='apex-info-list.xml':shutil.copyfile(p,root/'apex'/p.name)")
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
# Preserve actual APEX output on Java/bootstrap failures as well.
marker="if p.returncode!=0:\n failed_output="
text=text.replace(marker,"""for name in ['apex-query.txt','apex-active.txt','classpath','package-query.txt','package-list.txt']:
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
compile(text,'<integrated factory>','exec')
if '--materialize-only' in saved:
 Path('/home/tv/.cache/archtv/integrated-factory-preview.py').write_text(text)
else:
 exec(compile(text,'<integrated factory>','exec'),{'__name__':'__main__'})
