from pathlib import Path
import re,json,hashlib,subprocess
r=Path('/home/tv/repositorio-principal');cache=Path('/home/tv/.cache/archtv/aosp16-qpr2/native-build-inputs');src=cache/'build-release/source/build/release';out=r/'dist/aosp16/propertyinit-execution-2';out.mkdir();(out/'data').mkdir();vendor=out/'vendor/etc/selinux';vendor.mkdir(parents=True);chain=[];inputs=[];seen=set()
def record(p):
 data=p.read_bytes();inputs.append({'path':str(p),'sha256':hashlib.sha256(data).hexdigest()});return data.decode()
def visit(name):
 assert name not in seen;seen.add(name);text=record(src/'release_configs'/(name+'.textproto'))
 for parent in re.findall(r'^inherits:\s*"([^"]+)"',text,re.M):visit(parent)
 chain.append(name)
visit('bp4a');value=None;trace=[]
for name in chain:
 p=src/'flag_values'/name/'RELEASE_BOARD_API_LEVEL.textproto'
 if p.exists():
  text=record(p);m=re.search(r'string_value:\s*"([0-9]+)"',text);assert m;value=m[1];trace.append({'release':name,'value':value})
assert value and re.fullmatch('[0-9]{6}',value)
config=record(cache/'make-core-config/config.mk');assert 'PLATFORM_SEPOLICY_VERSION := $(BOARD_API_LEVEL)' in config and 'BOARD_SEPOLICY_VERS := $(PLATFORM_SEPOLICY_VERSION)' in config
board=record(cache/'make-board-config/board_config.mk');assert 'BOARD_API_LEVEL := $(RELEASE_BOARD_API_LEVEL)' in board
bp=record(cache/'sepolicy/source/system/sepolicy/Android.bp');assert 'name: "plat_sepolicy_vers.txt",\n    version: "vendor",' in bp
rule=record(cache/'sepolicy/source/system/sepolicy/build/soong/sepolicy_vers.go');assert 'ver = ctx.DeviceConfig().BoardSepolicyVers()' in rule and 'Text("echo").Text(ver).Text(">").Output(out)' in rule
file=vendor/'plat_sepolicy_vers.txt';result=subprocess.run(['/usr/bin/echo',value],capture_output=True,check=True);file.write_bytes(result.stdout);assert file.read_bytes()==(value+'\n').encode();(out/'generation.json').write_text(json.dumps({'scope':'Source-derived BP4A platform profile diagnostic; not original vendor binary, hardware vendor parity or policy enforcement','release_chain':chain,'flag_trace':trace,'resolved_value':value,'original_rule':'sepolicy_vers version vendor -> BoardSepolicyVers; echo version','inputs':inputs,'generated_file':str(file),'sha256':hashlib.sha256(file.read_bytes()).hexdigest(),'open':'Source/GSI/product configuration parity, actual vendor interfaces/policy and SELinux mediation remain unproved'},indent=2)+'\n');print('source-profile generated',value)
