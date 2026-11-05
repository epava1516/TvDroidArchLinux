#!/usr/bin/env python3
"""One bounded original APEX cohort with exact global-device cleanup/recovery."""
from pathlib import Path
import datetime,fcntl,hashlib,json,os,re,subprocess,sys,time,uuid

repo=Path(__file__).resolve().parents[2]
payload=(repo/sys.argv[1]).resolve()
data_store=Path(sys.argv[2]).resolve()
assert data_store.parent==Path("/home/tv/.cache/archtv/aosp16-qpr2") and data_store.name.startswith("apex-data-store-") and (data_store/"linux-preparation.json").is_file()
assert os.geteuid()==0 and payload.is_relative_to(repo/'dist/aosp16') and payload.is_file()
# Explicit bounded resource comparison, default unchanged. A4-vCPU VM retains
# at least one CPU of aggregate headroom at the experimental300% ceiling.
# This is not a production lightness or scheduling guarantee.
def candidate_cpu_quota_percent(raw, host_cpus):
    assert raw in ('200', '300'), 'Only reviewed200/300 percent CPU profiles'
    value = int(raw)
    assert value == 200 or (host_cpus is not None and host_cpus >= 4), '300 percent requires at least4 host-visible CPUs'
    return value
cpu_quota_percent = candidate_cpu_quota_percent(
    os.environ.get('ARCHTV_CANDIDATE_CPU_QUOTA_PERCENT', '200'), os.cpu_count())
assert cpu_quota_percent == 200 or len(sys.argv) == 4, '300 percent is integrated comparison only'
lock=open('/home/tv/.cache/archtv/apex-cohort.lock','a');fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
stamp=datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ')
recovery=Path(os.environ['ARCHTV_RUN_CHECKPOINT']) if os.environ.get('ARCHTV_RUN_CHECKPOINT') else Path('/home/tv/recuperacion-archtv')/(stamp+'-apex-activation')
if os.environ.get('ARCHTV_RUN_CHECKPOINT'):assert (recovery/'completion-manifest.json').is_file()
else:recovery.mkdir(mode=0o700)
Path('/home/tv/.cache/archtv/kernel-aosp16-1/apex-current-checkpoint').write_text(str(recovery)+'\n')
expected=json.loads((repo/'reports/android16-apex-bootstrap/complete-inputs.json').read_text())['modules'];allowed={m['name'] for m in expected}
bootstrap_profile=(payload.parent/'build-options.json').is_file() and json.loads((payload.parent/'build-options.json').read_text()).get('original_apex_bootstrap',False)
if bootstrap_profile:allowed |= {m['name']+'@'+str(m['version']) for m in expected}
def command(args,**kw):return subprocess.run(args,text=True,capture_output=True,**kw)
def dm_names(result):
    assert result.returncode==0,result.stderr
    raw=result.stdout.strip()
    return set() if raw=='No devices found' else {line.strip() for line in raw.splitlines() if line.strip()}
