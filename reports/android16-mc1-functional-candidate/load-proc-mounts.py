from pathlib import Path
import ctypes,hashlib,json,subprocess
r=Path('/home/tv/repositorio-principal');m=Path('/tmp/archtv-mc1-policy-load');m.mkdir(exist_ok=True)
subprocess.run(['/usr/bin/mount','--make-rprivate','/'],check=True)
subprocess.run(['/usr/bin/mount','-t','selinuxfs','selinuxfs',str(m)],check=True)
subprocess.run(['/usr/bin/mount','-o','remount,rw',str(m)],check=True)
assert not (__import__('os').statvfs(m).f_flag & __import__('os').ST_RDONLY)
lib=ctypes.CDLL(str(r/'dist/aosp16/linux-selinux-handoff-2/libselinux-3.11/src/libselinux.so.1'),use_errno=True)
lib.set_selinuxmnt.argtypes=[ctypes.c_char_p];lib.set_selinuxmnt(str(m).encode())
lib.security_load_policy.argtypes=[ctypes.c_void_p,ctypes.c_size_t]
lib.getcon_raw.argtypes=[ctypes.POINTER(ctypes.c_char_p)];lib.freecon.argtypes=[ctypes.c_void_p]
def context():
 c=ctypes.c_char_p();ret=lib.getcon_raw(ctypes.byref(c));v=c.value.decode() if ret==0 else None
 if ret==0:lib.freecon(c)
 return v
before={'enforce':(m/'enforce').read_text().strip(),'context':context()}
assert before['enforce']=='0',before
p=r/'dist/aosp16/mc1-functional-policy-6/policy.bin';b=p.read_bytes();sha=hashlib.sha256(b).hexdigest()
assert sha=='1777ae2eb82f23ab5cf826aa72058eb6e2876f188a16fcbf74e109fd6352cb41'
print('POLICY_LOAD_BEFORE '+json.dumps({'before':before,'sha256':sha,'bytes':len(b)}),flush=True)
ret=lib.security_load_policy(b,len(b));err=ctypes.get_errno()
print('POLICY_LOAD_RESULT '+json.dumps({'return':ret,'errno':err,'enforce':(m/'enforce').read_text().strip(),'context':context()}),flush=True)
assert ret==0
assert (m/'enforce').read_text().strip()=='0'
