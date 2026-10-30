#!/usr/bin/env python3
"""Generate and compile selected complete pinned AIDL contracts (window by default)."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import zipfile

parser=argparse.ArgumentParser()
for name in ('sources','aidl-tools','tools','reference','output'):
    parser.add_argument('--'+name,type=Path,required=True)
parser.add_argument('--manifest',type=Path,default=Path('runtime/aosp/window-aidl-sources.json'))
args=parser.parse_args()
root=Path(__file__).resolve().parents[2]
inputs=json.loads((root/args.manifest).read_text())
toolchain=json.loads((root/'runtime/aosp/aidl-toolchain.json').read_text())
reference=json.loads((root/'runtime/aosp/compile-reference.json').read_text())
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def verify():
    for item in inputs['files']:
        path=args.sources/item['cache_path']
        assert path.stat().st_size==item['bytes'] and sha(path)==item['sha256'],str(path)
    for item in toolchain['artifacts']:
        path=args.aidl_tools/item['file']
        assert path.stat().st_size==item['bytes'] and sha(path)==item['sha256'],str(path)
    assert sha(args.reference)==reference['sha256']
verify()
fixture_tools=json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())
for item in fixture_tools['artifacts']:
    if item['file'] in ('r8.jar','android.jar'):assert sha(args.tools/item['file'])==item['sha256']
out=args.output.resolve();out.mkdir(parents=True,exist_ok=False)
for name in ('generated','classes','dex'):(out/name).mkdir()
env={k:v for k,v in os.environ.items() if k not in ('LD_LIBRARY_PATH','LD_PRELOAD')}
env['LD_LIBRARY_PATH']=str(args.aidl_tools.resolve())
aidl=args.aidl_tools.resolve()/'aidl'
primaries=[args.sources/p for p in inputs['roots']]
assert primaries and len(set(p.stem for p in primaries))==len(primaries)
commands=[]
def run(name,command):
    command=list(map(str,command));commands.append({'name':name,'command':command})
    with (out/(name+'.stdout')).open('wb') as stdout,(out/(name+'.stderr')).open('wb') as stderr:
        subprocess.run(command,env=env,stdout=stdout,stderr=stderr,check=True,timeout=120)
includes=[part for prefix in inputs['include_roots'] for part in ('-I',str(args.sources/prefix))]
for index,primary in enumerate(primaries):
    run('generate' if index==0 else 'generate-'+str(index),[aidl,'--lang=java','--min_sdk_version=28',
        *includes,'-o',out/'generated',primary])
sources=sorted((out/'generated').rglob('*.java'))
assert {p.name for p in sources}=={p.stem+'.java' for p in primaries}
root_names=[re.search(r'^package\s+([^;]+);',p.read_text(),re.M).group(1)+'.'+p.stem for p in primaries]
interface_names=[name for name in root_names if any(p.stem==name.rsplit('.',1)[1] and re.search(r'^public interface ',p.read_text(),re.M) for p in sources)]
assert interface_names
jdk=Path('/usr/lib/jvm/java-17-openjdk/bin')
run('compile',[jdk/'javac','--release','8','-classpath',args.reference,'-d',out/'classes',*sources])
run('pack',[jdk/'jar','cf',out/'bindings.jar','-C',out/'classes','.'])
run('dex',[jdk/'java','-cp',args.tools/'r8.jar','com.android.tools.r8.D8','--release','--min-api','28',
    '--lib',args.tools/'android.jar','--output',out/'dex',out/'bindings.jar'])
def transactions(path):
    return {name:int(value) for name,value in re.findall(r'static final int TRANSACTION_(\w+) = (\d+);',path.read_text())}
def methods(path):
    text=path.read_text()
    return sorted(re.findall(r'  public abstract ([^\n]+)\n    descriptor: ([^\n]+)',text))
contracts={}
for index,name in enumerate(interface_names):
    prefix='' if index==0 else str(index)+'-'
    run(prefix+'generated-signatures',[jdk/'javap','-p','-s','-classpath',out/'bindings.jar',name])
    run(prefix+'reference-signatures',[jdk/'javap','-p','-s','-classpath',args.reference,name])
    run(prefix+'generated-transactions',[jdk/'javap','-p','-constants','-classpath',out/'bindings.jar',name+'$Stub'])
    run(prefix+'reference-transactions',[jdk/'javap','-p','-constants','-classpath',args.reference,name+'$Stub'])
    actual=methods(out/(prefix+'generated-signatures.stdout'));expected=methods(out/(prefix+'reference-signatures.stdout'))
    transaction_ids=transactions(out/(prefix+'generated-transactions.stdout'));reference_ids=transactions(out/(prefix+'reference-transactions.stdout'))
    assert actual and expected and len(transaction_ids)==len(actual)
    assert actual==expected and transaction_ids==reference_ids,name+' differs from pinned reference'
    contracts[name]={'interface_methods_count':len(actual),'reference_methods_equal':True,
        'transaction_ids':transaction_ids,'reference_transaction_ids_equal':True}
with zipfile.ZipFile(out/'bindings.jar') as archive:
    classes=sorted(name for name in archive.namelist() if name.endswith('.class'))
    assert classes and all(any(n==name.replace('.','/')+'.class' or n.startswith(name.replace('.','/')+'$') for name in root_names) for n in classes)
# Preserve the primary-interface fields consumed by the window service generator.
primary_contract=contracts[interface_names[0]]
actual=methods(out/'generated-signatures.stdout');expected=methods(out/'reference-signatures.stdout')
transaction_ids=primary_contract['transaction_ids'];reference_ids=transactions(out/'reference-transactions.stdout')
verify()
(out/'provenance.json').write_text(json.dumps({'original_aidl_inputs':inputs,'toolchain':toolchain,'compile_reference':reference,
 'generated_root_types':root_names,'interface_contracts':contracts,'commands':commands,'generated_java_sha256':{str(path.relative_to(out)):sha(path) for path in sources},
 'runtime_classes':classes,'bindings_jar_sha256':sha(out/'bindings.jar'),'dex_sha256':sha(out/'dex/classes.dex'),
 'transaction_ids':transaction_ids,'reference_transaction_ids_equal':transaction_ids==reference_ids,
 'interface_methods_count':len(actual),'reference_methods_equal':actual==expected,
 'methods_only_generated':[list(m) for m in actual if m not in expected],
 'methods_only_reference':[list(m) for m in expected if m not in actual],
 'scope':'Complete selected original AIDL contracts generated with pinned official compiler and original transitive import contracts. No trimmed interface, imported implementation classes or reference bytecode copied. Method comparison is not proof of transaction ABI, native Binder IPC, loaded runtime classes or working window service.'},indent=2)+'\n')
print(out/'bindings.jar')
