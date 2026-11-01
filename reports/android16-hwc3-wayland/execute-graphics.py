#!/usr/bin/env python3
"""Run the bounded graphics cohort in an already isolated Linux factory.

Requires loaded candidate policy, a real Linux compositor-owned Wayland socket,
and host devices. Caller must supply PID/mount/net/ipc/uts isolation and timeout.
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
base = (ROOT / 'reports/android16-hwmanager-cohort/execute.py').read_text()
base = base.replace("('mc1-live-'+str(time.time_ns()))", "('mc3-live-'+str(time.time_ns()))")
base = base.replace("for n in ['system','apex','linkerconfig','data','dev','proc','sys','vendor','odm','archtv']:(root/n).mkdir()", """for n in ['system','apex','linkerconfig','data','dev','proc','sys','vendor','odm','archtv']:(root/n).mkdir()
candidate=out/'candidate';candidate.mkdir()
mount('-o','loop,ro,noload',r/'dist/aosp16/graphics-cohort-build-5/payload-2.ext4',candidate)
mount('--bind',candidate/'vendor',root/'vendor');mount('-o','remount,bind,ro',root/'vendor')
""")
base = base.replace("shutil.copytree(r/'dist/aosp16/linux-failure-sink-worker-1/vendor',root/'vendor',dirs_exist_ok=True)", '')
start = base.index("if '--with-diagnostic-vintf' in sys.argv[1:]:")
end = base.index("shutil.copytree(r/'dist/aosp16/linux-selinux-handoff-2/linkerconfig-mc1'", start)
base = base[:start] + base[end:]
base = base.replace("fc=out/'original-file-contexts';shutil.copyfile(root/'system/etc/selinux/plat_file_contexts',fc)", """fc=out/'original-file-contexts';fc.write_bytes((root/'system/etc/selinux/plat_file_contexts').read_bytes()+b'\\n'+(root/'vendor/etc/selinux/vendor_file_contexts').read_bytes())""")
base = base.replace("dirs[:]=[n for n in dirs if Path(base)/n!=root/'system']", "dirs[:]=[n for n in dirs if Path(base)/n not in [root/'system',root/'vendor']]")
base = base.replace("mount('-o','loop,ro,noload',r/'dist/aosp16/hwmanager-cohort-4/payload-2.ext4',root/'archtv')", """mount('--bind',candidate,root/'archtv');mount('-o','remount,bind,ro',root/'archtv')
(root/'dev/dri').mkdir()
assert lib.lsetfilecon_raw(str(root/'dev/dri').encode(),b'u:object_r:gpu_device:s0')==0
for node in ['card0','renderD128']:
 actual=os.stat('/dev/dri/'+node);assert stat.S_ISCHR(actual.st_mode)
 p=root/'dev/dri'/node;os.mknod(p,stat.S_IFCHR|0o660,actual.st_rdev);os.chmod(p,0o660);os.chown(p,0,1003)
 assert lib.lsetfilecon_raw(str(p).encode(),b'u:object_r:gpu_device:s0')==0
# Original libdrm drmNodeIsDRM stats the real GPU sysfs tree before classifying
# a node. Export that device subtree read-only, not all host sysfs or a fake
# successful node test. Preserve the kernel's actual char-device symlink.
gpu_roots=set()
for node in ['card0','renderD128']:
 actual=os.stat('/dev/dri/'+node);key=str(os.major(actual.st_rdev))+':'+str(os.minor(actual.st_rdev))
 original=Path('/sys/dev/char')/key;gpu=(original/'device').resolve(strict=True)
 assert str(gpu).startswith('/sys/devices/')
 destination=root/str(gpu).lstrip('/')
 if gpu not in gpu_roots:
  destination.mkdir(parents=True,exist_ok=True)
  mount('--bind',gpu,destination);mount('-o','remount,bind,ro',destination);gpu_roots.add(gpu)
 link=root/'sys/dev/char'/key;link.parent.mkdir(parents=True,exist_ok=True)
 link.symlink_to(os.readlink(original))
 assert (link/'device/drm').is_dir()
 print('MC3_REAL_GPU_SYSFS_RO '+str(gpu)+' char='+key,flush=True)
