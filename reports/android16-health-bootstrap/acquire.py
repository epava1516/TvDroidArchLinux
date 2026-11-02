#!/usr/bin/env python3
"""Fetch pinned original health subsystem sources; no packages or runtime changes."""
from pathlib import Path
import hashlib,io,json,tarfile,urllib.request,xml.etree.ElementTree as ET
r=Path(__file__).resolve().parents[2];base=Path('/home/tv/.cache/archtv/aosp16-qpr2/health-original-study-1');base.mkdir(exist_ok=True)
manifest=ET.parse('/home/tv/.cache/archtv/aosp16-qpr2/manifest.lock.xml');pins={p.get('path'):p.get('revision') for p in manifest.findall('project')}
inputs=[('hardware/interfaces','aa229558cbf04bc997ed27465c5e7ad497123d1b','health','hardware-health'),('system/core','e9d1fa3705d7fbd0ac1c942bc4c276161bfbfed1','healthd','healthd'),('frameworks/native','fcbde2bcff56ca1d7bec9cabf8bdca5e288bf103','services/batteryservice','batteryservice'),('packages/modules/Connectivity','f930245ec39a510f37a9a7dfaded96d287491a61','bpf/syscall_wrappers','bpf-wrappers'),('packages/modules/Connectivity','f930245ec39a510f37a9a7dfaded96d287491a61','bpf/headers','bpf-headers')]
records=[]
for project,pin,sub,name in inputs:
 assert pins[project]==pin,(project,pins[project])
 url=f'https://android.googlesource.com/platform/{project}/+archive/{pin}/{sub}.tar.gz'
 blob=urllib.request.urlopen(url,timeout=30).read();assert len(blob)<10000000
 dest=base/name;dest.mkdir(exist_ok=True)
 with tarfile.open(fileobj=io.BytesIO(blob),mode='r:gz') as archive:
  members=[m for m in archive.getmembers() if m.isfile() or m.isdir()]
  skipped=[m.name for m in archive.getmembers() if not (m.isfile() or m.isdir())]
  archive.extractall(dest,members=members,filter='data')
 records.append(dict(project=project,pin=pin,url=url,path=str(dest),sha256=hashlib.sha256(blob).hexdigest(),skipped_nonregular=skipped))
 print(name,records[-1]['sha256'],flush=True)
(base/'complete-source-inputs.json').write_text(json.dumps(records,indent=2)+'\n')
