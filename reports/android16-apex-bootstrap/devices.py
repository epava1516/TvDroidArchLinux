#!/usr/bin/env python3
"""Research-only Linux device boundary for original apexd, never a device emulator.

Kernel loop allocations and dm tables remain real/global. Only an idle loop
pool and dm names derived from the pinned APEX manifests enter the private dev.
The outer runner owns cleanup. This does not establish MAC isolation.
"""
from pathlib import Path
import argparse, ctypes, errno, fcntl, json, os, signal, stat, subprocess, time

REPO = Path('/home/tv/repositorio-principal')


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def prepare(root, out, data_store):
    modules = json.loads((REPO/'reports/android16-apex-bootstrap/complete-inputs.json').read_text())['modules']
    allowed = {m['name'] for m in modules}
    assert len(allowed) == 41
    # Persistent, disk-backed native cache; do not repeat nested loop-image I/O.
    data_store=data_store.resolve()
    assert data_store.parent==Path('/home/tv/.cache/archtv/aosp16-qpr2') and data_store.name.startswith('apex-data-store-')
    assert data_store.stat().st_uid==0 and (data_store/'linux-preparation.json').is_file()
    (root/'data/apex').mkdir()
    subprocess.run(['mount','--bind',str(data_store),str(root/'data/apex')],check=True)
    for logical,mode,uid,gid in [('data/misc_de',0o551,1000,9998),('data/system_de',0o550,1000,1000)]:
        p=root/logical;p.mkdir(mode=mode);os.chown(p,uid,gid)
    for name in ['metadata', 'metadata/apex', 'metadata/apex/sessions', 'metadata/apex/images', 'metadata/apex/config']:
        p=root/name; p.mkdir(mode=0o700); os.chown(p,0,1000)
    for directory in ['dev/block/mapper/by-uuid','sys/dev/block','sys/block','sys/class/block','sys/devices/virtual/block']:
        (root/directory).mkdir(parents=True,exist_ok=True)
    for host, logical in [('/dev/loop-control','loop-control'),('/dev/mapper/control','device-mapper'),('/dev/kmsg','kmsg')]:
        info=os.stat(host); assert stat.S_ISCHR(info.st_mode)
        os.mknod(root/'dev'/logical,stat.S_IFCHR|0o600,info.st_rdev)
    paths=sorted(Path('/sys/devices/virtual/block').glob('loop*'),key=lambda p:int(p.name[4:]))
    idle=[]; occupied=[]
    for p in paths:
        backing=p/'loop/backing_file'
        if backing.exists() and backing.read_text().strip():
            value=backing.read_text().strip()
            assert '/home/tv/repositorio-principal/dist/aosp16/' in value or value=='/home/tv/.cache/archtv/aosp16-qpr2/artifact-selection/gsi-original/system.img',value
            occupied.append(int(p.name[4:]))
        else: idle.append(int(p.name[4:]))
    created=[]; next_id=max([int(p.name[4:]) for p in paths],default=-1)+1
    state={'allowed_dm_names':sorted(allowed),'loop_pool':[],'created_loop_ids':created,'occupied_factory_loops':occupied,'dm_nodes':[],'scope':'Real Linux devices; trusted diagnostic only, not MAC or APK acceptance'}
    save(out/'devices.json',state)
    ctl=os.open('/dev/loop-control',os.O_RDWR|os.O_CLOEXEC)
    try:
        while len(idle)<2*len(allowed)+8:
            fcntl.ioctl(ctl,0x4c80,next_id)  # real LOOP_CTL_ADD, never fake GET_FREE
            created.append(next_id);idle.append(next_id);next_id+=1
            save(out/'devices.json',state)
    finally: os.close(ctl)
    pool=idle[:2*len(allowed)+8]
    for number in pool:
        p=Path('/sys/devices/virtual/block')/f'loop{number}'
        major,minor=map(int,(p/'dev').read_text().split(':'))
        os.mknod(root/'dev/block'/p.name,stat.S_IFBLK|0o600,os.makedev(major,minor))
    # Real kernel links/metadata are copied, not invented block-device answers.
    for number in occupied+pool:
        expose_links(root,Path('/sys/devices/virtual/block')/f'loop{number}')
    state['loop_pool']=pool
    save(out/'devices.json',state)
    return state


def mount_sysfs(root):
    # Do this after scaffold labeling: never relabel the real host sysfs.
    subprocess.run(['mount','--bind','/sys/devices/virtual/block',str(root/'sys/devices/virtual/block')],check=True)
    subprocess.run(['mount','-o','remount,bind,ro',str(root/'sys/devices/virtual/block')],check=True)


