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
compile(base, '<materialized graphics factory>', 'exec')
exec(compile(base, '<materialized graphics factory>', 'exec'), {'__name__': '__main__'})