peer=Path(sys.argv[1]);assert stat.S_ISSOCK(peer.stat().st_mode)
target=root/'dev/socket/archtv-wayland';target.touch();mount('--bind',peer,target)
""")
base = base.replace("'--hardware-integration'", "'--graphics-integration'")
base = base.replace("os.chown(root/'data/local/tmp/archtv-mc1',2000,2000)", """os.chown(root/'data/local/tmp/archtv-mc1',2000,2000)
(root/'data/misc/surfaceflinger').mkdir(parents=True,mode=0o700)
os.chown(root/'data/misc/surfaceflinger',1000,1003)
""")
old = """  match=re.search(r'MC1_(MANAGER|HWMANAGER)_STARTED pid=(\\d+)',line)
  if match:
   kind=match[1];expected='u:r:hwservicemanager:s0' if kind=='HWMANAGER' else 'u:r:servicemanager:s0';pid=int(match[2]);seen=[];seen_errors=[];deadline=time.monotonic()+1"""
new = """  match=re.search(r'MC1_(MANAGER|HWMANAGER)_STARTED pid=(\\d+)|MC3_GRAPHICS_SERVICE_STARTED name=(\\S+) pid=(\\d+)',line)
  if match:
   kind=match[1] if match[1] else ('ALLOCATOR' if match[3]=='vendor.graphics.allocator' else 'COMPOSER')
   expected={'MANAGER':'u:r:servicemanager:s0','HWMANAGER':'u:r:hwservicemanager:s0','ALLOCATOR':'u:r:hal_graphics_allocator_default:s0','COMPOSER':'u:r:hal_graphics_composer_default:s0'}[kind]
   pid=int(match[2] or match[4]);seen=[];seen_errors=[];deadline=time.monotonic()+1"""
assert old in base
base = base.replace(old,new)
base = base.replace("{'MANAGER':'u:r:servicemanager:s0','HWMANAGER':'u:r:hwservicemanager:s0'}", "{'MANAGER':'u:r:servicemanager:s0','HWMANAGER':'u:r:hwservicemanager:s0','ALLOCATOR':'u:r:hal_graphics_allocator_default:s0','COMPOSER':'u:r:hal_graphics_composer_default:s0'}")
base = base.replace("list(map(int,fields['Gid'].split()))==[1000]*4", "list(map(int,fields['Gid'].split()))==[1003 if identity['kind'] in ['ALLOCATOR','COMPOSER'] else 1000]*4")
base = base.replace("int(fields['CapEff'],16)==0 and int(fields['CapPrm'],16)==0", "int(fields['CapEff'],16)==(1<<23 if identity['kind'] in ['ALLOCATOR','COMPOSER'] else 0) and int(fields['CapPrm'],16)==(1<<23 if identity['kind'] in ['ALLOCATOR','COMPOSER'] else 0)")
base += """
report=Path('/data/misc/surfaceflinger/archtv-integration.txt');info=report.lstat()
assert stat.S_ISREG(info.st_mode) and info.st_uid==1000 and info.st_gid==1003 and stat.S_IMODE(info.st_mode)==0o600 and 0<info.st_size<65536
assert os.getxattr(report,'security.selinux').rstrip(b'\\0')==b'u:object_r:surfaceflinger_data_file:s0'
observed=report.read_text();assert 'MC3_COMMANDS_ACCEPTED physical_timing_not_proven' in observed
print('MC3_EXPERIMENTAL_CLIENT_FILE_OBSERVED '+json.dumps(observed),flush=True)
"""
if '--surfaceflinger' in sys.argv[1:]:
    base = base.replace('dist/aosp16/graphics-cohort-build-5/payload-2.ext4', 'dist/aosp16/sf-cohort-build-7/payload-2.ext4')
    base = base.replace("'--graphics-integration'", "'--surfaceflinger-integration'")
    base = base.replace("'--observe-ms','150'", "'--observe-ms','60000'")
    base = base.replace("pid=(\\d+)',line)", "pid=(\\d+)|MC3_ORIGINAL_(SF|BOOTANIMATION)_STARTED pid=(\\d+)',line)")
    base = base.replace("('ALLOCATOR' if match[3]=='vendor.graphics.allocator' else 'COMPOSER')", "(('ALLOCATOR' if match[3]=='vendor.graphics.allocator' else 'COMPOSER') if match[3] else match[5])")
    base = base.replace("int(match[2] or match[4])", "int(match[2] or match[4] or match[6])")
    base = base.replace("'COMPOSER':'u:r:hal_graphics_composer_default:s0'", "'COMPOSER':'u:r:hal_graphics_composer_default:s0','SF':'u:r:surfaceflinger:s0','BOOTANIMATION':'u:r:bootanim:s0'")
    base = base.replace("['ALLOCATOR','COMPOSER']", "['ALLOCATOR','COMPOSER','SF']")
    base = base.replace("[1000]*4 and", "[1003 if identity['kind']=='BOOTANIMATION' else 1000]*4 and")
    base = base.replace("[1003 if identity['kind'] in ['ALLOCATOR','COMPOSER','SF'] else 1000]*4", "[1003 if identity['kind'] in ['ALLOCATOR','COMPOSER','SF','BOOTANIMATION'] else 1000]*4")
    # Retain real query output even when a later native client fails. These are
    # evidence files, never readiness signals or substitutes for Binder calls.
    base = base.replace("if p.returncode!=0:\n failed_output=", """for name in ['sf-query.txt','sf-aidl-query.txt']:
 report=Path('/data/local/tmp/archtv-mc1')/name
 if report.is_file():
  info=report.lstat();assert stat.S_ISREG(info.st_mode) and info.st_uid==2000 and info.st_gid==2000 and stat.S_IMODE(info.st_mode)==0o600 and info.st_size<1024
  assert os.getxattr(report,'security.selinux').rstrip(b'\\0')==b'u:object_r:shell_data_file:s0'
  print('MC3_ORIGINAL_QUERY_FILE_OBSERVED '+name+' '+json.dumps(report.read_text()),flush=True)
