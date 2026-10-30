import os,json,socket,errno
assert os.getuid()==10000 and os.geteuid()==10000
status=open('/proc/self/status').read();caps=next(x.split()[1] for x in status.splitlines() if x.startswith('CapEff:'));assert int(caps,16)==0
assert not os.path.exists('/home/tv')
try:
 open('/input/readonly','w');raise AssertionError('Read-only input writable')
except OSError as e:
 assert e.errno in (errno.EROFS,errno.EACCES)
with open('/data/persist.txt','w') as f:f.write('namespace-data')
net=socket.socket();net.settimeout(1)
try:
 net.connect(('127.0.0.1',int(os.environ['HOST_CANARY_PORT'])));raise AssertionError('Host loopback reachable')
except OSError as e:
 assert e.errno in (errno.ECONNREFUSED,errno.ENETUNREACH,errno.EHOSTUNREACH)
finally:net.close()
print(json.dumps({'isolation_preflight_pass':True,'uid':os.getuid(),'groups':os.getgroups(),'effective_capabilities_hex':caps,'host_home_absent':True,'readonly_input':True,'host_loopback_unreachable':True,'writable_data':True}))
