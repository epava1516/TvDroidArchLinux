from pathlib import Path
import json,subprocess,hashlib
r=Path('/home/tv/repositorio-principal');inputs=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs');b=inputs/'bionic-libc/source';out=r/'dist/aosp16/crt-native-1';out.mkdir();command=json.loads((r/'dist/aosp16/libcap-native-1/commands.json').read_text())[3]['argv'];print(command[0])
# Use the recorded target-only C configuration, without libcap-specific headers.
flags=command[1:command.index('-c')];remove=[]
for i,x in enumerate(flags):
 if x.startswith('-I') and ('/libcap' in x or '/generated' in x):remove.append(x)
flags=[x for x in flags if x not in remove]+['-I'+str(b),'-I'+str(b/'bionic'),'-I'+str(b/'private'),'-I'+str(b/'arch-common/bionic'),'-fno-stack-protector','-Wall','-Werror','-Wno-gcc-compat']
records=[]
for name,src in [('crtbegin_dynamic-part','crtbegin.c'),('crtbrand','crtbrand.S'),('crtend_android','crtend.S')]:
 source=b/'arch-common/bionic'/src;argv=[command[0],*flags,*(['-DPLATFORM_SDK_VERSION=36'] if src=='crtbrand.S' else []),'-c',str(source),'-o',str(out/(name+'.o'))];p=subprocess.run(argv,text=True,capture_output=True);records.append({'argv':argv,'exit_code':p.returncode,'stdout':p.stdout,'stderr':p.stderr,'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest()});(out/'commands.json').write_text(json.dumps(records,indent=2)+'\n');print(name,p.returncode,flush=True)
 if p.returncode:raise SystemExit(p.stderr)
print('Original CRT source objects compiled; original linker combine pending')
