from pathlib import Path
import json,subprocess,importlib.util,hashlib
r=Path('/home/tv/repositorio-principal');linker=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-toolchain-1/bin/ld.lld');crt=r/'dist/aosp16/crt-native-1';out=r/'dist/aosp16/property-libs-native-1';records=[]
def run(args):
 p=subprocess.run(list(map(str,args)),capture_output=True,text=True);records.append({'argv':list(map(str,args)),'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr});(out/'link-commands-2.json').write_text(json.dumps(records,indent=2)+'\n');print(p.returncode,p.stderr[:2000]);assert p.returncode==0;return p
run([linker,'--version']);run([linker,'-r',crt/'crtbegin_dynamic-part.o',crt/'crtbrand.o','-o',crt/'crtbegin_dynamic.o'])
spec=importlib.util.spec_from_file_location('audit',r/'tools/aosp/audit_boot_inputs.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);root=r/'dist/aosp16/factory-inputs-3/root'
libs=[m.inside(root,'/system/lib64/'+name+'.so') for name in ['libbase','libc++','libc','libm','libdl']];assert all(p.is_file() for p in libs)
run([linker,'-pie','--dynamic-linker','/system/bin/linker64','--build-id=sha1','--no-undefined','-z','relro','-z','now',crt/'crtbegin_dynamic.o',out/'property_info_tool.o','--start-group',out/'libpropertyinfoserializer.a',out/'libpropertyinfoparser.a','--end-group',*libs,crt/'crtend_android.o','-o',out/'property-info'])
elf=run(['readelf','-h','-l','-d',out/'property-info']).stdout;assert 'GLIBC_' not in subprocess.check_output(['readelf','-V',out/'property-info'],text=True);(out/'property-info.elf.txt').write_text(elf);print('Native executable linked',hashlib.sha256((out/'property-info').read_bytes()).hexdigest())
