from pathlib import Path
import json,subprocess,shutil
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/composer-link-1';rows=json.loads((out/'state.json').read_text());old=rows['compile'][0]['argv'];flags=old[:old.index('-c')];src=r/'reports/android16-composer-link/log-observer.cpp';cmd=flags+['-c',str(src),'-o',str(out/'log-observer.o')];x=subprocess.run(cmd,capture_output=True,text=True,timeout=60);rec={'compile':{'argv':cmd,'exit':x.returncode,'stderr':x.stderr}};print('observer compile',x.returncode,x.stderr[:2000],flush=True);assert x.returncode==0
cmd=rows['links'][0]['argv'];cmd=[str(out/'log-observer.o') if a.endswith('/HWC2OnFbAdapter.o') else '--soname=log-observer.so' if a.startswith('--soname=') else str(out/'log-observer.so') if a==str(out/'libhwc2onfbadapter.so') else a for a in cmd];x=subprocess.run(cmd,capture_output=True,text=True,timeout=60);rec['link']={'argv':cmd,'exit':x.returncode,'stderr':x.stderr};(out/'observer-build.json').write_text(json.dumps(rec,indent=2)+'\n');print('observer link',x.returncode,x.stderr[:2000],flush=True);assert x.returncode==0
exe=r/'dist/aosp16/composer-native-execution-1';exe.mkdir();(exe/'data').mkdir();(exe/'app').mkdir()
for n in ['android.hardware.graphics.composer@2.1-service','android.hardware.graphics.composer@2.1-resources.so','libhwc2onfbadapter.so','log-observer.so']:shutil.copy2(out/n,exe/'data'/n)
for src in [r/'dist/aosp16/libui-link-2/libui.so',r/'dist/aosp16/hwc2on1-build-1/libhwc2on1adapter.so']:shutil.copy2(src,exe/'data'/src.name)
s=(r/'reports/android16-libui-link/native-launcher.py').read_text().replace('libui-native-execution-1','composer-native-execution-1');start=s.index("mount('-t','binder'");end=s.index("os.chown(out/'data'",start)
s=s[:start]+"""mount('-t','binder','-o','max=3','binder',root/'dev/binderfs')
for name in ['binder','vndbinder','hwbinder']:
 fd=os.open(root/'dev/binderfs/binder-control',os.O_RDWR|os.O_CLOEXEC);request=bytearray(struct.pack('256sII',name.encode(),0,0))
 try:fcntl.ioctl(fd,(3<<30)|(len(request)<<16)|(ord('b')<<8)|1,request,True)
 finally:os.close(fd)
 os.chmod(root/'dev/binderfs'/name,0o666);(root/'dev'/name).symlink_to('/dev/binderfs/'+name);print('PRIVATE_BINDER '+json.dumps({'name':name,'major':struct.unpack('256sII',request)[1],'minor':struct.unpack('256sII',request)[2]}),flush=True)
"""+s[end:];s=s.replace('ui-runtime-probe','android.hardware.graphics.composer@2.1-service').replace("'LD_LIBRARY_PATH':'/data'","'LD_LIBRARY_PATH':'/data','LD_PRELOAD':'/data/log-observer.so'");(exe/'launcher.py').write_text(s);(out/'native-launcher.py').write_text(s);print('PREPARED',flush=True)
