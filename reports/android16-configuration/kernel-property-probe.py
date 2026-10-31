from pathlib import Path
import gzip,subprocess,tempfile,os,json,datetime,sys
fd,p=tempfile.mkstemp(prefix='archtv-a16-selinux-label-',dir='/tmp');os.close(fd)
try:
 try:os.setxattr(p,'security.selinux',b'u:object_r:properties_serial:s0');label={'success':True}
 except OSError as error:label={'success':False,'errno':error.errno,'error':error.strerror}
finally:os.unlink(p)
config=gzip.open('/proc/config.gz','rt').read().splitlines();prefixes=['CONFIG_SECURITY_SELINUX','CONFIG_ANDROID_BINDER','CONFIG_LSM=','CONFIG_NAMESPACES=','CONFIG_MEMFD_CREATE='];result={'observed_at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'effective_uid':os.geteuid(),'effective_gid':os.getegid(),'kernel':subprocess.check_output(['uname','-r'],text=True).strip(),'active_lsm':Path('/sys/kernel/security/lsm').read_text().strip(),'selected_config':[x for x in config if any(x.startswith(p) for p in prefixes)],'selinux_label_private_file':label,'scope':'Read-only host config plus label syscall on a private disposable file. No policy/kernel changes, no Android property-area or service execution, no complete isolation acceptance.'};out=Path(sys.argv[1]);out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result))
