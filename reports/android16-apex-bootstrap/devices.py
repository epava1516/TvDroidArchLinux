#!/usr/bin/env python3
"""Research-only Linux device boundary for original apexd, never a device emulator.

Kernel loop allocations and dm tables remain real/global. Only an idle loop
pool and dm names derived from the pinned APEX manifests enter the private dev.
The outer runner owns cleanup. This does not establish MAC isolation.
"""
from pathlib import Path
import argparse, ctypes, errno, fcntl, json, os, re, signal, stat, struct, subprocess, time

REPO = Path('/home/tv/repositorio-principal')


def save(path, value):
    temp = path.with_suffix('.tmp')
    temp.write_text(json.dumps(value, indent=2) + '\n')
    temp.replace(path)


def mount_backing_image(image, target, number, out):
    """Real readonly/autoclear Linux backing slot, outside original APEX IDs."""
    image=Path(image).resolve();assert number in [128,129] and image.is_file()
    path=out/'backing-loops.json';rows=json.loads(path.read_text()) if path.exists() else []
    assert all(row['id']!=number for row in rows)
    kernel=Path('/sys/devices/virtual/block')/f'loop{number}'
    backing=kernel/'loop/backing_file'
    assert not (backing.exists() and backing.read_text().strip()), 'Backing slot already occupied'
    row={'id':number,'image':str(image),'created':False,'configured':False,'mounted':False}
    rows.append(row);save(path,rows)
    if not kernel.exists():
        ctl=os.open('/dev/loop-control',os.O_RDWR|os.O_CLOEXEC)
        try: fcntl.ioctl(ctl,0x4c80,number)
        finally: os.close(ctl)
        row['created']=True;save(path,rows)
    major,minor=map(int,(kernel/'dev').read_text().split(':'))
    node=out/f'backing-loop{number}';os.mknod(node,stat.S_IFBLK|0o600,os.makedev(major,minor))
    fd=os.open(node,os.O_RDWR|os.O_CLOEXEC);image_fd=os.open(image,os.O_RDONLY|os.O_CLOEXEC)
    try:
        # Linux UAPI loop_config, native x86_64 ABI304 bytes. Real kernel flags:
        # LO_FLAGS_READ_ONLY1 | LO_FLAGS_AUTOCLEAR4; keep FD until mount owns it.
        info=struct.pack('=QQQQQIIII64s64s32sQQ',0,0,0,0,0,0,0,0,5,str(image).encode()[:63].ljust(64,b'\0'),b'\0'*64,b'\0'*32,0,0)
        config=struct.pack('=II',image_fd,0)+info+b'\0'*64;assert len(config)==304
        fcntl.ioctl(fd,0x4c0a,config)  # LOOP_CONFIGURE, not simulated ioctl
        actual=bytearray(232);fcntl.ioctl(fd,0x4c05,actual,True)
        fields=struct.unpack('=QQQQQIIII64s64s32sQQ',actual)
        assert fields[5]==number and fields[8]&5==5 and fields[1]==image.stat().st_ino
        row.update(configured=True,flags=fields[8],image_inode=fields[1],major=major,minor=minor);save(path,rows)
        subprocess.run(['mount','-o','ro,noload',str(node),str(target)],check=True)
        assert os.statvfs(target).f_flag & os.ST_RDONLY
        row['mounted']=True;save(path,rows)
    finally:
        os.close(image_fd);os.close(fd)


