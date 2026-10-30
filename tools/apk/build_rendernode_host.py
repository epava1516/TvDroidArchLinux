#!/usr/bin/env python3
"""Build original HWUI host units and link the source-verified RenderNode JNI profile."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ('sources','androidfw-sources','androidfw-build','skia-build','aosp-cache','art','output'):
        parser.add_argument('--'+name,type=Path,required=True)
    parser.add_argument('--resume',action='store_true')
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    sources, cache = args.sources.resolve(), args.androidfw_sources.resolve()
    skia, native, art = args.skia_build.resolve(), args.androidfw_build.resolve(), args.art.resolve()
    manifests = {}
    for name, directory in [('hwui',sources),('androidfw',cache),('skia-extra',sources/'skia/third_party/externals'),
                            ('hwui-host',sources)]:
        path = root/'runtime/aosp'/(name+'-sources.json')
        manifest = json.loads(path.read_text())
        manifests[name] = sha(path)
        for component in manifest['components']:
            for filename, expected in component['files'].items():
                p = directory/component['name']/filename
                if not p.is_file() or sha(p)!=expected['sha256']:
                    raise SystemExit('Original source mismatch: '+str(p))
    subprocess.run(['python',str(root/'tools/apk/generate_rendernode_jni.py'),'--sources',str(sources),
                    '--aosp-cache',str(args.aosp_cache.resolve()),'--output',str(root/'runtime/aosp/native/rendernode-jni.cpp'),'--check'],check=True)
    sproof = json.loads((skia/'result.json').read_text())
    nproof = json.loads((native/'provenance.json').read_text())
    if not sproof['build_pass'] or any(manifests.get(name)!=value
                                      for name,value in sproof['configuration']['manifests'].items()):
        raise SystemExit('Skia build/source provenance mismatch')
    recipe = json.loads((root/'runtime/aosp/androidfw-build.json').read_text())
    if nproof['source_manifest']!=json.loads((root/'runtime/aosp/androidfw-sources.json').read_text()) or nproof['recipe']!=recipe:
        raise SystemExit('Native archive source/recipe mismatch')
    archives = []
    for build, proof in [(skia,sproof),(native,nproof)]:
        for name, expected in proof['archives'].items():
            path = build/name
            if sha(path)!=expected:
                raise SystemExit('Dependency archive modified: '+str(path))
            archives.append(path)
    libcxx = art/'lib64/libc++.so'
    if sha(libcxx)!=nproof['libcxx_runtime_sha256']:
        raise SystemExit('ART libc++ mismatch')
    bp = (sources/'hwui/Android.bp').read_text()
    block = bp[bp.index('name: "libhwui_defaults"'):]
    units = re.findall(r'"([^"]+\.cpp)"',re.search(r'\bsrcs:\s*\[(.*?)\]',block,re.S)[1])
    units += ['utils/HostColorSpace.cpp']
    if len(units)!=len(set(units)) or not units:
        raise SystemExit('Invalid original host unit set')
    original_files = next(c['files'] for c in json.loads((root/'runtime/aosp/hwui-sources.json').read_text())['components'] if c['name']=='hwui')
    if any(name not in original_files for name in units):
        raise SystemExit('Host unit not pinned')
    minikin_bp = (sources/'minikin/libs/minikin/Android.bp').read_text()
    minikin_block = minikin_bp[minikin_bp.index('name: "libminikin"'):]
    minikin_units = re.findall(r'"([^"]+\.cpp)"',re.search(r'\bsrcs:\s*\[(.*?)\]',minikin_block,re.S)[1])
    minikin_files = next(c['files'] for c in json.loads((root/'runtime/aosp/hwui-sources.json').read_text())['components'] if c['name']=='minikin')
    if not minikin_units or len(minikin_units)!=len(set(minikin_units)) or any('libs/minikin/'+p not in minikin_files for p in minikin_units):
        raise SystemExit('Minikin unit not pinned')
    include = [cache/p for p in recipe['includes']]
    include += [sources/p for p in ['hwui','hwui/jni','skia','skia/linux','skia/src/codec','skia/src/core',
                'skia/src/effects','skia/src/image','skia/src/images','skia/client_utils/android',
                'nativehelper/include','nativehelper/include_jni','nativehelper/include_platform',
                'nativehelper/header_only_include','minikin/include','harfbuzz','ui-headers','gui-headers','vulkan-headers',
                'ui-types','math-headers']]
    include += sorted(p for p in (sources/'skia/include').iterdir() if p.is_dir())
    include += [root/'runtime/aosp/native',skia/'host-headers']
    atomic_header = skia/'host-headers/stdatomic.h'
    if sha(atomic_header)!=sproof['configuration']['original_bionic_stdatomic_sha256']:
        raise SystemExit('Exported original atomic header modified')
    own = [root/'runtime/aosp/native'/name for name in ['rendernode-jni.cpp','critical-host-adapter.h','skcms-clang-compat.h']]
    flags = ['clang++','-std=gnu++20','-nostdinc++','-isystem',str(cache/'libcxx'),'-fPIC','-O1','-g0',
             '-fvisibility=hidden','-fno-rtti','-ffunction-sections','-fdata-sections','-DSTATIC_ANDROIDFW_FOR_TOOLS',
             '-DFMT_HEADER_ONLY','-DNDEBUG','-include',str(own[2]),*['-I'+str(p) for p in include]]
    identity = {'manifests':manifests,'own_sources_sha256':{str(p):sha(p) for p in own},
                'compiler':subprocess.check_output(['clang++','--version'],text=True),
                'system_packages':subprocess.check_output(['pacman','-Q','harfbuzz','harfbuzz-icu','icu',
                                    'freetype2','libpng','libjpeg-turbo','libwebp','zlib','expat'],text=True),
                'skia_provenance_sha256':sha(skia/'result.json'),'native_provenance_sha256':sha(native/'provenance.json'),
                'libcxx_sha256':sha(libcxx),'original_bionic_stdatomic_sha256':sha(atomic_header)}
    fingerprint = hashlib.sha256(json.dumps(identity,sort_keys=True).encode()).hexdigest()
    out = args.output.resolve()
    out.mkdir(parents=True,exist_ok=args.resume)
    (out/'objects').mkdir(exist_ok=args.resume)
    (out/'logs').mkdir(exist_ok=args.resume)
    commands, objects = [], []
    sources_to_compile = [(name,sources/'hwui'/name) for name in units]
    sources_to_compile += [('minikin/'+name,sources/'minikin/libs/minikin'/name) for name in minikin_units]
    sources_to_compile += [('rendernode-jni',own[0])]
    failed = None
    for name, source in sources_to_compile:
        key = name.replace('/','-')
        target = out/'objects'/(key+'.o')
        command = [*flags,'-c',str(source),'-o',str(target)]
        commands.append(command)
        state = target.with_suffix('.json')
        stamp = hashlib.sha256((fingerprint+json.dumps(command)).encode()).hexdigest()
        saved = json.loads(state.read_text()) if args.resume and state.exists() else {}
        if not (saved.get('stamp')==stamp and target.exists() and sha(target)==saved.get('sha256')):
            print('Compiling '+name,flush=True)
            with (out/'logs'/(key+'.log')).open('w') as log:
                run = subprocess.run(command,stdout=log,stderr=subprocess.STDOUT,timeout=180)
            if run.returncode:
                failed = {'unit':name,'exit_code':run.returncode}
                break
            state.write_text(json.dumps({'stamp':stamp,'sha256':sha(target)})+'\n')
        objects.append(target)
    link = []
    library = out/'libarchtv_rendernode_host.so'
    if failed is None:
        link = ['clang++','-shared','-nostdlib++','-Wl,--gc-sections','-Wl,--no-undefined','-Wl,--exclude-libs,ALL',
                '-L'+str(libcxx.parent),'-Wl,-rpath,'+str(libcxx.parent),*map(str,objects),'-Wl,--start-group',
                *map(str,archives),'-Wl,--end-group','-lc++','-lz','-ldl','-lpthread','-lm','-lpng','-ljpeg',
                '-lwebp','-lwebpmux','-lwebpdemux','-lexpat','-lfreetype','-lharfbuzz','-lharfbuzz-subset','-lharfbuzz-icu',
                '-licuuc','-licui18n','-licudata','-o',str(library)]
        with (out/'link.log').open('w') as log:
            run = subprocess.run(link,stdout=log,stderr=subprocess.STDOUT,timeout=120)
        if run.returncode:
            failed = {'stage':'link','exit_code':run.returncode}
    proof = {'build_pass':failed is None,'failure':failed,'identity':identity,'original_units':units,
             'original_minikin_units':minikin_units,
             'objects':{p.name:sha(p) for p in objects},'commands':commands,'link_command':link,
             'builder_sha256':sha(Path(__file__)),
             'scope':'Original HWUI host common units plus 16-entry RenderNode JNI profile. No ART execution or drawing claim.'}
    if failed is None:
        proof['library_sha256'] = sha(library)
    (out/'result.json').write_text(json.dumps(proof,indent=2)+'\n')
    print(json.dumps({'build_pass':proof['build_pass'],'failure':failed}),flush=True)
    return 0 if failed is None else 1


if __name__=='__main__':
    raise SystemExit(main())
