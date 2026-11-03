#!/usr/bin/env python3
"""Research-only Linux device boundary for original apexd, never a device emulator.

Kernel loop allocations and dm tables remain real/global. Only an idle loop
pool and dm names derived from the pinned APEX manifests enter the private dev.
The outer runner owns cleanup. This does not establish MAC isolation.
"""
from pathlib import Path
import argparse, ctypes, errno, fcntl, json, os, re, signal, stat, subprocess, time

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
    (root/'data/apex').mkdir(exist_ok=True)
    subprocess.run(['mount','--bind',str(data_store),str(root/'data/apex')],check=True)
    for logical,mode,uid,gid in [('data/misc_de',0o551,1000,9998),('data/system_de',0o550,1000,1000)]:
        p=root/logical;p.mkdir(mode=mode,exist_ok=True);os.chown(p,uid,gid)
    # Original init.rc environ scaffold for the original derive service.
    # These are directories only, never service inventory or readiness files.
    for logical,mode,uid,gid in [('data/system',0o775,1000,1000),('data/system/environ',0o700,1000,1000)]:
        p=root/logical;p.mkdir(parents=True,mode=mode,exist_ok=True);os.chmod(p,mode);os.chown(p,uid,gid)
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
    # Fixed experimental private RW pool. Original sysfs_loop labels are
    # broader globally; this is not label exclusivity. Reject changed allocation
    # before exposing a control; never borrow foreign loops.
    assert pool==list(range(2,92)), ('Reserved loop policy/profile mismatch',pool)
    state['loop_policy_profile']={'first':2,'last':91,'scope':'Exact private RW control pool and actual original labels; not exclusive global mappings'}
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
    assert state['loop_pool']==list(range(2,92)), 'Refuse unlabelled loop controls'
    # Every slot was idle when reserved, but bootstrap may temporarily use it.
    # Keep its control available when apexd releases and reuses that slot.
    # The rest of sysfs
    # stays read-only; no host disk, scheduler or general queue write access.
    for number in state['loop_pool']:
        kernel=Path('/sys/devices/virtual/block')/f'loop{number}'
        source=kernel/'queue/read_ahead_kb';target=root/'sys/devices/virtual/block'/kernel.name/'queue/read_ahead_kb'
        previous=source.read_text().strip()
        control_label=os.getxattr(source,'security.selinux').decode().rstrip(chr(0))
        assert control_label=='u:object_r:sysfs_loop:s0', ('Reserved control label mismatch',str(source),control_label)
        subprocess.run(['mount','--bind',str(source),str(target)],check=True)
        subprocess.run(['mount','-o','remount,bind,rw',str(target)],check=True)
        changes.append({'id':number,'previous':previous,'attribute':'queue/read_ahead_kb','actual_selinux_label':control_label})
    # Check the actual private mount boundary without writing a value. This
    # Linux-coordinator VFS negative is not an Android MAC/isolation test.
    denied=[]
    for number in [0,1]:
        other=root/'sys/devices/virtual/block'/f'loop{number}'/'queue/read_ahead_kb'
        assert other.is_file(), ('Missing negative control',str(other))
        try: fd=os.open(other,os.O_WRONLY|os.O_CLOEXEC)
        except OSError as error:
            assert error.errno==errno.EROFS, ('Expected real EROFS',str(other),error)
            denied.append({'id':number,'errno':error.errno})
        else:
            os.close(fd);raise AssertionError('Outside-pool control writable: '+str(other))
    state['loop_readonly_vfs_negative']={'observed':denied,'scope':'Trusted Linux coordinator open only, no write; not Android MAC or remount resistance'}
    state['loop_controls']=changes;save(out/'devices.json',state)


def expose_links(root, kernel):
    major,minor=map(int,(kernel/'dev').read_text().split(':'))
    for source,dest in [(Path('/sys/dev/block')/f'{major}:{minor}',root/'sys/dev/block'/f'{major}:{minor}'),(Path('/sys/block')/kernel.name,root/'sys/block'/kernel.name),(Path('/sys/class/block')/kernel.name,root/'sys/class/block'/kernel.name)]:
        target=os.readlink(source)
        if not dest.is_symlink():dest.symlink_to(target)
        else:assert os.readlink(dest)==target


