from __future__ import annotations
import threading, time, uuid
from concurrent.futures import ThreadPoolExecutor
from .eventstore import EventStore

_QUEUES={}; _LOCK=threading.Lock()

class TaskQueue:
    """Persistent queue with restart recovery metadata and handler registry."""
    def __init__(self, store: EventStore, workers=2, stale_after=300):
        self.store=store; self.workers=max(1,int(workers)); self.stale_after=max(10,int(stale_after)); self.pool=ThreadPoolExecutor(max_workers=self.workers,thread_name_prefix='skif-worker'); self._futures={}; self._handlers={}; self._lock=threading.RLock(); self.recover()
    def register(self,kind,fn): self._handlers[str(kind)]=fn
    def submit(self, kind, payload, fn=None, idempotency_key=''):
        if fn is None: fn=self._handlers.get(kind)
        if fn is None: raise ValueError(f'no handler for {kind}')
        if idempotency_key:
            existing=self.store.recent_jobs(1000)
            for row in existing:
                if row['payload'].get('_idempotency_key')==idempotency_key and row['kind']==kind and row['status'] in ('queued','running','completed'):
                    return {'job_id':row['id'],'status':row['status'],'kind':kind,'deduplicated':True}
        job_id=str(uuid.uuid4()); payload=dict(payload); payload['_idempotency_key']=idempotency_key
        self.store.create_job(job_id,kind,payload); self.store.emit('queue_job_created',actor='skIF',payload={'job_id':job_id,'kind':kind},idempotency_key=f'job:create:{job_id}')
        fut=self.pool.submit(self._run,job_id,fn,payload); self._futures[job_id]=fut
        return {'job_id':job_id,'status':'queued','kind':kind}
    def _run(self,job_id,fn,payload):
        self.store.update_job(job_id,'running')
        try:
            result=fn(payload); self.store.update_job(job_id,'completed',result=result); self.store.emit('queue_job_completed',actor='skIF',payload={'job_id':job_id}); return result
        except Exception as exc:
            self.store.update_job(job_id,'failed',result={'error':str(exc)}); self.store.emit('queue_job_failed',actor='skIF',payload={'job_id':job_id,'error':str(exc)}); return {'error':str(exc)}
    def status(self,job_id): return self.store.get_job(job_id)
    def recent(self,limit=100): return self.store.recent_jobs(limit)
    def recover(self):
        now=time.time(); recovered=[]
        for row in self.store.recent_jobs(1000):
            if row['status']=='running' and now-float(row['updated_at'])>self.stale_after:
                self.store.update_job(row['id'],'queued',result={'recovered':True,'previous_status':'running'})
                self.store.emit('queue_job_recovered',actor='skIF',payload={'job_id':row['id'],'from':'running'})
                recovered.append(row['id'])
            elif row['status']=='queued' and row['kind'] in self._handlers and row['id'] not in self._futures:
                self._futures[row['id']]=self.pool.submit(self._run,row['id'],self._handlers[row['kind']],row['payload'])
        return recovered
    def shutdown(self): self.pool.shutdown(wait=False,cancel_futures=True)

def get_queue(store_path,workers=2):
    key=str(store_path)
    with _LOCK:
        q=_QUEUES.get(key)
        if q is None:q=TaskQueue(EventStore(key),workers);_QUEUES[key]=q
        return q
