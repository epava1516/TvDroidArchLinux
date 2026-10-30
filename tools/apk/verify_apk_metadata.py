#!/usr/bin/env python3
"""Verify original ApplicationInfo and native AOSP manifest decoding in ART."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import subprocess
import zipfile

parser=argparse.ArgumentParser(description=__doc__)
for name in ('runtime-build','framework','linux-library','resources-library','art','tools','output'):
    parser.add_argument('--'+name,type=Path,required=True)
args=parser.parse_args();root=Path(__file__).resolve().parents[2]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
tools=args.tools.resolve();runtime=args.runtime_build.resolve();out=args.output.resolve()
proof=json.loads((runtime/'provenance.json').read_text())
assert sha(runtime/'dex/classes.dex')==proof['dex_sha256']
framework=args.framework.resolve()
assert sha(framework/'framework.jar')==proof['aosp_build']['framework_jar_sha256']
for item in json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())['artifacts']:
    if item['file'] in ('r8.jar','android.jar','aapt2'):assert sha(tools/item['file'])==item['sha256']
aapt_item=next(item for item in json.loads((root/'fixtures/apk/counter/toolchain.json').read_text())['artifacts'] if item['file']=='aapt2.jar')
assert sha(tools/'aapt2.jar')==aapt_item['sha256']
with zipfile.ZipFile(tools/'aapt2.jar') as bundle:
    assert hashlib.sha256(bundle.read('aapt2')).hexdigest()==sha(tools/'aapt2')
out.mkdir(parents=True,exist_ok=False)
for name in ('classes','dex'):(out/name).mkdir()
fixture=root/'fixtures/aosp-metadata';commands=[
    [str(tools/'aapt2'),'compile','--dir',str(fixture/'res'),'-o',str(out/'res.zip')],
    [str(tools/'aapt2'),'link','-I',str(tools/'android.jar'),'--manifest',str(fixture/'AndroidManifest.xml'),'-o',str(out/'metadata.apk'),str(out/'res.zip')],
    ['/usr/lib/jvm/java-17-openjdk/bin/javac','--release','8','-encoding','UTF-8','-classpath',str(runtime/'runtime.jar')+':'+str(framework/'framework.jar'),'-d',str(out/'classes'),str(fixture/'MetadataProbe.java')],
    ['/usr/lib/jvm/java-17-openjdk/bin/jar','cf',str(out/'probe.jar'),'-C',str(out/'classes'),'.'],
    ['/usr/lib/jvm/java-17-openjdk/bin/java','-cp',str(tools/'r8.jar'),'com.android.tools.r8.D8','--release','--min-api','28','--lib',str(tools/'android.jar'),'--output',str(out/'dex'),str(out/'probe.jar')],
]
for i,command in enumerate(commands):
    with (out/(str(i)+'.build.log')).open('w') as log:subprocess.run(command,check=True,stdout=log,stderr=subprocess.STDOUT,timeout=120)
bad=out/'invalid.apk'
counter=root/'fixtures/apk/counter/golden/counter.apk'
with zipfile.ZipFile(counter) as source,zipfile.ZipFile(bad,'w') as target:
    for item in source.infolist():target.writestr(item,b'not binary XML' if item.filename=='AndroidManifest.xml' else source.read(item))
newer=out/'newer-manifest.xml';newer.write_text((fixture/'AndroidManifest.xml').read_text().replace('minSdkVersion="21"','minSdkVersion="35"').replace('targetSdkVersion="27"','targetSdkVersion="35"'))
newer_command=[str(tools/'aapt2'),'link','-I',str(tools/'android.jar'),'--manifest',str(newer),'-o',str(out/'newer.apk'),str(out/'res.zip')]
with (out/'newer.build.log').open('w') as log:subprocess.run(newer_command,check=True,stdout=log,stderr=subprocess.STDOUT,timeout=60)
amplified=out/'amplified-manifest.xml'
attributes=' '.join('extra%d="%s"'%(i,'x'*150000) for i in range(20))
amplified.write_text((fixture/'AndroidManifest.xml').read_text().replace('<application ','<application '+attributes+' '))
amplified_command=[str(tools/'aapt2'),'link','-I',str(tools/'android.jar'),'--manifest',str(amplified),'-o',str(out/'amplified.apk'),str(out/'res.zip')]
with (out/'amplified.build.log').open('w') as log:subprocess.run(amplified_command,check=True,stdout=log,stderr=subprocess.STDOUT,timeout=60)
cases=[('counter',counter,'org.archtv.probe','28',None),('metadata',out/'metadata.apk','org.archtv.metadata','27',None),
       ('invalid',bad,'org.archtv.probe','28','Invalid APK binary XML'),
       ('newer',out/'newer.apk','org.archtv.metadata','35','newer platform SDK'),
       ('amplified',out/'amplified.apk','org.archtv.metadata','27','Manifest metadata output exceeds budget')]
results={}
for name,apk,package,sdk,error in cases:
    data=out/(name+'-data');data.mkdir(mode=0o700)
    art_data=out/(name+'-art');art_data.mkdir(mode=0o700)
    env={k:v for k,v in os.environ.items() if not k.startswith('ANDROID_') and k not in ('LD_PRELOAD','LD_LIBRARY_PATH','CLASSPATH')}
    env.update(ANDROID_DATA=str(art_data),ANDROID_LOG_TAGS='*:w')
    command=[str(args.art.resolve()/'bin/art'),'--64','--no-compile','--','-Xint','-Xcheck:jni','-cp',
             str(runtime/'dex/classes.dex')+':'+str(out/'dex/classes.dex'),'org.archtv.apkruntime.MetadataProbe',
             str(args.linux_library.resolve()),str(args.resources_library.resolve()),str(apk),str(data),package,sdk]
    run=subprocess.run(command,capture_output=True,text=True,env=env,timeout=30)
    (out/(name+'.stdout')).write_text(run.stdout);(out/(name+'.stderr')).write_text(run.stderr)
    passed=(run.returncode==0 and 'AOSP_APPLICATION_INFO_OK package='+package+' target='+sdk in run.stdout) if error is None else (run.returncode==1 and error in run.stderr)
    results[name]={'pass':passed,'exit_code':run.returncode,'command':command,'apk_sha256':sha(apk)}
passed=all(case['pass'] for case in results.values())
(out/'result.json').write_text(json.dumps({'application_info_pass':passed,'cases':results,'commands':commands+[newer_command,amplified_command],
    'runtime_dex_sha256':sha(runtime/'dex/classes.dex'),'resources_library_sha256':sha(args.resources_library),
    'probe_source_sha256':sha(fixture/'MetadataProbe.java'),'verifier_sha256':sha(Path(__file__)),
    'scope':'Original ApplicationInfo populated from original androidfw binary XML in two APKs, actual Linux UID/paths, literal flags and UTF-16 label. Malformed XML and excessive minimum SDK rejected. Not full PackageManager, signatures, split packages or general APK compatibility.'},indent=2)+'\n')
print(json.dumps({'application_info_pass':passed,'cases':{n:r['pass'] for n,r in results.items()}}))
if not passed:raise SystemExit(1)
