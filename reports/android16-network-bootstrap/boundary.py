#!/usr/bin/env python3
"""Private Linux BPF mount and real sysctl bindings for original AOSP loaders."""
from pathlib import Path
import json,os,stat,subprocess,time

def save(path,value):
    path.write_text(json.dumps(value,indent=2)+'\n')

def mount(args,pass_fds=()):
    subprocess.run(['/usr/bin/mount',*map(str,args)],pass_fds=pass_fds,check=True,stdout=subprocess.DEVNULL)

def prepare(root,out):
    assert os.geteuid()==0
    host_net=int(os.environ['ARCHTV_HOST_NETNS_INODE'])
    current_net=Path('/proc/self/ns/net').stat().st_ino
    assert current_net!=host_net,'Refuse host network namespace'
    names=os.environ.get('LISTEN_FDNAMES','').split(':')
    assert names==['archtv-bpf-jit','archtv-bpf-kallsyms','archtv-host-netns'],names
    assert os.environ.get('LISTEN_FDS')=='3'
    assert os.fstat(5).st_ino==host_net,'Unexpected host network handle'
    private_net_fd=os.open('/proc/self/ns/net',os.O_RDONLY|os.O_CLOEXEC)
    controls={}
    for fd,name in zip([3,4],['bpf_jit_enable','bpf_jit_kallsyms']):
        assert os.readlink('/proc/self/fd/'+str(fd))=='/proc/sys/net/core/'+name
        os.lseek(fd,0,os.SEEK_SET);value=os.read(fd,128).decode().strip()
        assert value=='1',(name,value)  # Original loader writes exactly this existing value.
        controls[name]=(fd,value)
    target=root/'sys/fs/bpf';target.mkdir(parents=True,exist_ok=True)
    host_bpf_device=Path('/sys/fs/bpf').stat().st_dev
    mount(['-t','bpf','-o','nodev,noexec,nosuid','bpf',target])
    assert target.stat().st_dev!=host_bpf_device,'Refuse shared host BPF filesystem'
    # Linux bpf_fill_super()->populate_bpffs() installs these iterator links.
    # kernel/bpf/preload/bpf_preload_kern.c fixes their names; they are not
    # Android readiness or maps inherited from the host mount.
    builtins=[]
    for p in target.iterdir():
        s=p.lstat()
        assert p.name in {'maps.debug','progs.debug'},('Unexpected fresh bpffs entry',p.name)
        assert stat.S_ISREG(s.st_mode) and stat.S_IMODE(s.st_mode)==0o400 and s.st_uid==0
        builtins.append(p.name)
    # Containers only, matching original createDir(). Never create mainline_done or pins.
    for name in ['tethering','netd_shared','netd_readonly','net_shared','net_private','loader']:
        p=target/name;p.mkdir();p.chmod(0o1777)
    core=root/'proc/sys/net/core'
    existing={p.name:os.open(p,os.O_PATH|os.O_CLOEXEC) for p in core.iterdir() if p.is_file()}
    assert not set(controls)&set(existing),'Kernel now has private JIT controls; review boundary'
    # Preserve real private-net controls while adding the two actual global nodes.
    mount(['-t','tmpfs','-o','mode=0755,nodev,nosuid,noexec','archtv-net-core',core])
    bound=[]
    for name,fd in {**existing,**{n:f for n,(f,v) in controls.items()}}.items():
        p=core/name;p.touch(mode=0o600)
        # proc sysctl dentries are revalidated against the caller's netns.
        # Bind the actual global node while temporarily in the host netns;
        # no sockets, writes or loaders run there, and always restore first.
        if name in controls:
            try:
                os.setns(5,0)
                source='/proc/sys/net/core/'+name
                original=os.stat(source)
                assert Path(source).read_text().strip()==controls[name][1]
                staging=root/'archtv-kernel-controls';staging.mkdir(exist_ok=True)
                staged=staging/name;staged.touch(mode=0o600)
                mount(['--bind',source,staged])
            finally:
                os.setns(private_net_fd,0)
            assert Path('/proc/self/ns/net').stat().st_ino==current_net
            mount(['--bind',staged,p])
        else:
            mount(['--no-canonicalize','--bind','/proc/self/fd/'+str(fd),p],pass_fds=(fd,))
        if name not in controls: original=os.fstat(fd)
        actual=p.stat()
        assert (original.st_dev,original.st_ino)==(actual.st_dev,actual.st_ino),(name,(original.st_dev,original.st_ino),(actual.st_dev,actual.st_ino),p.read_text().strip())
        bound.append({'name':name,'device':actual.st_dev,'inode':actual.st_ino,'global':name in controls})
        os.close(fd)
    os.close(private_net_fd);os.close(5)
    for key in ['LISTEN_FDS','LISTEN_FDNAMES','LISTEN_PID']:os.environ.pop(key,None)
    source=Path('/sys/kernel/btf');dest=root/'sys/kernel/btf';dest.mkdir(parents=True,exist_ok=True)
    assert (source/'vmlinux').is_file()
    mount(['--bind',source,dest]);mount(['-o','remount,bind,ro',dest])
    # A new sysfs superblock in this actual private NET exposes its real
    # interface objects. Never bind the host's /sys/class/net into Android.
    net_sysfs=out/'private-network-sysfs';net_sysfs.mkdir()
    mount(['-t','sysfs','-o','ro,nodev,nosuid,noexec','sysfs',net_sysfs])
    interfaces=sorted(p.name for p in (net_sysfs/'class/net').iterdir())
    assert interfaces==['lo'],('Unexpected initial private interfaces',interfaces)
    for logical in ['class/net','devices/virtual/net']:
        destination=root/'sys'/logical;destination.mkdir(parents=True,exist_ok=True)
        mount(['--bind',net_sysfs/logical,destination]);mount(['-o','remount,bind,ro',destination])
    assert (root/'sys/class/net/lo').is_dir()
    save(out/'network-sysfs.json',{'private_netns':current_net,'interfaces':interfaces,'source':str(net_sysfs),'scope':'Real private-net sysfs view, read-only class/net and devices/virtual/net only; no host interface binding or fabricated metadata.'})
    save(out/'network-boundary.json',{'host_netns':host_net,'private_netns':current_net,'controls':bound,'global_values':{n:v for n,(f,v) in controls.items()},'bpf_root':str(target),'bpf_device':target.stat().st_dev,'kernel_preload_entries':sorted(builtins),'cgroup_view':str(root/'sys/fs/cgroup'),'scope':'Fresh private bpffs with kernel preload iterators; real sysctl inodes, existing private controls preserved. No Android programs loaded or readiness created.'})

def snapshot(root,out,phase):
    """Retain kernel IDs only for objects pinned under this run's private mount."""
    prefix=str(root/'sys/fs/bpf')+'/'
    record={'phase':phase,'time':time.time(),'objects':{},'errors':[]}
    for kind in ['prog','map','link']:
        p=subprocess.run(['/usr/bin/bpftool','-j','-f',kind,'show'],capture_output=True,text=True,timeout=3)
        if p.returncode:
            record['errors'].append({'kind':kind,'exit':p.returncode,'stderr':p.stderr});continue
        data=json.loads(p.stdout)
        record['objects'][kind]=[o for o in data if any(str(path).startswith(prefix) and str(path) not in {prefix+'maps.debug',prefix+'progs.debug'} for path in o.get('pinned',[]))]
    path=out/'bpf-owned.json';records=json.loads(path.read_text()) if path.exists() else []
    records.append(record);save(path,records)
    return record
