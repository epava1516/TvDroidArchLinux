from pathlib import Path
import struct,json,hashlib
r=Path('/home/tv/repositorio-principal');out=r/'dist/aosp16/property-native-execution-1';orders=[]
def decode(data):
 def words(offset,count):
  assert 0<=offset<=len(data) and offset+4*count<=len(data)
  return struct.unpack_from('<'+'I'*count,data,offset)
 def string(offset):
  assert 0<=offset<len(data);end=data.index(0,offset);return data[offset:end].decode()
 version,minimum,size,co,to,root=words(0,6);assert version==minimum==1 and size==len(data)
 def table(offset):return [string(p) for p in words(offset+4,words(offset,1)[0])]
 contexts,types=table(co),table(to);seen=set();prefix_orders={};count={'nodes':0,'prefixes':0,'exact':0}
 def entry(offset):
  no,nl,ci,ti=words(offset,4);name=string(no);assert len(name.encode())==nl
  return {'name':name,'context':None if ci==0xffffffff else contexts[ci],'type':None if ti==0xffffffff else types[ti]}
 def node(offset,path):
  assert offset not in seen;seen.add(offset);count['nodes']+=1
  eo,nc,ca,np,pa,ne,ea=words(offset,7);e=entry(eo);path=path+(e['name'],);prefixes=[entry(p) for p in words(pa,np)];exact=[entry(p) for p in words(ea,ne)];assert len({p['name'] for p in prefixes})==len(prefixes)
  prefix_orders['/'.join(path)]=prefixes;count['prefixes']+=np;count['exact']+=ne
  return {'entry':e,'prefixes':sorted(prefixes,key=lambda e:(-len(e['name']),e['name'])),'exact':exact,'children':[node(p,path) for p in words(ca,nc)]}
 tree=node(root,());return {'contexts':contexts,'types':types,'tree':tree},prefix_orders,count
host,ho,hc=decode((out/'data/property_info-host').read_bytes());native,no,nc=decode((out/'data/property_info').read_bytes());assert host==native and hc==nc
changed=[]
for path,items in ho.items():
 other=no[path]
 if items==other:continue
 assert [len(p['name']) for p in items]==[len(p['name']) for p in other]
 assert sorted(items,key=lambda p:p['name'])==sorted(other,key=lambda p:p['name'])
 changed.append({'node':path,'host_order':[p['name'] for p in items],'native_order':[p['name'] for p in other],'lengths':[len(p['name']) for p in items]})
result={'layout_source':'Original pinned property_info_parser.h and trie_serializer.cpp; read-only diagnostic decoder, not runtime implementation','complete_semantic_tree_equal_after_equal_length_prefix_order_normalization':True,'contexts_and_types_equal':True,'counts':hc,'changed_prefix_orders':changed,'canonical_tree_sha256':hashlib.sha256(json.dumps(host,sort_keys=True).encode()).hexdigest(),'reason':'Original serializer comparator sorts prefix matches by descending length only, no tie breaker. Distinct equal-length prefixes cannot both match one same input prefix. Metadata entries/contexts/types/children/exact order are identical after that normalization.','scope':'Proves this pair of generated artifacts have the same complete decoded tree content and only harmless tied prefix ordering at semantic level; not framework/property-service/SELinux or APK acceptance'}
(out/'layout-comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
