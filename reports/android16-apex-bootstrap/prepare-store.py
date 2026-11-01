#!/usr/bin/env python3
"""Prepare an original APEX decompression cache; apexd must still validate it.

No XML inventory, properties, signatures, verity results or service answers are
created here. Every seeded file equals original_apex inside the pinned CAPEX.
"""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,zipfile
repo=Path(__file__).resolve().parents[2];target=Path(sys.argv[1]).resolve();native_image=Path(sys.argv[2]).resolve()
assert os.geteuid()==0 and target.parent==Path('/home/tv/.cache/archtv/aosp16-qpr2') and target.name.startswith('apex-data-store-')
stage=target.with_name(target.name+'.staging');assert not target.exists() and not stage.exists()
stage.mkdir(mode=0o755);os.chown(stage,0,1000)
result=subprocess.run(['debugfs','-R','rdump / '+str(stage),str(native_image)],capture_output=True,text=True,timeout=90)
assert result.returncode==0,result.stderr
modules=json.loads((repo/'reports/android16-apex-bootstrap/complete-inputs.json').read_text())['modules']
root=repo/'dist/aosp16/factory-inputs-3/root';records=[]
for module in modules:
    if not module['archive'].endswith('.capex'):continue
    archive=root/module['archive'].lstrip('/')
    assert archive.is_file(),archive
    assert hashlib.file_digest(archive.open('rb'),'sha256').hexdigest()==module['archive_sha256']
    source=repo/'dist/aosp16/factory-inputs-3'/(archive.stem+'.original.apex');assert source.is_file()
    digest=hashlib.file_digest(source.open('rb'),'sha256').hexdigest()
    with zipfile.ZipFile(archive) as package:
        with package.open('original_apex') as stream:expected=hashlib.file_digest(stream,'sha256').hexdigest()
    assert digest==expected,source
    filename=f"{module['name']}@{module['version']}.decompressed.apex"
    dest=stage/'decompressed'/filename;reused=False
    if dest.exists():
        if hashlib.file_digest(dest.open('rb'),'sha256').hexdigest()==digest:reused=True
        else:dest.rename(dest.with_suffix('.native-partial-preserved'))
    if not reused:
        temp=dest.with_suffix('.copying')
        with source.open('rb') as inp,temp.open('xb') as out:
            shutil.copyfileobj(inp,out,1024*1024);out.flush();os.fsync(out.fileno())
        temp.chmod(0o644);os.chown(temp,0,1000);temp.rename(dest)
    records.append({'module':module['name'],'version':module['version'],'sha256':digest,'reused_native_output':reused,'source':'Unmodified original_apex ZIP entry; not signature or activation acceptance'})
manifest={'scope':'Linux cache preparation only. Original apexd must revalidate every cached file and publish/mount actual modules. No FBE/MAC/update acceptance.','native_source_image':str(native_image),'seeded':records,'expected_modules':len(modules)}
(stage/'linux-preparation.json').write_text(json.dumps(manifest,indent=2)+'\n')
stage.rename(target)
print('Prepared original cache',len(records),'CAPEX entries; runtime inventory still unproven',flush=True)