def enable_loop_controls(root,out):
    state=json.loads((out/'devices.json').read_text());changes=[]
    # Every slot was idle when reserved, but bootstrap may temporarily use it.
    # Keep its control available when apexd releases and reuses that slot.
    # The rest of sysfs
    # stays read-only; no host disk, scheduler or general queue write access.
    for number in state['loop_pool']:
        kernel=Path('/sys/devices/virtual/block')/f'loop{number}'
        source=kernel/'queue/read_ahead_kb';target=root/'sys/devices/virtual/block'/kernel.name/'queue/read_ahead_kb'
        previous=source.read_text().strip()
        subprocess.run(['mount','--bind',str(source),str(target)],check=True)
        subprocess.run(['mount','-o','remount,bind,rw',str(target)],check=True)
        changes.append({'id':number,'previous':previous,'attribute':'queue/read_ahead_kb'})
    state['loop_controls']=changes;save(out/'devices.json',state)


def expose_links(root, kernel):
    major,minor=map(int,(kernel/'dev').read_text().split(':'))
    for source,dest in [(Path('/sys/dev/block')/f'{major}:{minor}',root/'sys/dev/block'/f'{major}:{minor}'),(Path('/sys/block')/kernel.name,root/'sys/block'/kernel.name),(Path('/sys/class/block')/kernel.name,root/'sys/class/block'/kernel.name)]:
        target=os.readlink(source)
        if not dest.is_symlink():dest.symlink_to(target)
        else:assert os.readlink(dest)==target


