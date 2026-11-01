#!/usr/bin/env python3
"""Materialize the existing isolated factory for original apexd, not Android boot."""
from pathlib import Path
import argparse
# Load verifier dependencies before the private chroot; never feed XML to apexd.
import xml.etree.ElementTree

REPO=Path(__file__).resolve().parents[2]
parser=argparse.ArgumentParser()
parser.add_argument('--payload',required=True,type=Path)
parser.add_argument('--data-store',required=True,type=Path)
parser.add_argument('--observe-logs',action='store_true')
parser.add_argument('--materialize-only',type=Path)
options=parser.parse_args()
payload=options.payload.resolve()
data_store=options.data_store.resolve()
assert payload.is_relative_to(REPO/'dist/aosp16') and payload.is_file()
text=(REPO/'reports/android16-hwmanager-cohort/execute.py').read_text()
text=text.replace("('mc1-live-'+str(time.time_ns()))","('apex-live-'+str(time.time_ns()))")
text=text.replace("root.mkdir()\n", """root.mkdir()
import importlib.util
spec=importlib.util.spec_from_file_location('apex_devices',r/'reports/android16-apex-bootstrap/devices.py')
devices=importlib.util.module_from_spec(spec);spec.loader.exec_module(devices)
""",1)
text=text.replace("elif p.is_file():shutil.copyfile(p,root/'apex'/p.name)","elif p.is_file() and p.name!='apex-info-list.xml':shutil.copyfile(p,root/'apex'/p.name)")
text=text.replace("label(root)\n", "devices.prepare(root,out,Path("+repr(str(data_store))+"))\nassert not (root/'apex/apex-info-list.xml').exists(), 'No derived inventory may enter this test'\nlabel(root)\n",1)
text=text.replace("for p in sorted((r/'dist/aosp16/factory-inputs-3').glob('*.payload.img')):","devices.mount_sysfs(root)\nfor p in sorted((r/'dist/aosp16/factory-inputs-3').glob('*.payload.img')):",1)
text=text.replace("r/'dist/aosp16/hwmanager-cohort-4/payload-2.ext4'",repr(str(payload)))
text=text.replace("mount('-t','proc','proc',root/'proc')","devices.enable_loop_controls(root,out)\nmount('-t','proc','proc',root/'proc')")
text=text.replace("cgbase=Path('/sys/fs/cgroup/system.slice/codex-remote.service/archtv-mc1')", """unit_cgroup=Path('/proc/self/cgroup').read_text().split('0::',1)[1].strip()
assert unit_cgroup.startswith('/system.slice/archtv-apex-') and unit_cgroup.endswith('.service'),unit_cgroup
cgbase=Path('/sys/fs/cgroup'+unit_cgroup)/'archtv-apex'""")
text=text.replace("stdin_fd=os.open(root/'dev/null'", """monitor_log=(out/'device-monitor.log').open('w')
monitor=subprocess.Popen([sys.executable,str(r/'reports/android16-apex-bootstrap/devices.py'),str(root),str(out),str(os.getpid())],stdout=monitor_log,stderr=subprocess.STDOUT)
print('APEX_DEVICE_MONITOR_OWNED pid='+str(monitor.pid),flush=True)
stdin_fd=os.open(root/'dev/null'""",1)
text=text.replace("'--hardware-integration'","'--apex-integration'")
text=text.replace("'--observe-ms','150'","'--observe-ms','3000','--startup-ms','150000'")
old="""  match=re.search(r'MC1_(MANAGER|HWMANAGER)_STARTED pid=(\\d+)',line)
  if match:
   kind=match[1];expected='u:r:hwservicemanager:s0' if kind=='HWMANAGER' else 'u:r:servicemanager:s0';pid=int(match[2]);seen=[];seen_errors=[];deadline=time.monotonic()+1"""
new="""  match=re.search(r'MC1_(MANAGER)_STARTED pid=(\\d+)|APEX_(DAEMON|SNAPSHOT)_STARTED pid=(\\d+)',line)
  if match:
   kind=match[1] or match[3];expected='u:r:servicemanager:s0' if kind=='MANAGER' else 'u:r:apexd:s0';pid=int(match[2] or match[4]);seen=[];seen_errors=[];deadline=time.monotonic()+1"""
