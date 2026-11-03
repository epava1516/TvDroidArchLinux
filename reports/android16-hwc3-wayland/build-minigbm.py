from pathlib import Path
import json,subprocess,hashlib,shutil,re,difflib,time,sys
r=Path('/home/tv/repositorio-principal');cache=Path('/home/tv/.cache/archtv/graphics-candidates-1');source=cache/'minigbm';out=r/'dist/aosp16'/('minigbm-native-4' if len(sys.argv)<2 else sys.argv[1]);out.mkdir();tree=out/'source';shutil.copytree(source,tree);rec={'scope':'Whole original minigbm core/common/AIDL allocator/stable-C mapper source modules, with explicit real vmwgfx dumb allocation profile; no runtime/BO/mapper/HWC/APK acceptance','commands':[],'sources':[]}
for row in json.loads((source/'allocator-source-inventory.json').read_text())['files']:assert hashlib.sha256((source/row['path']).read_bytes()).hexdigest()==row['sha256'],row['path']
patch=[]
for name in ['drv.c','dumb_driver.c']:
 p=tree/name;old=p.read_text();new=old
 if name=='drv.c':new=new.replace('extern const struct backend backend_vkms;','extern const struct backend backend_vkms;\nextern const struct backend backend_vmwgfx;').replace('&backend_vkms,','&backend_vmwgfx, &backend_vkms,')
 else:
  new=new.replace('#include <errno.h>','#include <errno.h>\n#include <xf86drm.h>')
  new+='''
/* Linux vmwgfx software allocation: real primary-node dumb BOs only.
 * No mock fallback, DRM master claim, GPU acceleration or protected-memory claim. */
static int vmwgfx_dumb_init(struct driver *drv)
{
    uint64_t available = 0;
    if (drmGetNodeTypeFromFd(drv->fd) != DRM_NODE_PRIMARY ||
        drmGetCap(drv->fd, DRM_CAP_DUMB_BUFFER, &available) != 0 || !available)
        return -ENOTSUP;
    return dumb_driver_init(drv);
}
const struct backend backend_vmwgfx = {
    .name = "vmwgfx",
    .init = vmwgfx_dumb_init,
    .bo_create = drv_dumb_bo_create,
    .bo_create_with_modifiers = dumb_bo_create_with_modifiers,
    .bo_destroy = drv_dumb_bo_destroy,
    .bo_import = drv_prime_bo_import,
    .bo_map = drv_dumb_bo_map,
    .bo_unmap = drv_bo_munmap,
    .resolve_format_and_use_flags = drv_resolve_format_and_use_flags_helper,
};
'''
 p.write_text(new);patch.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='a/'+name,tofile='b/'+name))
(out/'vmwgfx-dumb.patch').write_text(''.join(patch));rec['patch_sha256']=hashlib.sha256((out/'vmwgfx-dumb.patch').read_bytes()).hexdigest()
cpp=json.loads((r/'reports/android16-hwc3-frontend/build.json').read_text())['results'][0]['argv'];cpp=cpp[:cpp.index('-MMD')];c=next(row['argv'] for row in json.loads((r/'reports/android16-wayland-client/build.json').read_text())['commands'] if Path(row['argv'][0]).name=='clang-21');c=c[:c.index('-c')]+[arg for arg in cpp if arg.startswith('-I')]
heap=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/libdmabufheap-original')
heap_provenance=json.loads((heap/'provenance.json').read_text())
assert heap_provenance['status']=='complete' and heap_provenance['commit']=='2b9dbd3bcb16fdc0336bb18fddcca6f95badc237'
heap_headers=heap/heap_provenance['relative_source_root']/'include'
ion=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs/libion-original')
ion_provenance=json.loads((ion/'provenance.json').read_text())
assert ion_provenance['status']=='complete' and ion_provenance['commit']=='622d6495817e1468ed238c119fc0e0772e213000'
ion_headers=ion/ion_provenance['relative_source_root']/'kernel-headers'
assert (heap_headers/'BufferAllocator/BufferAllocator.h').is_file()
assert 'generic_cflags = ["-DHAS_DMABUF_SYSTEM_HEAP"]' in (tree/'Android.bp').read_text()
rec['original_generic_dma_heap']={'provenance':heap_provenance,'ion_provenance':ion_provenance,'headers':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for folder in (heap_headers,ion_headers) for p in sorted(folder.rglob('*.h'))},'android_bp_sha256':hashlib.sha256((tree/'Android.bp').read_bytes()).hexdigest(),'scope':'Original generic build option and complete heap interface; allocation/device/MAC require execution.'}
includes=['-I'+str(p) for p in [tree,heap_headers,ion_headers,cache/'libdrm',cache/'libdrm/include/drm',cache/'hardware-interfaces/graphics/mapper/stable-c/include',cache/'hardware-interfaces/graphics/mapper/stable-c/implutils/include',cache/'frameworks-native/libs/nativewindow/include']];defines=['-Wno-unused-parameter','-Wno-sign-compare','-DANDROID','-DANDROID_API_LEVEL=36','-D_FILE_OFFSET_BITS=64','-DHAS_DMABUF_SYSTEM_HEAP']
bp=(tree/'Android.bp').read_text();start=bp.index('name: "minigbm_core_files"');part=bp[start:];core=re.findall(r'"([^" ]+\.c)"',re.search(r'srcs: \[(.*?)\]',part,re.S)[1]);assert len(core)>=10
sources=[('core',tree/name) for name in core]+[('common',tree/'cros_gralloc'/name) for name in ['cros_gralloc_buffer.cc','cros_gralloc_driver.cc','cros_gralloc_helpers.cc']]+[('utils',tree/'cros_gralloc/gralloc4/CrosGralloc4Utils.cc'),('allocator',tree/'cros_gralloc/aidl/Allocator.cpp'),('allocator',tree/'cros_gralloc/aidl/Main.cpp'),('mapper',tree/'cros_gralloc/gralloc4/CrosGralloc4Mapper.cc'),('mapper',tree/'cros_gralloc/mapper_stablec/Mapper.cpp')]
for module,p in sources:
 obj=out/(module+'-'+p.stem+'.o');cmd=(c if p.suffix=='.c' else cpp)+includes+defines+['-MMD','-MF',str(obj.with_suffix('.d')),'-c',str(p),'-o',str(obj)];t=time.monotonic();x=subprocess.run(cmd,capture_output=True,text=True,timeout=150);rec['commands'].append({'argv':cmd,'exit':x.returncode,'seconds':time.monotonic()-t,'stderr':x.stderr});(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n');print(module,p.name,x.returncode,x.stderr[:1800],flush=True)
 if x.returncode:raise SystemExit(x.returncode)
 rec['sources'].append({'module':module,'source':str(p),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'object':str(obj),'object_sha256':hashlib.sha256(obj.read_bytes()).hexdigest()})
rec['terminal']=True;(out/'build.json').write_text(json.dumps(rec,indent=2)+'\n')
