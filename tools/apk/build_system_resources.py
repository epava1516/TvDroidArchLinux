#!/usr/bin/env python3
"""Build a scoped Android system resource APK from pinned original AOSP default values."""
import argparse
import copy
import hashlib
import json
from pathlib import Path
import re
import subprocess
import xml.etree.ElementTree as ET
import zipfile

parser = argparse.ArgumentParser()
for name in ('sources','reference','tools','output'):
    parser.add_argument('--'+name,type=Path,required=True)
args = parser.parse_args()
root = Path(__file__).resolve().parents[2]
manifest = json.loads((root/'runtime/aosp/framework-study.json').read_text())
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def original(name):
    path = args.sources/name
    entry = next(item for item in manifest['files'] if item['path']==name)
    assert path.stat().st_size==entry['bytes'] and sha(path)==entry['sha256'],name
    return path
reference = json.loads((root/'runtime/aosp/compile-reference.json').read_text())
assert sha(args.reference)==reference['sha256']
toolchain = json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())
aapt_entry = next(item for item in toolchain['artifacts'] if item['file']=='aapt2.jar')
assert sha(args.tools/'aapt2.jar')==aapt_entry['sha256']
consumer = original('core/java/android/view/ViewConfiguration.java')
keys = set(re.findall(r'com\.android\.internal\.R\.(bool|dimen|integer)\.(\w+)',consumer.read_text()))
assert len(keys)==18,'Review changed original ViewConfiguration resource surface'
inputs = [original(name) for name in manifest['system_resource_inputs']]
definitions = {}
for path in inputs:
    for item in ET.parse(path).getroot():
        key = (item.attrib.get('type',item.tag),item.attrib.get('name'))
        if key in keys:
            assert key not in definitions,'Duplicate default definition'
            assert len(item)==0 and not (item.text or '').strip().startswith(('@','?')),'Unresolved resource dependency'
            definitions[key]=(path,copy.deepcopy(item))
assert set(definitions)==keys,sorted(keys-set(definitions))
ids = {}
for kind in sorted({kind for kind,name in keys}):
    text = subprocess.check_output(['/usr/lib/jvm/java-17-openjdk/bin/javap','-constants','-classpath',str(args.reference),
        'com.android.internal.R$'+kind],text=True,timeout=30)
    fields = {name:int(value) for name,value in re.findall(r'public static final int (\w+) = (\d+);',text)}
    for key in sorted(keys):
        if key[0]==kind:
            value = fields[key[1]]
            assert value>>24==1
            ids[key]=value
assert len(set(ids.values()))==len(keys)
out = args.output.resolve();out.mkdir(parents=True,exist_ok=False)
(out/'res/values').mkdir(parents=True)
resources = ET.Element('resources')
for key in sorted(keys): resources.append(definitions[key][1])
ET.indent(resources)
(out/'res/values/system.xml').write_text('<?xml version="1.0" encoding="utf-8"?>\n<!-- Selected original AOSP defaults; input licenses: Apache-2.0. -->\n'+ET.tostring(resources,encoding='unicode')+'\n')
(out/'AndroidManifest.xml').write_text('<manifest package="android"/>\n')
(out/'stable-ids.txt').write_text(''.join('android:%s/%s = 0x%08x\n' % (*key,ids[key]) for key in sorted(keys)))
with zipfile.ZipFile(args.tools/'aapt2.jar') as archive: (out/'aapt2').write_bytes(archive.read('aapt2'))
(out/'aapt2').chmod(0o700)
commands = [
 [out/'aapt2','compile','--dir',out/'res','-o',out/'compiled.zip'],
 [out/'aapt2','link','-x','--stable-ids',out/'stable-ids.txt','--emit-ids',out/'emitted-ids.txt',
  '--manifest',out/'AndroidManifest.xml','-o',out/'framework-res.apk',out/'compiled.zip'],
 [out/'aapt2','dump','resources',out/'framework-res.apk']]
for i,command in enumerate(commands):
    with (out/('build-'+str(i)+'.stdout')).open('wb') as stdout,(out/('build-'+str(i)+'.stderr')).open('wb') as stderr:
        subprocess.run(list(map(str,command)),check=True,stdout=stdout,stderr=stderr,timeout=120)
emitted = (out/'emitted-ids.txt').read_text()
for key,value in ids.items():
    assert 'android:%s/%s = 0x%08x' % (*key,value) in emitted
with zipfile.ZipFile(out/'framework-res.apk') as archive:
    assert 'resources.arsc' in archive.namelist() and not any(name.endswith('.dex') for name in archive.namelist())
for path in inputs+[consumer]: original(str(path.relative_to(args.sources)))
assert sha(args.reference)==reference['sha256']
assert sha(args.tools/'aapt2.jar')==aapt_entry['sha256']
(out/'provenance.json').write_text(json.dumps({'revision':manifest['revision'],
 'original_inputs_sha256':{str(p.relative_to(args.sources)):sha(p) for p in inputs+[consumer]},
 'reference':reference,'aapt2':aapt_entry,'commands':[list(map(str,c)) for c in commands],
 'resources':[{'type':key[0],'name':key[1],'id':ids[key],'source':str(definitions[key][0].relative_to(args.sources)),
    'original_definition':ET.tostring(definitions[key][1],encoding='unicode').strip()} for key in sorted(keys)],
 'apk_sha256':sha(out/'framework-res.apk'),
 'scope':'Selected 18 original AOSP default resources used by ViewConfiguration, compiled as package android/0x01. Private IDs derive from the pinned compiler reference and are verified in emitted IDs. No copied reference bytecode, DEX, product overlay, full framework-res, themes or qualifier-complete compatibility claim.'},indent=2)+'\n')
print(out/'framework-res.apk')