def monitor(root,out,parent):
    libc=ctypes.CDLL(None,use_errno=True)
    assert libc.prctl(1,signal.SIGTERM,0,0,0)==0  # owned parent's death stops monitor
    assert libc.prctl(38,1,0,0,0)==0  # NNP also applies to this trusted Linux observer
    assert os.getppid()==parent
    state=json.loads((out/'devices.json').read_text());allowed=set(state['allowed_dm_names']);seen=set();live={}
    lib=ctypes.CDLL(str(REPO/'dist/aosp16/linux-selinux-handoff-2/libselinux-3.11/src/libselinux.so.1'),use_errno=True)
    class Opt(ctypes.Structure):_fields_=[('type',ctypes.c_int),('value',ctypes.c_char_p)]
    lib.selabel_open.argtypes=[ctypes.c_uint,ctypes.POINTER(Opt),ctypes.c_uint];lib.selabel_open.restype=ctypes.c_void_p
    lib.selabel_lookup_raw.argtypes=[ctypes.c_void_p,ctypes.POINTER(ctypes.c_char_p),ctypes.c_char_p,ctypes.c_int]
    lib.lsetfilecon_raw.argtypes=[ctypes.c_char_p,ctypes.c_char_p];lib.freecon.argtypes=[ctypes.c_void_p]
    opt=Opt(3,str(root/'system/etc/selinux/plat_file_contexts').encode());handle=lib.selabel_open(0,ctypes.byref(opt),1);assert handle
    stopping=False;bpf_captured=False
    network=None
    if (out/'network-boundary.json').exists():
        import importlib.util
        spec=importlib.util.spec_from_file_location('network_boundary',REPO/'reports/android16-network-bootstrap/boundary.py')
        network=importlib.util.module_from_spec(spec);spec.loader.exec_module(network)
        def stop_monitor(signum,frame):
            nonlocal stopping
            stopping=True
        signal.signal(signal.SIGTERM,stop_monitor)
    network_peers={}
    end=time.monotonic()+200
    while time.monotonic()<end and not stopping:
        if network is not None:
            for proc in Path('/proc').iterdir():
                if not proc.name.isdigit():continue
                try:
                    comm=(proc/'comm').read_text().strip()
                    if comm not in {'netbpfload','archtv-platform','netd'}:continue
                    started=(proc/'stat').read_text().rsplit(')',1)[1].split()[19]
                    key=proc.name+':'+started
                    if key in network_peers:continue
                    fields=dict(l.split(':',1) for l in (proc/'status').read_text().splitlines() if ':' in l)
                    peer={'pid':int(proc.name),'start_ticks':started,'comm':comm,'executable':os.readlink(proc/'exe'),'context':(proc/'attr/current').read_text().strip().rstrip('\0')}
                    peer.update({n:fields[n].strip() for n in ['Uid','Gid','Groups','CapInh','CapPrm','CapEff','CapBnd','CapAmb','NoNewPrivs']})
                    network_peers[key]=peer;save(out/'network-identities.json',list(network_peers.values()))
                except (OSError,ProcessLookupError):continue
        if network is not None and not bpf_captured and (root/'sys/fs/bpf/netd_shared/mainline_done').is_dir():
            network.snapshot(root,out,'mainline-done');bpf_captured=True
        for uuid,(kernel_name,name) in list(live.items()):
            kernel=Path('/sys/devices/virtual/block')/kernel_name
            try: present=(kernel/'dm/uuid').read_text().strip()==uuid
            except OSError as error:
                if error.errno not in (errno.ENOENT,errno.ENODEV,errno.EINVAL):raise
                present=False
            if not present:
                target=root/'sys/devices/virtual/block'/kernel_name/'queue/read_ahead_kb'
                mounts={row.split()[4] for row in Path('/proc/self/mountinfo').read_text().splitlines()}
                if str(target) in mounts:
                    removed=subprocess.run(['umount',str(target)],capture_output=True,text=True)
                    if removed.returncode:
                        # Device removal can detach its sysfs mount between
                        # observation and umount. Only accept actual absence.
                        remaining={row.split()[4] for row in Path('/proc/self/mountinfo').read_text().splitlines()}
                        if str(target) in remaining:raise RuntimeError(removed.stderr)
                state.setdefault('dm_control_removals',[]).append({'path':str(target),'mount_absent':True})
                save(out/'devices.json',state)
                unique=root/'dev/block/mapper/by-uuid'/uuid
                if unique.is_symlink() and os.readlink(unique)=='../../'+kernel_name:unique.unlink()
                seen.discard((kernel_name,name,uuid));del live[uuid]
        for p in Path('/sys/devices/virtual/block').glob('dm-*'):
            try:
                name=(p/'dm/name').read_text().strip()
                if name not in allowed:continue
                uuid=(p/'dm/uuid').read_text().strip()
                key=(p.name,name,uuid)
                if key in seen:continue
                if not uuid:continue
                assert '/' not in uuid and len(uuid)<129
                major,minor=map(int,(p/'dev').read_text().split(':'));node=root/'dev/block'/p.name
                if node.exists():
                    info=node.stat();assert stat.S_ISBLK(info.st_mode) and info.st_rdev==os.makedev(major,minor)
                else:os.mknod(node,stat.S_IFBLK|0o600,os.makedev(major,minor))
                logical=('/dev/block/'+p.name).encode();context=ctypes.c_char_p()
                assert lib.selabel_lookup_raw(handle,ctypes.byref(context),logical,stat.S_IFBLK|0o600)==0
                assert lib.lsetfilecon_raw(str(node).encode(),context)==0;lib.freecon(context)
                expose_links(root,p)
                # Publish the real writable leaf BEFORE the libdm UUID link.
                source=p/'queue/read_ahead_kb'
                target=root/'sys/devices/virtual/block'/p.name/'queue/read_ahead_kb'
                subprocess.run(['mount','--bind',str(source),str(target)],check=True)
                subprocess.run(['mount','-o','remount,bind,rw',str(target)],check=True)
                unique=root/'dev/block/mapper/by-uuid'/uuid
                if not unique.is_symlink():unique.symlink_to('../../'+p.name)
                else:assert os.readlink(unique)=='../../'+p.name
                context=ctypes.c_char_p()
                assert lib.selabel_lookup_raw(handle,ctypes.byref(context),('/dev/block/mapper/by-uuid/'+uuid).encode(),stat.S_IFLNK|0o777)==0
                assert lib.lsetfilecon_raw(str(unique).encode(),context)==0;lib.freecon(context)
                seen.add(key);live[uuid]=(p.name,name)
                state['dm_nodes'].append({'name':name,'kernel_name':p.name,'uuid':uuid,'major':major,'minor':minor,'label':os.getxattr(node,'security.selinux').decode().rstrip('\0')})
                save(out/'devices.json',state)
            except OSError as error:
                if error.errno not in (errno.ENOENT,errno.ENODEV,errno.EINVAL):raise
                continue  # real kernel creation/removal raced sysfs reads
        time.sleep(.02)  # native device-event bridge, no model polling
    if network is not None:network.snapshot(root,out,'monitor-close')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);parser.add_argument('output',type=Path);parser.add_argument('parent',type=int);args=parser.parse_args();monitor(args.root,args.output,args.parent)
