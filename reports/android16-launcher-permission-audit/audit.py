from pathlib import Path
import importlib.util,re,json,hashlib,collections
r=Path('/home/tv/repositorio-principal');d=r/'reports/android16-launcher-permission-audit';out=r/'dist/aosp16/launcher-permission-audit-1';spec=importlib.util.spec_from_file_location('builder',r/'tools/aosp/build_linux_policy.py');mod=importlib.util.module_from_spec(spec);spec.loader.exec_module(mod)
actor='archtv_launcher';pattern=re.compile(r'\(allow\s+(\S+)\s+(\S+)\s+\((\S+)\s+\(([^()]*)\)\)\)')
def scan(path):
 text=path.read_text();types=set(re.findall(r'^\(type (\S+)\)$',text,re.M));attrs={n:set() for n in re.findall(r'^\(typeattribute (\S+)\)$',text,re.M)}
 values=re.findall(r'^\(typeattributeset (\S+) \(([^()]*)\)\)$',text,re.M);assert len(values)==len(re.findall(r'^\(typeattributeset ',text,re.M))
 for name,members in values:attrs[name].update(members.split())
 def members(name,seen=None):
  if name in types:return {name}
  seen=set() if seen is None else seen
  if name not in attrs or name in seen:raise ValueError('Unknown/cyclic type set '+name)
  result=set()
  for v in attrs[name]:result.update(members(v,seen|{name}))
  return result
 rules=[];incoming=[];extended=[];all_rules=0;all_extended=0;unsupported=[];containers={};forms=mod.forms(text)
 for number,form in enumerate(forms):
  parsed=list(pattern.finditer(form));all_rules+=len(parsed)
  assert len(parsed)==len(re.findall(r'\(allow\s',form)),('Unparsed AV rule',number)
  conditional=mod.keyword(form)=='booleanif'
  for match in parsed:
   src,target,cls,perms=match.groups()
   sources=members(src)
   targets=sources if target=='self' else members(target)
   if actor not in sources and actor not in targets:continue
   meta={'source_expression':src,'target_expression':target,'class':cls,'permissions':perms.split(),'conditional':conditional,'container_kind':mod.keyword(form),'container_sha256':hashlib.sha256(form.encode()).hexdigest(),'source_form_index':number}
   if conditional:containers[str(number)]={'sha256':meta['container_sha256'],'form':form}
   if actor in sources:rules.append({**meta,'targets':[actor] if target=='self' else sorted(targets)})
   if actor in targets:incoming.append({**meta,'sources':[actor] if target=='self' else sorted(sources)})
  xrules=list(re.finditer(r'\(allowx\s+(\S+)\s+(\S+)\s+',form));assert len(xrules)==len(re.findall(r'\(allowx\s',form)),('Unparsed extended rule',number);all_extended+=len(xrules)
  for x in xrules:
   src,target=x.groups();sources=members(src);targets=sources if target=='self' else members(target)
   if actor in sources or actor in targets:extended.append({'source':src,'target':target,'actor_source':actor in sources,'actor_target':actor in targets,'container_kind':mod.keyword(form),'source_form_index':number,'container_sha256':hashlib.sha256(form.encode()).hexdigest(),'form':form})
  if re.search(r'\((allowx|typetransition|typechange|typemember|typebounds)\s',form):
   if actor in form.split():unsupported.append({'kind':mod.keyword(form),'form_index':number,'sha256':hashlib.sha256(form.encode()).hexdigest()})
 return {'path':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),'all_AV_rules_parsed':all_rules,'all_extended_rules_parsed':all_extended,'actor_rules':rules,'non_AV_actor_declarations':unsupported,'incoming_rules':incoming,'actor_extended_rules':extended,'conditional_containers':containers,'attrs':attrs}
j=scan(out/'entry.cil');rows=j.pop('actor_rules');incoming=j.pop('incoming_rules');extended=j.pop('actor_extended_rules');containers=j.pop('conditional_containers');j.pop('attrs');perms=collections.defaultdict(set);targets=set();conditional=sum(x['conditional'] for x in rows)
for row in rows:perms[row['class']].update(row['permissions']);targets.update(row['targets'])
record={'scope':'Complete syntactic potential standard-AV allow coverage for new actor in original binary export, including conditional branches. NOT effective permissions; constraints, boolean values, extended permissions, bounds, DAC/caps/other LSM and actual labels are separate. No policy evaluator reimplemented.','export':j,'actor':actor,'matching_rules':len(rows),'conditional_rules':conditional,'target_type_count':len(targets),'class_permission_union':{k:sorted(v) for k,v in sorted(perms.items())},'rules':rows,'incoming_potential_rules':incoming,'extended_actor_rules':extended,'conditional_containers':containers};(d/'actor-potential-allows.json').write_text(json.dumps(record,indent=2)+'\n');print(json.dumps({k:record[k] for k in ['matching_rules','conditional_rules','target_type_count']},indent=2))
# Full statement delta is evidence, not equivalence; preserve exact strings locally
# and publish hashes/counts plus only changed AV rules that name concrete actors.
before=collections.Counter((out/'base.cil').read_text().splitlines());after=collections.Counter((out/'entry.cil').read_text().splitlines());added=list((after-before).elements());removed=list((before-after).elements());(out/'statement-delta.json').write_text(json.dumps({'added':added,'removed':removed},indent=2)+'\n');(d/'statement-delta-index.json').write_text(json.dumps({'scope':'Full syntactic statement delta, not effective AV equivalence','path':str(out/'statement-delta.json'),'sha256':hashlib.sha256((out/'statement-delta.json').read_bytes()).hexdigest(),'added':len(added),'removed':len(removed),'actor_standard_AV_rules':len(rows),'conditional_actor_rules':conditional},indent=2)+'\n')
