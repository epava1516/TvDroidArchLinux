#!/usr/bin/env python3
"""One result consumer per immutable run; queue receipt is not execution."""
import contextlib,fcntl,hashlib,json,os,subprocess,sys,uuid
from pathlib import Path
GATE=Path('/home/tv/.cache/archtv/completion-notifications.enabled')

def write(path, value):
    temp=path.with_suffix('.tmp')
    with temp.open('w') as f:
        json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(temp,path)
    fd=os.open(path.parent,os.O_RDONLY|os.O_DIRECTORY)
    try:os.fsync(fd)
    finally:os.close(fd)

@contextlib.contextmanager
def locked(manifest):
    manifest=Path(manifest).resolve();m=json.loads(manifest.read_text())
    assert str(uuid.UUID(m['id']))==m['id']
    assert Path(m['checkpoint']).resolve()==manifest.parent
    assert m['owner']==m['unit']
    with (manifest.parent/'completion.lock').open('a') as lock:
        if os.geteuid()==0:
            owner=manifest.parent.stat();os.fchown(lock.fileno(),owner.st_uid,owner.st_gid)
        fcntl.flock(lock,fcntl.LOCK_EX)
        yield manifest.parent,m

def consumer(cp,m):
    p=cp/'completion-consumer.json'
    if p.exists():
        c=json.loads(p.read_text());assert c['id']==m['id'];return c
    return {'id':m['id'],'state':'active','owner':m.get('active_owner','active:'+m['id'])}

def terminal(cp,m):
    """Persist the terminal outcome even when no message is needed."""
    p=cp/'completion-result.json'
    if p.exists():
        result=json.loads(p.read_text());assert result['id']==m['id'];return result
    status={k:os.environ.get(k) for k in ('SERVICE_RESULT','EXIT_CODE','EXIT_STATUS')}
    resultfile=cp/'result.json'
    data=json.loads(resultfile.read_text()) if resultfile.exists() else {}
    if status['SERVICE_RESULT'] is None and not isinstance(data.get('outer_exit'),int):return None
    outcome='runner exit '+str(data['outer_exit']) if 'outer_exit' in data else 'service '+str(status)
    result={'id':m['id'],'service':status,'outcome':outcome,'evidence':str(cp),'result_sha256':hashlib.sha256(resultfile.read_bytes()).hexdigest() if resultfile.exists() else None}
    write(p,result);return result

def transfer(manifest,owner,action):
    """Explicit consume, release to queue, or reclaim an unsent result."""
    with locked(manifest) as (cp,m):
        c=consumer(cp,m);assert c['owner']==owner,'different active owner'
        delivery=cp/'completion-delivery.json'
        sent=json.loads(delivery.read_text()) if delivery.exists() else {}
        if sent.get('state') in ('sending','queued','indeterminate'):
            raise RuntimeError('Delivery already attempted: reconcile queue before changing consumer')
        if action=='consume':
            assert c['state']=='active','active ownership must be reclaimed before processing'
            assert terminal(cp,m) is not None,'no terminal result'
            c.update(state='consumed',consumed_by=owner)
        elif action=='handoff':
            assert c['state']=='active','only unconsumed active owner can hand off'
            c.update(state='queue')
        elif action=='claim-active':
            assert c['state'] in ('active','queue'),'result already consumed'
            c.update(state='active')
        else:raise ValueError(action)
        write(cp/'completion-consumer.json',c);return c

def deliver(manifest,sender=None,enabled=None):
    with locked(manifest) as (cp,m):
        result=terminal(cp,m)
        if result is None:return {'state':'not-terminal'}
        c=consumer(cp,m);write(cp/'completion-consumer.json',c)
        state=cp/'completion-delivery.json'
        previous=json.loads(state.read_text()) if state.exists() else {}
        # A crash after sending began is ambiguous, never retry automatically.
        if previous.get('state') in ('sending','queued','indeterminate'):return previous
        if c['state']!='queue':
            record={'id':m['id'],'state':'consumed' if c['state']=='consumed' else 'active_owned','continuation':'not_requested','result':str(cp/'completion-result.json')}
            write(state,record);return record
        if not (GATE.is_file() if enabled is None else enabled):
            record={'id':m['id'],'state':'notifications_disabled','continuation':'not_requested','result':str(cp/'completion-result.json')}
            write(state,record);return record
        message=f"Finalizó {m['name']} · {m['id']}. Resultado: {result['outcome']}. Evidencias: {cp}. Reclamar y contrastar este resultado antes de retomar."
        record={'id':m['id'],'destination':m['thread'],'state':'sending','message':message,'continuation':'not_observed'}
        write(state,record)
        try:
            if sender is None:
                cmd=['/usr/bin/codex','--remote',m['remote'],'queue','--thread',m['thread'],'--message',message]
                if os.geteuid()==0:cmd=['runuser','-u','tv','--']+cmd
                completed=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
            else:completed=sender(message)
            record.update(state='queued' if completed.returncode==0 else 'indeterminate',exit=completed.returncode,stdout=completed.stdout,stderr=completed.stderr)
        except Exception as error:record.update(state='indeterminate',error=str(error))
        write(state,record);return record

if __name__=='__main__':
    if len(sys.argv)==2:print(json.dumps(deliver(sys.argv[1])))
    else:print(json.dumps(transfer(sys.argv[1],sys.argv[3],sys.argv[2])))
