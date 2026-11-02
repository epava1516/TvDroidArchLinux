#!/usr/bin/env python3
"""Compose original health and already-used graphics TE before Linux/AOSP policy."""
from pathlib import Path
import runpy,subprocess,json,hashlib,sys
r=Path(__file__).resolve().parents[2];out=(r/sys.argv[1]).resolve();out.mkdir()
old=runpy.run_path(str(r/'reports/android16-hwc3-wayland/prepare-vendor-policy.py'))
source=old['SOURCE'];require=old['REQUIRE'].replace('module graphics_vendor','module health_graphics_vendor').replace(' attribute halserverdomain;', ' attribute bpfdomain; attribute hal_health; attribute hal_health_server; attribute halserverdomain;').replace(' type init;', ' type charger_vendor; type hal_health_server_tmpfs; type init;')
inputs=[source/name for name in ['public/global_macros','public/ioctl_defines','public/ioctl_macros','public/te_macros','vendor/hal_graphics_allocator_default.te','vendor/hal_graphics_composer_default.te','vendor/hal_health_default.te']]
argv=['m4','-Dtarget_full_treble=true','-Dtarget_build_variant=user']+list(map(str,inputs));expanded=subprocess.check_output(argv,text=True)
(out/'health_vendor.te').write_text(require+expanded+'\nrole r types { hal_health_default hal_graphics_allocator_default hal_graphics_composer_default };\n')
compiler=r/'dist/aosp16/selinux-tools-host-4/source/checkpolicy/checkmodule';cmd=[str(compiler),'-m','-M','-C','-o',str(out/'health_graphics_vendor.cil'),str(out/'health_vendor.te')];p=subprocess.run(cmd,capture_output=True,text=True)
record={'m4':argv,'inputs':{str(f):hashlib.sha256(f.read_bytes()).hexdigest() for f in inputs},'argv':cmd,'exit':p.returncode,'stderr':p.stderr,'scope':'Entire original health TE including charger transition, no invented allows. Offline; charger service never started.'};(out/'build.json').write_text(json.dumps(record,indent=2));assert p.returncode==0,p.stderr
lines=(out/'health_graphics_vendor.cil').read_text().splitlines();removed=[l for l in lines if 'cil_gen_require' in l];assert all(l.startswith(('(typeattributeset cil_gen_require ','(roleattributeset cil_gen_require ')) for l in removed)
base=r/'dist/aosp16/factory-inputs-3/root/system/etc/selinux/plat_sepolicy.cil';merged=base.read_bytes()+b'\n'+('\n'.join(l for l in lines if l not in removed)+'\n').encode();(out/'platform-with-vendor.cil').write_bytes(merged)
profile=json.loads((r/'reports/android16-hwmanager-cohort/profile.json').read_text());assert hashlib.sha256(base.read_bytes()).hexdigest()==profile['input_sha256']['aosp'];profile['input_sha256']['aosp']=hashlib.sha256(merged).hexdigest();profile['limitations'].append('Original health vendor TE composed offline; not load, service or MAC acceptance.');(out/'profile.json').write_text(json.dumps(profile,indent=2))