def prepare(root, out, data_store, bootstrap=False):
    modules = json.loads((REPO/'reports/android16-apex-bootstrap/complete-inputs.json').read_text())['modules']
    allowed = {m['name'] for m in modules}
    assert len(allowed) == 41
    if bootstrap:allowed |= {m['name']+'@'+str(m['version']) for m in modules}
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
    import importlib.util
    userdata_spec=importlib.util.spec_from_file_location('linux_userdata',REPO/'reports/android16-package-bootstrap/userdata.py')
    userdata=importlib.util.module_from_spec(userdata_spec);userdata_spec.loader.exec_module(userdata)
    checkpoint=os.environ.get('ARCHTV_RUN_CHECKPOINT')
    owned_userdata=userdata.verified_verity_backing(checkpoint) if checkpoint else None
    owned_data_image=owned_userdata['store']['backing']['image'] if owned_userdata else None
    paths=sorted(Path('/sys/devices/virtual/block').glob('loop*'),key=lambda p:int(p.name[4:]))
    idle=[]; occupied=[]
    for p in paths:
        backing=p/'loop/backing_file'
        if backing.exists() and backing.read_text().strip():
            value=backing.read_text().strip()
            assert '/home/tv/repositorio-principal/dist/aosp16/' in value or value=='/home/tv/.cache/archtv/aosp16-qpr2/artifact-selection/gsi-original/system.img' or (value==owned_data_image and int(p.name[4:])==130),value
            occupied.append(int(p.name[4:]))
        else: idle.append(int(p.name[4:]))
    backing_rows=json.loads((out/'backing-loops.json').read_text()) if bootstrap else []
    if bootstrap:assert occupied==([128,129,130] if owned_userdata else [128,129]) and all(row['mounted'] and row['flags']&5==5 for row in backing_rows)
    created=[row['id'] for row in backing_rows if row['created']]; next_id=max([int(p.name[4:]) for p in paths],default=-1)+1
    state={'allowed_dm_names':sorted(allowed),'loop_pool':[],'created_loop_ids':created,'occupied_factory_loops':occupied,'dm_nodes':[],'scope':'Real Linux devices; trusted diagnostic only, not MAC or APK acceptance'}
    save(out/'devices.json',state)
    ctl=os.open('/dev/loop-control',os.O_RDWR|os.O_CLOEXEC)
    try:
        if bootstrap:
            pool=list(range(2*len(modules)+8));assert pool==list(range(90))
            for number in pool:
                kernel=Path('/sys/devices/virtual/block')/f'loop{number}'
                backing=kernel/'loop/backing_file'
                assert not (backing.exists() and backing.read_text().strip()), ('Original bootstrap slot occupied',number)
                if not kernel.exists():
                    fcntl.ioctl(ctl,0x4c80,number);created.append(number);save(out/'devices.json',state)
        else:
            while len(idle)<2*len(modules)+8:
                fcntl.ioctl(ctl,0x4c80,next_id)
                created.append(next_id);idle.append(next_id);next_id+=1;save(out/'devices.json',state)
            pool=idle[:2*len(modules)+8]
            assert pool==list(range(2,92)), ('Reserved loop profile mismatch',pool)
    finally: os.close(ctl)
    state['loop_policy_profile']={'first':pool[0],'last':pool[-1],'scope':'Actual private RW pool; original broad loop labels are not exclusive'}
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
    # Reuse the real kernel's block-link indexes, rather than dynamically
    # copying sysfs-typed links into tmpfs (which requires an invalid extra
    # filesystem-associate adaptation under MAC). Metadata indexes are RO;
    # they do not create /dev nodes or grant access to host block contents.
    views=[]
    for logical in ['sys/devices/virtual/block','sys/dev/block','sys/block','sys/class/block']:
        target=root/logical
        subprocess.run(['mount','--bind','/'+logical,str(target)],check=True)
        subprocess.run(['mount','-o','remount,bind,ro',str(target)],check=True)
        assert os.statvfs(target).f_flag & os.ST_RDONLY
        views.append({'source':'/'+logical,'target':str(target),'readonly':True})
    save(root.parent/'sysfs-kernel-views.json',{'views':views,'scope':'Actual read-only kernel metadata including host indexes; /dev remains manifest-filtered. Not block-data access or isolation proof.'})