if p.returncode!=0:
 failed_output=""")

    # The API harness report is inapplicable to original clients. Retain the
    # manager assertions and check the original Binder CLI outputs instead.
    base = base[:base.index("\nreport=Path('/data/misc/surfaceflinger/archtv-integration.txt')")]
    base += """
for name, expected in [('sf-query.txt','Service SurfaceFlinger: found\\n'),('sf-aidl-query.txt','Service SurfaceFlingerAIDL: found\\n')]:
 report=Path('/data/local/tmp/archtv-mc1')/name;info=report.lstat()
 assert stat.S_ISREG(info.st_mode) and info.st_uid==2000 and info.st_gid==2000 and stat.S_IMODE(info.st_mode)==0o600 and info.st_size<1024
 assert os.getxattr(report,'security.selinux').rstrip(b'\\0')==b'u:object_r:shell_data_file:s0'
 observed=report.read_text();print('MC3_ORIGINAL_SF_QUERY '+json.dumps(observed),flush=True);assert observed==expected
print('MC3_ORIGINAL_SF_QUERIES_VERIFIED NOT_PIXEL_MAC_OR_APK_ACCEPTANCE',flush=True)
"""
if '--selected-display' in sys.argv[1:]:
    base = base.replace("'--observe-ms','60000'", "'--observe-ms','30000','--startup-ms','45000'")
    # Keep bounded diagnostic frames after ART namespace messages.
    base = base.replace('len(observed_logs)<256', 'len(observed_logs)<512')
    assert '--surfaceflinger' in sys.argv[1:]
    base = base.replace('sf-cohort-build-7/payload-2.ext4', 'sf-cohort-build-29/payload-2.ext4')
    base = base.replace("'--surfaceflinger-integration'", "'--display-integration'")
    base = base.replace("args=['/archtv/bin/native-supervisor'", "assert not Path('/sys/power/state').exists() and not Path('/sys/power/wakeup_count').exists()\nprint('SELECTED_HOST_POWER_CONTROLS_ABSENT original_SystemSuspend_host_managed_path',flush=True)\nargs=['/archtv/bin/native-supervisor'")

    base = base.replace("MC3_ORIGINAL_(SF|BOOTANIMATION)_STARTED pid=(\\d+)',line)", "MC3_ORIGINAL_(SF|BOOTANIMATION)_STARTED pid=(\\d+)|SELECTED_(SUSPEND|SERVICES)_STARTED pid=(\\d+)',line)")
    base = base.replace("else match[5])", "else (match[5] or match[7]))")
    base = base.replace("int(match[2] or match[4] or match[6])", "int(match[2] or match[4] or match[6] or match[8])")
    base = base.replace("'BOOTANIMATION':'u:r:bootanim:s0'", "'BOOTANIMATION':'u:r:bootanim:s0','SUSPEND':'u:r:system_suspend:s0','SERVICES':'u:r:system_server:s0'")
    base = base.replace("(1<<23 if identity['kind'] in ['ALLOCATOR','COMPOSER','SF'] else 0)", "(1<<36 if identity['kind']=='SUSPEND' else 1<<23 if identity['kind'] in ['ALLOCATOR','COMPOSER','SF','SERVICES'] else 0)")

    base = base.replace("(root/'data/misc/surfaceflinger').mkdir(parents=True,mode=0o700)", """(root/'data/system').mkdir(mode=0o775)
os.chown(root/'data/system',1000,1000)
(root/'data/misc/surfaceflinger').mkdir(parents=True,mode=0o700)""")
    base = base.replace("for name in ['sf-query.txt','sf-aidl-query.txt']:", "for name in ['sf-query.txt','sf-aidl-query.txt','display-query.txt','display-ids.txt']:")
    # Retain a bounded original dump on failures too. A dumped display is
    # evidence, not an ACK or a synthesized result to the Android process.
    base = base.replace("if p.returncode!=0:\n failed_output=", """display=Path('/data/local/tmp/archtv-mc1/display-dump.txt')
if display.is_file():
 info=display.lstat();assert info.st_uid==2000 and info.st_gid==2000 and stat.S_IMODE(info.st_mode)==0o600 and info.st_size<524288
 assert os.getxattr(display,'security.selinux').rstrip(b'\\0')==b'u:object_r:shell_data_file:s0'
 print('SELECTED_DISPLAY_ORIGINAL_DUMP '+json.dumps(display.read_text()),flush=True)
if p.returncode!=0:
 failed_output=""")
    base += """
query=Path('/data/local/tmp/archtv-mc1/display-query.txt').read_text()
ids=Path('/data/local/tmp/archtv-mc1/display-ids.txt').read_text()
assert query=='Service display: found\\n' and '0' in ids.splitlines()
print('SELECTED_DISPLAY_QUERIES_VERIFIED NOT_APK_OR_MAC_ACCEPTANCE',flush=True)
"""
compile(base, '<materialized graphics factory>', 'exec')
exec(compile(base, '<materialized graphics factory>', 'exec'), {'__name__': '__main__'})
