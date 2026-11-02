#!/usr/bin/env python3
"""One run-bound notification attempt; queue acknowledgment is not continuation."""
import fcntl,json,os,subprocess,sys,uuid
from pathlib import Path

def write(path, value):
    temp=path.with_suffix('.tmp')
    with temp.open('w') as f:
        json.dump(value,f,indent=2);f.write('\n');f.flush();os.fsync(f.fileno())
    os.replace(temp,path)

def deliver(manifest, sender=None):
    manifest=Path(manifest).resolve();m=json.loads(manifest.read_text())
    assert str(uuid.UUID(m['id']))==m['id']
    assert Path(m['checkpoint']).resolve()==manifest.parent
    assert m['owner']==m['unit']
    state=manifest.parent/'completion-delivery.json'
    with (manifest.parent/'completion.lock').open('a') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX)
        # Includes sending left by crash: never retry an ambiguous attempt.
        if state.exists():return json.loads(state.read_text())
        result=manifest.parent/'result.json'
        status={k:os.environ.get(k) for k in ('SERVICE_RESULT','EXIT_CODE','EXIT_STATUS')}
        if status['SERVICE_RESULT'] is None:return {'state':'not-terminal'}
        if result.exists():
            data=json.loads(result.read_text());outcome='runner exit '+str(data.get('outer_exit','unknown'))
        else:outcome='service '+str(status)
        message=f"Finalizó {m['name']} · {m['id']}. Resultado: {outcome}. Evidencias: {manifest.parent}. Contrastar Git y resultado antes de retomar."
        record={'id':m['id'],'destination':m['thread'],'state':'sending','service':status,'message':message,'continuation':'not_observed'}
        write(state,record)
        try:
            if sender is None:
                cmd=['/usr/bin/codex','--remote',m['remote'],'queue','--thread',m['thread'],'--message',message]
                if os.geteuid()==0:cmd=['runuser','-u','tv','--']+cmd
                completed=subprocess.run(cmd,capture_output=True,text=True,timeout=30)
            else:completed=sender(message)
            record.update(state='queued' if completed.returncode==0 else 'indeterminate',exit=completed.returncode,stdout=completed.stdout,stderr=completed.stderr)
        except Exception as error:record.update(state='indeterminate',error=str(error))
        write(state,record)
        return record

if __name__=='__main__':deliver(sys.argv[1])