def enable_loop_controls(root,out):
    state=json.loads((out/'devices.json').read_text());changes=[]
    profile=state['loop_policy_profile']
    assert state['loop_pool']==list(range(profile['first'],profile['last']+1)) and len(state['loop_pool'])==90, 'Refuse changed control pool'
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
    for number in state['occupied_factory_loops']:
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


def read_dm_identity_attribute(path, state, out):
    """Only computed DM name/uuid metadata; never suppress other I/O errors.

    Linux dm_attr_{name,uuid}_show returns EIO when dm_copy_name_and_uuid
    cannot find the hash-cell identity. The mapping can be leaving sysfs.
    Final real DM/BPF cleanup checks remain mandatory.
    """
    assert path.name in {'name', 'uuid'} and path.parent.name == 'dm'
    assert path.parent.parent.parent == Path('/sys/devices/virtual/block')
    try:
        return path.read_text().strip()
    except OSError as error:
        if error.errno != errno.EIO:
            raise
        state['dm_identity_unavailable_count'] = state.get('dm_identity_unavailable_count', 0) + 1
        rows = state.setdefault('dm_identity_unavailable', [])
        if len(rows) < 32:
            rows.append({'path': str(path), 'errno': error.errno,
                         'observed_monotonic': time.monotonic(),
                         'scope': 'Computed kernel identity unavailable; not device/cleanup acceptance'})
        save(out/'devices.json', state)
        return None


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
    # Factory preparation already copied the original platform/vendor patterns
    # verbatim for Linux labeling. Reuse that exact private input rather than
    # reopening Android file_contexts_file under Linux after enforcing starts.
    contexts=out/'original-file-contexts';assert contexts.is_file()
    opt=Opt(3,str(contexts).encode());handle=lib.selabel_open(0,ctypes.byref(opt),1);assert handle
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
    network_identity_blocked=False
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
    monitor_error=None
    try:
        while time.monotonic()<end and not stopping:
            observe_app_startups(app_log,app_state,out,owner_cgroup,namespaces,procbase)
            if network is not None and not network_identity_blocked:
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
                    except PermissionError as error:
                        # Optional read-only diagnosis must not continuously retry
                        # MAC-denied proc access and rotate away the actual failure.
                        # Stop only this sampler; device/BPF monitoring continues.
                        network_identity_blocked=True
                        save(out/'network-identities-error.json',{'error':str(error),'scope':'Optional Linux proc sampler stopped after actual permission denial; missing identities remain unknown. No MAC permissions changed.'})
                        break
                    except (OSError,ProcessLookupError):continue
            if network is not None and not bpf_captured and (root/'sys/fs/bpf/netd_shared/mainline_done').is_dir():
                network.snapshot(root,out,'mainline-done');bpf_captured=True
            for uuid,(kernel_name,name) in list(live.items()):
                kernel=Path('/sys/devices/virtual/block')/kernel_name
                try: present=read_dm_identity_attribute(kernel/'dm/uuid',state,out)==uuid
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
                    name=read_dm_identity_attribute(p/'dm/name',state,out)
                    if name not in allowed:continue
                    uuid=read_dm_identity_attribute(p/'dm/uuid',state,out)
                    if uuid is None:continue
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
    except BaseException as error:
        monitor_error=repr(error)
        raise
    finally:
        snapshot_completed=False
        try:
            app_log.close()
            if network is not None:
                network.snapshot(root,out,'monitor-close')
                snapshot_completed=True
        finally:
            save(out/'device-monitor-result.json', {
                'loop_error': monitor_error,
                'network_snapshot_attempted': network is not None,
                'snapshot_call_completed': snapshot_completed,
                'scope': 'Lifecycle evidence only; snapshot errors, final ownership and monitor exit remain independently checked'})



if __name__=='__main__':
    parser=argparse.ArgumentParser();parser.add_argument('root',type=Path);parser.add_argument('output',type=Path);parser.add_argument('parent',type=int);args=parser.parse_args();monitor(args.root,args.output,args.parent)