assert old in text;text=text.replace(old,new)
text=text.replace('len(observed_logs)<256','len(observed_logs)<512')
text=text.replace("log_stop=True\n", "monitor.terminate();monitor.wait(timeout=3);monitor_log.close()\nlog_stop=True\n",1)
boundary=text.index("\nif p.returncode!=0:\n failed_output=")
text=text[:boundary]+'''
for name in ['apex-query.txt','apex-active.txt','classpath']:
 result=Path('/data/local/tmp/archtv-mc1')/name
 if result.is_file():
  info=result.lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==0 and info.st_gid==(1000 if name=='classpath' else 0) and stat.S_IMODE(info.st_mode)==(0o640 if name=='classpath' else 0o600) and info.st_size<=262144
  print('APEX_ORIGINAL_OUTPUT '+name+' '+json.dumps(result.read_text()),flush=True)
xml=Path('/apex/apex-info-list.xml')
if xml.is_file():
 assert xml.stat().st_size<=262144
 print('APEX_ORIGINAL_XML '+json.dumps(xml.read_text()),flush=True)
 print('APEX_ORIGINAL_XML_LABEL '+repr(os.getxattr(xml,'security.selinux')),flush=True)
if p.returncode!=0:sys.exit(1)
assert {v['kind']:v['actual_context'] for v in identities}=={'MANAGER':'u:r:servicemanager:s0','DAEMON':'u:r:apexd:s0','SNAPSHOT':'u:r:apexd:s0'}
for identity in identities:
 fields={line.split(':',1)[0]:line.split(':',1)[1].strip() for line in identity['status']}
 expected_uid=1000 if identity['kind']=='MANAGER' else 0
 expected_caps={'MANAGER':0,'DAEMON':0x20000f,'SNAPSHOT':0xf}[identity['kind']]
 assert list(map(int,fields['Uid'].split()))==[expected_uid]*4 and list(map(int,fields['Gid'].split()))==[1000]*4
 assert int(fields['CapEff'],16)==expected_caps and int(fields['CapPrm'],16)==expected_caps and fields['NoNewPrivs']=='1'
query=Path('/data/local/tmp/archtv-mc1/apex-query.txt').read_text()
assert query=='Service apexservice: found\\n'
expected={m['name']:m['version'] for m in json.loads(Path('/archtv/apex-expected.json').read_text())}
actual={}
for line in Path('/data/local/tmp/archtv-mc1/apex-active.txt').read_text().splitlines():
 match=re.fullmatch(r'Module: (\\S+) Version: (\\d+) VersionName:.* Path: (\\S+) IsActive: true IsFactory: (true|false) Partition: (\\S+)',line)
 assert match,line
 assert match[1] not in actual
 actual[match[1]]=int(match[2])
assert actual==expected,{'expected':expected,'actual':actual}
import xml.etree.ElementTree as ET
from_xml={e.attrib['moduleName']:int(e.attrib['versionCode']) for e in ET.fromstring(xml.read_bytes()) if e.attrib.get('isActive')=='true'}
assert from_xml==expected,{'xml':from_xml,'expected':expected}
for name,version in expected.items():
 assert Path('/apex/'+name+'@'+str(version)).is_mount(),name
 assert Path('/apex/'+name).is_mount(),name
classpath=Path('/data/local/tmp/archtv-mc1/classpath').read_text()
classpath_names=set()
for line in classpath.splitlines():
 export,name,value=line.split(' ',2)
 assert export=='export' and name in ['BOOTCLASSPATH','DEX2OATBOOTCLASSPATH','SYSTEMSERVERCLASSPATH','STANDALONE_SYSTEMSERVER_JARS']
 assert name not in classpath_names
 classpath_names.add(name)
 for path in value.split(':'):
  assert path.startswith(('/apex/','/system/')) and Path(path).is_file(),path
assert len(classpath_names)==4
print('APEX_ORIGINAL_CLASSPATH_PATHS_VERIFIED NOT_CLASSLOADER_OR_APK_ACCEPTANCE',flush=True)
print('APEX_ORIGINAL_COMPLETE_INVENTORY_VERIFIED modules='+str(len(actual))+' NOT_APK_OR_MAC_ACCEPTANCE',flush=True)
'''
compile(text,'<materialized APEX factory>','exec')
if options.materialize_only:
    options.materialize_only.write_text(text)
else:
    exec(compile(text,'<materialized APEX factory>','exec'),{'__name__':'__main__'})