import importlib.util
userdata_spec=importlib.util.spec_from_file_location('linux_userdata',repo/'reports/android16-package-bootstrap/userdata.py')
userdata=importlib.util.module_from_spec(userdata_spec);userdata_spec.loader.exec_module(userdata)
owned_userdata=userdata.verified_verity_backing(recovery)
expected_userdata_images={owned_userdata['store']['backing']['image']} if owned_userdata else set()
initial_loop_images=set(command(['losetup','-l','-n','-O','BACK-FILE']).stdout.strip().splitlines())
assert initial_loop_images==expected_userdata_images,'Another loop workload or missing owned data loop'
assert not command(['systemctl','list-units','archtv-mc3*','--all','--no-legend']).stdout.strip(),'Another cohort exists'
integrated_socket=Path(sys.argv[3]) if len(sys.argv)==4 else None
# Only extend the post-start interaction window; native startup stays300000ms.
interaction_extension=0
if integrated_socket:
 observe_ms=json.loads((payload.parent/'build-options.json').read_text()).get('observe_ms',3000)
 assert isinstance(observe_ms,int) and 3000<=observe_ms<=600000
 interaction_extension=max(0,(observe_ms+999)//1000-30)
(recovery/'before.json').write_text(json.dumps({'phase':'preflight','argv':sys.argv,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'head':command(['runuser','-u','tv','--','git','-C',str(repo),'rev-parse','HEAD']).stdout.strip(),'pending':command(['runuser','-u','tv','--','git','-C',str(repo),'status','--short']).stdout},indent=2)+'\n')
os.chown(recovery,1000,1000);os.chown(recovery/'before.json',1000,1000)
sessions=command(['loginctl','list-sessions','--no-legend']).stdout.strip()
if integrated_socket:
    runtime_record=recovery/'wayland-runtime.json'
    if runtime_record.exists():
        runtime=json.loads(runtime_record.read_text());manifest=json.loads((recovery/'completion-manifest.json').read_text())
        assert runtime['id']==manifest['id'] and runtime['path']=='/run/user/1000/archtv-'+manifest['id']
        assert integrated_socket.parent==Path(runtime['path'])
        rst=integrated_socket.parent.lstat();assert (rst.st_dev,rst.st_ino)==(runtime['dev'],runtime['inode']) and rst.st_uid==1000
        assert os.getxattr(integrated_socket.parent,'security.selinux').rstrip(b'\0').decode()==runtime['context']
    else:assert integrated_socket.parent==Path('/run/user/1000')
    assert integrated_socket.is_socket()
    console_found=False
    for row in sessions.splitlines():
        fields=row.split();assert len(fields)>2 and fields[1]=='1000',row
        sid=fields[0]
        info=command(['loginctl','show-session',sid,'-p','TTY','-p','Service','-p','Class']).stdout
        if 'Class=manager' in info:
            assert 'Service=systemd-user' in info and '\nTTY=\n' in '\n'+info,info
        else:
            assert 'TTY=tty2' in info and 'Service=login' in info,info
            console_found=True
    assert console_found,'Owned tty2 session missing'
else:assert not sessions,'Interactive session present'

before={'utc':stamp,'head':command(['runuser','-u','tv','--','git','-C',str(repo),'rev-parse','HEAD']).stdout.strip(),'pending':command(['runuser','-u','tv','--','git','-C',str(repo),'status','--short']).stdout,'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'kernel':os.uname().release,'payload':str(payload),'data_store':str(data_store),'integrated_socket':str(integrated_socket) if integrated_socket else None,'data_preparation_sha256':hashlib.sha256((data_store/'linux-preparation.json').read_bytes()).hexdigest(),'payload_sha256':hashlib.file_digest(payload.open('rb'),'sha256').hexdigest(),'allowed_dm_names':sorted(allowed),'modules_before':command(['lsmod']).stdout,'scope':('Bounded enforcing integration diagnostic requested; inspect mac-window.json actual modes/result. No APK/MAC acceptance or VM restart inferred.' if os.environ.get('ARCHTV_MAC_WINDOW_SECONDS') else 'Trusted original APEX activation only. Permissive; no APK or MAC acceptance. No VM restart requested.')}
before['cpu_quota_percent']=cpu_quota_percent
assert re.fullmatch('[0-9a-f]{40}',before['head']),before['head']
(recovery/'before.json').write_text(json.dumps(before,indent=2)+'\n')
(recovery/'pending.patch').write_bytes(subprocess.check_output(['runuser','-u','tv','--','git','-C',str(repo),'diff','--binary']))
own=['reports/android16-network-bootstrap/boundary.py','runtime/aosp/linux-services/org/archtv/aosplinux/ServiceLauncher.java','runtime/aosp/native/linux-exec-context.c','runtime/aosp/native/linux-property-worker.cpp','runtime/aosp/native/linux-mc1-cohort.h','crates/archtv-core/examples/native_supervisor.rs','reports/android16-apex-bootstrap/run.py','reports/android16-apex-bootstrap/execute.py','reports/android16-apex-bootstrap/devices.py','reports/android16-apex-bootstrap/build-payload.py','reports/android16-package-bootstrap/execute-integrated.py','reports/android16-package-bootstrap/build-integrated.py','runtime/aosp/linux-services/org/archtv/aosplinux/SelectedServices.java','runtime/aosp/linux-services/install-markor.sh']
before['own_code_sha256']={n:hashlib.sha256((repo/n).read_bytes()).hexdigest() for n in own}
for name in own:
    destination=recovery/'code'/name;destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes((repo/name).read_bytes())
(recovery/'before.json').write_text(json.dumps(before,indent=2)+'\n')
(recovery/'RETOMAR.txt').write_text('Read before.json, run.log, result.json and /home/tv/repositorio-principal/docs/ESTADO.md.\nOriginal apexd will activate signed GSI APEX/CAPEX, create actual loop/dm-verity devices, and publish its own inventory. Linux mirrors only idle loop-pool nodes and exact allowed dm names into private dev; metadata sysfs is read-only. A disk-backed Linux directory holds unmodified original APEX cache; the daemon must revalidate it. dm-verity original restart-on-corruption remains enabled; kernel failure can interrupt connection. Snapshot and external console confirmed, restore not rehearsed.\nRecovery: stop only the archtv-apex-* unit recorded in result/before metadata; wait for its processes/namespaces to exit. Compare dmsetup info with before and allowed_dm_names. Remove only exact NEW owned names recorded in devices.json/result; never remove unrelated devices or detach other work. Empty newly-created loops can be removed with LOOP_CTL_REMOVE only after checking unused; busy devices require diagnosis. Runner normally performs these steps.\nIf VM must recover: Space at systemd-boot, select original archtv-lts-selinux-test.conf or arch.conf. Active candidate has a separate archtv-aosp16-test.conf entry; default arch.conf remains original. No old PID/handles apply after reboot. No Android full boot or Waydroid.\n')
if integrated_socket:
    bpf_before={k:json.loads(command(['bpftool','-j',k,'show']).stdout) for k in ['prog','map','link']}
    (recovery/'bpf-before.json').write_text(json.dumps(bpf_before,indent=2)+'\n')
    (recovery/'bpf-sysctls-before.json').write_text(json.dumps({n:Path('/proc/sys/'+n).read_text().strip() for n in ['kernel/unprivileged_bpf_disabled','net/core/bpf_jit_enable','net/core/bpf_jit_kallsyms']},indent=2)+'\n')
    with (recovery/'RETOMAR.txt').open('a') as instructions:
        instructions.write('Network experiment: original nonroot Mainline BPF loader, then original platform loader and netd, in private NET/MOUNT/cgroup. Kernel BPF IDs remain global. Never delete unrelated host BPF or stop NetworkManager/systemd to empty inventory. Normal cleanup: stop only the recorded cohort, let private mounts/cgroups exit, then inspect bpf-owned.json and bpf-cleanup.json; remaining objects require diagnosis by exact IDs, not broad deletion. Global sysctls must retain recorded before values. No new policy/enforcing change.\n')
print('APEX_RECOVERY '+str(recovery),flush=True)
# Global effects begin only after the recovery point is on disk.
load=command(['modprobe','dm-verity']);assert load.returncode==0,load.stderr
baseline=command(['dmsetup','info','-c','--noheadings','-o','name']);assert baseline.returncode==0,baseline.stderr
dm_before=dm_names(baseline);assert not dm_before,dm_before
unit='archtv-apex-'+str(time.time_ns())
before['unit']=unit;before['dm_before']=sorted(dm_before);(recovery/'before.json').write_text(json.dumps(before,indent=2)+'\n')
started=time.time();log=recovery/'run.log';exit_code=None;cleanup=[]
# Opt-in bounded integration diagnostic; reuses the preopened-control watchdog
# from hwmanager-cohort/enforcing-window.py. Never enables a permissive domain.
mac_window=int(os.environ.get('ARCHTV_MAC_WINDOW_SECONDS','0'))
# A complete APK workflow includes the existing 300s native startup bound
# plus up to 600s post-start interaction. Short probes retain the 120s ceiling.
# This changes duration only; preopened-FD restoration and independent watchdog
# remain mandatory, with no permissive domain or administration exception.
mac_limit=300+(observe_ms+999)//1000 if integrated_socket and observe_ms>=30000 else 120
assert mac_window==0 or 4<=mac_window<=mac_limit

def candidate_run(args, **kwargs):
    if not mac_window:return subprocess.run(args,**kwargs)
    import ctypes,signal
    expected=os.environ['ARCHTV_MAC_EXPECT_POLICY_SHA256'];assert re.fullmatch('[0-9a-f]{64}',expected)
    lib=ctypes.CDLL(None,use_errno=True);assert lib.unshare(0x00020000)==0,ctypes.get_errno()
    subprocess.run(['mount','--make-rprivate','/'],check=True)
    control=recovery/'mac-control';control.mkdir(mode=0o700)
    subprocess.run(['mount','-t','selinuxfs','selinuxfs',str(control)],check=True)
    fd=None;watchdog=None;proc=None
    record={'seconds':mac_window,'scope':'Global enforcing only after real factory preparation; original subsystems, not APK/MAC acceptance by exit0','activated':False}
    try:
        assert (control/'enforce').read_text().strip()=='0'
        record['policy_readback_sha256']=hashlib.sha256((control/'policy').read_bytes()).hexdigest();assert record['policy_readback_sha256']==expected
        fd=os.open(control/'enforce',os.O_RDWR|os.O_CLOEXEC)
        def mode(value=None):
            os.lseek(fd,0,0)
            if value is not None:assert os.write(fd,value)==1;os.lseek(fd,0,0)
            return os.read(fd,16).strip()
        proc=subprocess.Popen(args,stdin=subprocess.PIPE,**{k:v for k,v in kwargs.items() if k!='timeout'})
        deadline=time.monotonic()+60
        while proc.poll() is None and 'MAC_FACTORY_PREPARED_AWAITING_RELEASE' not in log.read_text():
            if time.monotonic()>deadline:raise TimeoutError('Factory preparation did not reach MAC gate')
            time.sleep(.1)
        if proc.poll() is not None:
            record['candidate_exit_before_gate']=proc.returncode
            return subprocess.CompletedProcess(args,proc.returncode)
        # Fork outside candidate PID/mount/cgroup; no exec/library/path lookup
        # is needed for recovery through the preopened kernel control.
        watchdog=os.fork()
        if watchdog==0:
            time.sleep(mac_window)
            try:os.lseek(fd,0,0);os.write(fd,b'0');os._exit(0)
            except BaseException:os._exit(90)
        assert mode(b'1')==b'1';record['activated']=True;record['started_monotonic']=time.monotonic()
        proc.stdin.write(b'G');proc.stdin.flush();proc.stdin.close()
        try:code=proc.wait(timeout=mac_window+5)
        except subprocess.TimeoutExpired:
            subprocess.run(['systemctl','stop',unit+'.service'],check=True);code=124;proc.wait(timeout=15)
        record['candidate_exit']=code;record['mode_at_candidate_exit']=mode().decode();record['elapsed_enforcing_attempt']=time.monotonic()-record['started_monotonic']
        if record['mode_at_candidate_exit']!='1':code=124;record['window_expired_no_acceptance']=True
        return subprocess.CompletedProcess(args,code)
    finally:
        if fd is not None:
            os.lseek(fd,0,0);assert os.write(fd,b'0')==1;os.lseek(fd,0,0);record['restored_enforce']=os.read(fd,16).strip().decode();assert record['restored_enforce']=='0'
        if watchdog is not None:
            waited,status=os.waitpid(watchdog,os.WNOHANG)
            if not waited:os.kill(watchdog,signal.SIGTERM);_,status=os.waitpid(watchdog,0);record['watchdog_cancelled_after_restore']=True
            record['watchdog_status']=status
        (recovery/'mac-window.json').write_text(json.dumps(record,indent=2)+'\n')
        if fd is not None:os.close(fd)
        subprocess.run(['umount',str(control)],check=True);control.rmdir()

try:
    with log.open('x') as stream:
        result=candidate_run(['systemd-run','--wait','--pipe','--collect','--unit='+unit,'--slice=archtv.slice','--service-type=exec','--property=RuntimeMaxSec='+str(385+interaction_extension if integrated_socket else 210),'--property=TimeoutStopSec=5','--property=KillMode=control-group','--property=MemoryMax=4G','--property=MemorySwapMax=1G','--property=CPUQuota='+str(cpu_quota_percent)+'%','--property=TasksMax='+str(1024 if integrated_socket else 256),'--setenv=ARCHTV_RUN_CHECKPOINT='+str(recovery),*(['--setenv=ARCHTV_MAC_STDIN_GATE=1'] if mac_window else []),*(['--property=OpenFile=/proc/sys/net/core/bpf_jit_enable:archtv-bpf-jit:read-only','--property=OpenFile=/proc/sys/net/core/bpf_jit_kallsyms:archtv-bpf-kallsyms:read-only','--property=OpenFile=/proc/self/ns/net:archtv-host-netns:read-only','--setenv=ARCHTV_HOST_NETNS_INODE='+str(Path('/proc/self/ns/net').stat().st_ino)] if integrated_socket else []),'timeout','--kill-after=5',str(380+interaction_extension if integrated_socket else 205),'setpriv','--inh-caps=-all','--ambient-caps=-all',*(['/usr/bin/python',str(repo/'reports/android16-package-bootstrap/execute-integrated.py'),'--prepare-wayland',str(integrated_socket),str(payload),str(data_store)] if integrated_socket and json.loads((payload.parent/'build-options.json').read_text()).get('preconnected_wayland',False) else ['unshare','--mount','--pid','--fork','--kill-child=SIGKILL','--net','--ipc','--uts','/usr/bin/python',*([str(repo/'reports/android16-package-bootstrap/execute-integrated.py'),str(integrated_socket),str(payload),str(data_store)] if integrated_socket else [str(repo/'reports/android16-apex-bootstrap/execute.py'),'--payload',str(payload),'--data-store',str(data_store),'--observe-logs'])])],stdout=stream,stderr=subprocess.STDOUT,timeout=405+interaction_extension if integrated_socket else 230)
        exit_code=result.returncode
finally:
    command(['systemctl','stop',unit+'.service'])
    # Namespace exit unmounts the private roots; verity tables are global and
    # must be removed by exact ownership, not by a broad dmsetup/losetup wipe.
    current=command(['dmsetup','info','-c','--noheadings','-o','name'])
    assert current.returncode==0,current.stderr
    names=dm_names(current)
    for name in sorted((names-dm_before)&allowed):
        try:
            result=command(['dmsetup','remove','--retry',name],timeout=5)
            cleanup.append({'name':name,'exit':result.returncode,'stderr':result.stderr})
        except subprocess.TimeoutExpired:
            cleanup.append({'name':name,'exit':None,'error':'Bounded removal timed out; not forced'})
    binding=recovery/'factory-path.json'
    if bootstrap_profile:
        factory=None
        if binding.exists():
            row=json.loads(binding.read_text());manifest=json.loads((recovery/'completion-manifest.json').read_text())
            assert row['id']==manifest['id'] and row['checkpoint']==str(recovery)
            assert str(uuid.UUID(row['id']))==row['id']
            candidate=repo/'dist/aosp16'/('apex-live-'+uuid.UUID(row['id']).hex);assert row['factory']==str(candidate)
            if candidate.is_dir():factory=candidate
    else:
        factories=sorted((repo/'dist/aosp16').glob('apex-live-*'),key=lambda p:p.stat().st_mtime)
        factory=factories[-1] if factories and factories[-1].stat().st_mtime>=started else None
    device_state=json.loads((factory/'devices.json').read_text()) if factory and (factory/'devices.json').exists() else None
    loop_cleanup=[]
    if not device_state and factory and (factory/'backing-loops.json').exists():
        rows=json.loads((factory/'backing-loops.json').read_text())
        device_state={'created_loop_ids':[row['id'] for row in rows if row['created']],'loop_controls':[],'scope':'Backing setup failed before APEX scaffold; exact owned IDs only'}
    if device_state:
        for item in device_state.get('loop_controls',[]):
            kernel=Path('/sys/devices/virtual/block')/('loop'+str(item['id']))
            backing=kernel/'loop/backing_file'
            if kernel.exists() and not (backing.exists() and backing.read_text().strip()):
                (kernel/item['attribute']).write_text(item['previous']+'\n')
        ctl=os.open('/dev/loop-control',os.O_RDWR|os.O_CLOEXEC)
        try:
            for number in reversed(device_state['created_loop_ids']):
                try:fcntl.ioctl(ctl,0x4c81,number);loop_cleanup.append({'id':number,'removed':True})
                except OSError as error:loop_cleanup.append({'id':number,'removed':False,'errno':error.errno})
        finally:os.close(ctl)
    bpf_cleanup={'verified':not bool(integrated_socket),'owned':{},'remaining':{},'errors':[]}
    if integrated_socket:
        records_path=factory/'bpf-owned.json' if factory else None
        records=json.loads(records_path.read_text()) if records_path and records_path.exists() else []
        bpf_cleanup['final_snapshot']=bool(records and records[-1]['phase']=='monitor-close')
        for kind in ['prog','map','link']:
            owned={o['id'] for row in records for o in row.get('objects',{}).get(kind,[])}
            bpf_cleanup['owned'][kind]=sorted(owned)
            current=command(['bpftool','-j',kind,'show'])
            if current.returncode:bpf_cleanup['errors'].append({'kind':kind,'stderr':current.stderr});continue
            bpf_cleanup['remaining'][kind]=sorted(owned & {o['id'] for o in json.loads(current.stdout)})
        bpf_cleanup['errors'] += [e for row in records for e in row.get('errors',[])]
        bpf_cleanup['verified']=bpf_cleanup['final_snapshot'] and not bpf_cleanup['errors'] and not any(bpf_cleanup['remaining'].values())
        (recovery/'bpf-cleanup.json').write_text(json.dumps(bpf_cleanup,indent=2)+'\n')
    final_dm=command(['dmsetup','info','-c','--noheadings','-o','name'])
    loops=command(['losetup','-l','-n','-O','BACK-FILE']).stdout.strip()
    klog=command(['journalctl','-b','-k','--since','@'+str(int(started)),'--no-pager','-o','json']).stdout
    messages=[]
    for line in klog.splitlines():
        row=json.loads(line);tag=row.get('SYSLOG_IDENTIFIER','');message=row.get('MESSAGE','')
        if 'apex' in tag.lower() or 'bpf' in tag.lower() or re.search(r'apexd|device-mapper|dm-verity|loop[0-9]+|avc:|audit.*(?:lost|suppressed|backlog|rate limit)',message,re.I):messages.append({'utc_us':row.get('__REALTIME_TIMESTAMP'),'tag':tag,'message':message})
    (recovery/'kernel-apex.json').write_text(json.dumps(messages,indent=2)+'\n')
    (recovery/'kernel-apex.log').write_text('\n'.join(row['tag']+': '+row['message'] for row in messages)+'\n')
    # Native Android KernelLogger/user AVC records may enter journald outside
    # the kernel-only transport. Preserve the real original service decisions.
    service_journal=command(['journalctl','-b','--since','@'+str(int(started)),'--no-pager','-o','json']).stdout
    service_messages=[]
    for line in service_journal.splitlines():
        row=json.loads(line);tag=row.get('SYSLOG_IDENTIFIER','');message=row.get('MESSAGE','')
        if tag.startswith('apexd-') or 'bpf' in tag.lower() or tag in ['servicemanager','hwservicemanager','apexd','vold','linkerconfig','derive_classpath','logd','keystore2','NetBpfLoad','BpfLoader','netd','archtv-platform-bpfloader'] or ('name=apexservice' in message and 'tclass=service_manager' in message):
            service_messages.append({'utc_us':row.get('__REALTIME_TIMESTAMP'),'transport':row.get('_TRANSPORT'),'pid':row.get('_PID'),'tag':tag,'message':message})
    (recovery/'android-service-journal.json').write_text(json.dumps(service_messages,indent=2)+'\n')

    text=log.read_text() if log.exists() else ''
    final={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'unit':unit,'factory':str(factory) if factory else None,'outer_exit':exit_code,'elapsed_seconds':time.time()-started,'native_complete_inventory_verified':'APEX_ORIGINAL_COMPLETE_INVENTORY_VERIFIED modules=41' in text,'bpf_cleanup':bpf_cleanup,'dm_cleanup':cleanup,'devices':device_state,'loop_cleanup':loop_cleanup,'final_dm':sorted(dm_names(final_dm)),'final_dm_raw':final_dm.stdout,'active_loops':loops,'owned_userdata_backing':owned_userdata,'unexpected_loop_images':sorted(set(loops.splitlines())-expected_userdata_images),'log_sha256':hashlib.sha256(log.read_bytes()).hexdigest() if log.exists() else None,'scope':'Execution evidence, not APK or MAC acceptance; inspect native results and errors. Host owner must subsequently unmount/detach its recorded private userdata backing.'}
    (recovery/'result.json').write_text(json.dumps(final,indent=2)+'\n')
    for p in recovery.iterdir():os.chown(p,1000,1000)
    os.chown(recovery,1000,1000)
    print('APEX_RESULT '+json.dumps({k:final[k] for k in ['outer_exit','elapsed_seconds','native_complete_inventory_verified','active_loops','final_dm']}),flush=True)
    print('APEX_EVIDENCE '+str(recovery),flush=True)
assert bpf_cleanup['verified'] and exit_code==0 and final['native_complete_inventory_verified'] and set(loops.splitlines())==expected_userdata_images and not dm_names(final_dm),{k:final[k] for k in ['outer_exit','native_complete_inventory_verified','active_loops','final_dm']}
