from pathlib import Path
import subprocess,zipfile,shutil,hashlib,json
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/statsd-inputs-1';out.mkdir(exist_ok=False);image=Path('/home/tv/.cache/archtv/aosp16-qpr2/artifact-selection/gsi-original/system.img');archive=out/'com.android.os.statsd.apex';commands=[]
def run(a):
 commands.append(list(map(str,a)));p=subprocess.run(a,capture_output=True,text=True,timeout=60);(out/'debugfs.log').open('a').write(p.stdout+p.stderr);p.check_returncode()
run(['debugfs','-R',f'dump /system/apex/{archive.name} {archive}',str(image)]);assert archive.exists()
with zipfile.ZipFile(archive) as z:
 payload=out/'payload.img';payload.write_bytes(z.read('apex_payload.img'));(out/'apex_manifest.pb').write_bytes(z.read('apex_manifest.pb'))
module=out/'com.android.os.statsd';module.mkdir();run(['debugfs','-R',f'rdump / {module}',str(payload)]);shutil.copytree(module,Path('/tmp/archtv-a16-native-root/apex/com.android.os.statsd'),symlinks=True)
files={str(p.relative_to(out)):{'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size} for p in out.rglob('*') if p.is_file() and not p.is_symlink()};(out/'provenance.json').write_text(json.dumps({'image_sha256':'c4989f703ac23bbd3bb3da2e33a3633d373bf763afcfcbed3cccc73d5049d656','commands':commands,'files':files,'scope':'Whole original StatsD APEX extracted unchanged; static dependency candidates only, statsd service not run, no signature verification'},indent=2)+'\n')
s=Path('/tmp/archtv-a16-probe-3.py').read_text().replace('native-probe-3','native-probe-4').replace("'/apex/com.android.conscrypt/lib64'","'/apex/com.android.conscrypt/lib64','/apex/com.android.os.statsd/lib64'")
Path('/tmp/archtv-a16-probe-4.py').write_text(s)