def owned_process(proc, owner_cgroup, namespaces):
    if any((proc/'ns'/name).stat().st_ino!=inode for name,inode in namespaces.items()):
        return False
    line=(proc/'cgroup').read_text().strip()
    if not line.startswith('0::'):return False
    path=line[3:]
    if not path.startswith('/') or '..' in path.split('/'):return False
    return owner_cgroup=='/' or path==owner_cgroup or path.startswith(owner_cgroup.rstrip('/')+'/')


def observe_app_startups(log, state, out, owner_cgroup, namespaces, procbase):
    """Bounded, read-only diagnostic for actual original AMS child-start events.

    No ptrace, signals, heap dumps, app changes or model notifications. PID/start
    time and cgroup checks prevent observing a reused or unrelated process.
    """
    changed=False
    for _ in range(64):
        line=log.readline()
        if not line:break
        try:item=json.loads(line)
        except json.JSONDecodeError:continue
        if item.get('tag')!='ActivityManager':continue
        match=re.match(r'Start proc (\d+):([^/]+)/',item.get('message',''))
        if not match or match[2] not in {'com.android.permissioncontroller','com.android.settings','net.gsantner.markor'}:continue
        sender=item.get('actual_sender_pid_uid_gid',[])
        if len(sender)!=3 or sender[1]!=1000:continue
        try:
            source=procbase/str(sender[0])
            if (source/'attr/current').read_text().strip().rstrip('\0')!='u:r:system_server:s0':continue
            if not owned_process(source,owner_cgroup,namespaces):continue
        except OSError:continue
        if len(state['processes'])>=6:
            state['truncated']=True;changed=True;continue
        proc=procbase/match[1]
        event={'pid':int(match[1]),'package':match[2],'event':item,'seen_monotonic':time.monotonic(),'samples':[]}
        try:
            event['start_ticks']=(proc/'stat').read_text().rsplit(')',1)[1].split()[19]
            event['initial_cgroup']=(proc/'cgroup').read_text().strip()
            if not owned_process(proc,owner_cgroup,namespaces):continue
        except OSError as error:event['early_exit_or_read_error']=str(error)
        state['processes'].append(event);changed=True
    for event in state['processes']:
        if 'start_ticks' not in event:continue
        age=time.monotonic()-event['seen_monotonic']
        for delay in [2,7]:
            if age<delay or any(x['delay_requested']==delay for x in event['samples']):continue
            sample={'delay_requested':delay,'age_seconds':age,'observed_monotonic':time.monotonic()}
            proc=procbase/str(event['pid'])
            try:
                ticks=(proc/'stat').read_text().rsplit(')',1)[1].split()[19]
                if ticks!=event['start_ticks']:raise RuntimeError('PID reused; observation refused')
                cgroup=(proc/'cgroup').read_text().strip()
                if not owned_process(proc,owner_cgroup,namespaces):raise RuntimeError('PID outside owned namespaces/cgroup; observation refused')
                sample['cgroup']=cgroup
                sample['context']=(proc/'attr/current').read_text().strip().rstrip('\0')
                sample['cmdline']=(proc/'cmdline').read_bytes()[:4096].replace(b'\0',b' ').decode(errors='replace')
                sample['status']=[x for x in (proc/'status').read_text().splitlines() if x.startswith(('Name:','State:','Uid:','Gid:','Groups:','Cap','NoNewPrivs:','Seccomp:','Threads:','NSpid:','VmRSS:'))]
                sample['tasks']=[]
                for task in sorted((proc/'task').iterdir(),key=lambda x:int(x.name))[:12]:
                    entry={'tid':int(task.name)}
                    for name in ['comm','wchan','stack','syscall']:
                        try:entry[name]=(task/name).read_text()[:8192]
                        except OSError as error:entry[name+'_error']=str(error)
                    sample['tasks'].append(entry)
                sample['fds']={}
                for fd in sorted((proc/'fd').iterdir(),key=lambda x:int(x.name))[:32]:
                    try:sample['fds'][fd.name]=os.readlink(fd)
                    except OSError as error:sample['fds'][fd.name]=str(error)
                sample['maps_prefix']=(proc/'maps').read_text().splitlines()[:128]
                if (proc/'stat').read_text().rsplit(')',1)[1].split()[19]!=ticks:raise RuntimeError('Process identity changed during observation')
            except (OSError,RuntimeError) as error:sample['error']=str(error)
            event['samples'].append(sample);changed=True
    if changed:save(out/'app-start-observations.json',state)


