from pathlib import Path
import shutil
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-service-effect-audit'
cases={
'quoted-import':{
 'main.rc':'import /data/profiles/imported.rc\nservice audit.declared /system/bin/false\n    user system\n    disabled\n    reboot_on_failure reboot\n    onrestart setprop persist.audit.text "value with spaces"\non property:audit.trigger=1\n    setprop persist.audit.expansion "${audit.source:-fallback value}"\n',
 'imported.rc':'service audit.imported /system/bin/getprop ro.build.version.sdk\n    user system\n    oneshot\n'},
'bad-option':{'main.rc':'service audit.invalid /system/bin/false\n    user system\n    unsupported_linux_option yes\n'},
'override':{'main.rc':'service audit.overridden /system/bin/false\n    user system\n    onrestart setprop audit.old value\nservice audit.overridden /system/bin/getprop ro.build.version.sdk\n    user shell\n    override\n    onrestart setprop audit.new value\n'}}
for name,files in cases.items():
 out=r/('dist/aosp16/service-effect-audit-'+name+'-1');out.mkdir();(out/'data/profiles').mkdir(parents=True);(out/'app').mkdir();shutil.copytree(r/'dist/aosp16/propertyinit-execution-2/vendor',out/'vendor');shutil.copy2(r/'dist/aosp16/service-effect-audit-build-2/audit-service-profiles',out/'data/audit-service-profiles')
 for filename,text in files.items():
  (out/'data/profiles'/filename).write_text(text);fixture=d/'fixtures'/name/filename;fixture.parent.mkdir(parents=True,exist_ok=True);fixture.write_text(text)
 s=(d/'launcher-canonical-final.py').read_text().replace('service-effect-audit-canonical-2','service-effect-audit-'+name+'-1');i=s.index("os.execve('/data/audit-service-profiles'");s=s[:i]+"os.execve('/data/audit-service-profiles',['/data/audit-service-profiles','/data/profiles/main.rc'],{'ANDROID_ROOT':'/system','ANDROID_DATA':'/data'})\n";(out/'launcher.py').write_text(s);(d/('launcher-'+name+'.py')).write_text(s)
