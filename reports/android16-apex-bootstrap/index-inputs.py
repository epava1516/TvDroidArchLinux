#!/usr/bin/env python3
"""Inventory all original GSI APEX archives, including system_ext.

Expectations only: this never creates runtime apex-info-list.xml, activates a
module, or authenticates a signature. Original apexd must do those operations.
"""
from pathlib import Path
import ast,hashlib,json,sys,zipfile
repo=Path(__file__).resolve().parents[2]
output=Path(sys.argv[1]);assert not output.exists()
source=repo/'tools/aosp/prepare_factory_inputs.py'
tree=ast.parse(source.read_text())
functions=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ['varint','fields','manifest']]
assert len(functions)==3
import re
namespace={'re':re};exec(compile(ast.Module(body=functions,type_ignores=[]),str(source),'exec'),namespace)
root=repo/'dist/aosp16/factory-inputs-3/root'
modules=[];names=set()
for logical,folder in [('/system/apex',root/'system/apex'),('/system_ext/apex',root/'system/system_ext/apex'),('/product/apex',root/'system/product/apex')]:
    if not folder.exists():continue
    for archive in sorted(folder.iterdir()):
        assert archive.suffix in ['.apex','.capex']
        with zipfile.ZipFile(archive) as package:raw=package.read('apex_manifest.pb')
        m=namespace['manifest'](raw);assert m[1] not in names;names.add(m[1])
        modules.append({'name':m[1],'version':m[2],'archive':logical+'/'+archive.name,'archive_sha256':hashlib.file_digest(archive.open('rb'),'sha256').hexdigest(),'manifest_sha256':hashlib.sha256(raw).hexdigest()})
assert len(modules)==41,len(modules)
result={'scope':'Actual original archive identity expectations, not runtime inventory or signature/activation acceptance','parser_source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'modules':modules}
output.parent.mkdir(parents=True,exist_ok=True);output.write_text(json.dumps(result,indent=2)+'\n')
print('Original GSI module inputs',len(modules))