def monitor(root,out,parent):
    libc=ctypes.CDLL(None,use_errno=True)
    assert libc.prctl(1,signal.SIGTERM,0,0,0)==0  # owned parent's death stops monitor
    assert libc.prctl(38,1,0,0,0)==0  # NNP also applies to this trusted Linux observer
    assert os.getppid()==parent
    libc.mount.argtypes=[ctypes.c_char_p,ctypes.c_char_p,ctypes.c_char_p,ctypes.c_ulong,ctypes.c_void_p]
    libc.mount.restype=ctypes.c_int
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
    app_log=(out/'android-log-live.jsonl').open()
    app_state={'scope':'Read-only native app-start diagnosis; not app availability/security acceptance','processes':[],'truncated':False}
    # The monitor retains the Linux mount namespace. Numeric SCM/AMS PIDs
    # belong to the cohort PID namespace, whose procfs is mounted in root/proc.
    procbase=root/'proc'
    assert int((procbase/'self/stat').read_text().split(' ',1)[0])==os.getpid(), 'procfs must expose cohort PID namespace'
    assert (procbase/str(os.getpid())/'ns/pid').stat().st_ino==(procbase/'self/ns/pid').stat().st_ino
    own=((procbase/'self/cgroup').read_text().strip().split('0::',1)[1])
    owner_cgroup=own.split('.service',1)[0]+'.service' if '.service' in own else own
    namespaces={name:(procbase/'self/ns'/name).stat().st_ino for name in ['pid','cgroup']}
    app_state['owner_cgroup']=owner_cgroup;app_state['owner_namespaces']=namespaces
    app_state['procfs']=str(procbase)
    save(out/'app-start-observations.json',app_state)
    end=time.monotonic()+400
    while time.monotonic()<end and not stopping:
        observe_app_startups(app_log,app_state,out,owner_cgroup,namespaces,procbase)
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
                observed=time.monotonic()
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
                # Same real bind/remount operations, without two fork/execs per
                # concurrent DM device before its original libdm UUID deadline.
                # Keep nosuid/nodev/noexec on the one writable owned-device leaf.
                for mount_source,flags in [(os.fsencode(source),4096),(None,4096|32|2|4|8)]:
                    if libc.mount(mount_source,os.fsencode(target),None,flags,None)!=0:
                        error=ctypes.get_errno();raise OSError(error,os.strerror(error),str(target))
                unique=root/'dev/block/mapper/by-uuid'/uuid
                if not unique.is_symlink():unique.symlink_to('../../'+p.name)
                else:assert os.readlink(unique)=='../../'+p.name
                context=ctypes.c_char_p()
                assert lib.selabel_lookup_raw(handle,ctypes.byref(context),('/dev/block/mapper/by-uuid/'+uuid).encode(),stat.S_IFLNK|0o777)==0
                assert lib.lsetfilecon_raw(str(unique).encode(),context)==0;lib.freecon(context)
                seen.add(key);live[uuid]=(p.name,name)
                state['dm_nodes'].append({'name':name,'kernel_name':p.name,'uuid':uuid,'major':major,'minor':minor,'label':os.getxattr(node,'security.selinux').decode().rstrip('\0'),'observed_monotonic':observed,'published_monotonic':time.monotonic(),'publication_seconds':time.monotonic()-observed})
                save(out/'devices.json',state)
            except OSError as error:
                if error.errno not in (errno.ENOENT,errno.ENODEV,errno.EINVAL):raise
                continue  # real kernel creation/removal raced sysfs reads
        time.sleep(.02)  # native device-event bridge, no model polling
    app_log.close()
    if network is not None:network.snapshot(root,out,'monitor-close')


if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);parser.add_argument('output',type=Path);parser.add_argument('parent',type=int);args=parser.parse_args();monitor(args.root,args.output,args.parent)
