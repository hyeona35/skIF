from __future__ import annotations
import json, sqlite3, threading, time
from pathlib import Path
from typing import Any
from .event_schema import make_event, validate_event, SCHEMA_VERSION

class EventStore:
    """SQLite-backed event store with a stable interface for a future Postgres backend."""
    def __init__(self, path='data/events.db'):
        self.path=str(path); Path(self.path).parent.mkdir(parents=True,exist_ok=True); self._lock=threading.Lock(); self._subscribers=[]
        with self._connect() as db:
            db.execute('PRAGMA journal_mode=WAL')
            existing=[r[1] for r in db.execute('PRAGMA table_info(events)').fetchall()]
            if existing and 'event_id' not in existing:
                db.execute('ALTER TABLE events RENAME TO events_legacy')
            db.execute('CREATE TABLE IF NOT EXISTS events (id INTEGER PRIMARY KEY AUTOINCREMENT, event_id TEXT UNIQUE NOT NULL, ts REAL NOT NULL, schema_version TEXT NOT NULL, event_type TEXT NOT NULL, actor TEXT, actor_type TEXT NOT NULL, source TEXT NOT NULL, skill TEXT, run_id TEXT, correlation_id TEXT, idempotency_key TEXT, payload TEXT NOT NULL, signature TEXT)')
            if existing and 'event_id' not in existing:
                rows=db.execute('SELECT ts,event_type,actor,skill,run_id,payload FROM events_legacy ORDER BY id').fetchall()
                for ts,event_type,actor,skill,run_id,payload in rows:
                    try: pl=json.loads(payload or '{}')
                    except Exception: pl={'legacy_payload':payload}
                    ev=make_event(event_type,actor=actor or '',actor_type='agent',source='legacy',skill=skill or '',run_id=run_id or '',payload=pl,ts=ts)
                    db.execute('INSERT OR IGNORE INTO events(event_id,ts,schema_version,event_type,actor,actor_type,source,skill,run_id,correlation_id,idempotency_key,payload,signature) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(ev.event_id,ev.ts,ev.schema_version,ev.event_type,ev.actor,ev.actor_type,ev.source,ev.skill,ev.run_id,'','',self._dump(ev.payload),''))
            db.execute('CREATE INDEX IF NOT EXISTS v25_idx_events_ts ON events(ts)')
            db.execute('CREATE INDEX IF NOT EXISTS v25_idx_events_skill ON events(skill)')
            db.execute('CREATE INDEX IF NOT EXISTS v25_idx_events_actor ON events(actor)')
            db.execute('CREATE INDEX IF NOT EXISTS v25_idx_events_type_actor ON events(event_type,actor)')
            db.execute('CREATE UNIQUE INDEX IF NOT EXISTS v25_idx_events_idempotency ON events(idempotency_key) WHERE idempotency_key IS NOT NULL AND idempotency_key != ""')
            db.execute('CREATE TABLE IF NOT EXISTS jobs (id TEXT PRIMARY KEY, created_at REAL NOT NULL, updated_at REAL NOT NULL, kind TEXT NOT NULL, status TEXT NOT NULL, payload TEXT NOT NULL, result TEXT)')
            db.execute('CREATE INDEX IF NOT EXISTS v25_idx_jobs_status ON jobs(status)')
    def _connect(self):
        db=sqlite3.connect(self.path, timeout=30); db.execute('PRAGMA busy_timeout=30000'); return db
    @staticmethod
    def _dump(value: Any) -> str: return json.dumps(value,ensure_ascii=False,default=str)
    @staticmethod
    def _load(value: str | None) -> Any: return json.loads(value) if value else None
    def subscribe(self, callback):
        if callable(callback): self._subscribers.append(callback)
        return callback
    def emit(self,event_type,actor='',skill='',run_id='',payload=None,*,actor_type='agent',source='api',correlation_id='',idempotency_key='',event_id=None):
        event=make_event(event_type,actor=actor,actor_type=actor_type,source=source,skill=skill,run_id=run_id,correlation_id=correlation_id,idempotency_key=idempotency_key,payload=payload or {},event_id=event_id)
        row=event.to_dict()
        with self._lock, self._connect() as db:
            if idempotency_key:
                existing=db.execute('SELECT id,event_id,ts,schema_version,event_type,actor,actor_type,source,skill,run_id,correlation_id,idempotency_key,payload,signature FROM events WHERE idempotency_key=?',(idempotency_key,)).fetchone()
                if existing:
                    return self._row(existing)
            cur=db.execute('INSERT INTO events(event_id,ts,schema_version,event_type,actor,actor_type,source,skill,run_id,correlation_id,idempotency_key,payload,signature) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?)',(event.event_id,event.ts,event.schema_version,event.event_type,event.actor,event.actor_type,event.source,event.skill,event.run_id,event.correlation_id,event.idempotency_key,self._dump(event.payload),event.signature))
            row['id']=cur.lastrowid
        for callback in tuple(self._subscribers):
            try: callback(row)
            except Exception: pass
        return row
    def _row(self,r):
        return {'id':r[0],'event_id':r[1],'ts':r[2],'schema_version':r[3],'event_type':r[4],'actor':r[5],'actor_type':r[6],'source':r[7],'skill':r[8],'run_id':r[9],'correlation_id':r[10],'idempotency_key':r[11],'payload':self._load(r[12]),'signature':r[13]}
    def validate(self,event): return validate_event(event)
    def recent_by_actor(self, actor, limit=1000):
        with self._connect() as db:
            rows=db.execute('SELECT id,event_id,ts,schema_version,event_type,actor,actor_type,source,skill,run_id,correlation_id,idempotency_key,payload,signature FROM events WHERE actor=? ORDER BY id DESC LIMIT ?',(actor,int(limit))).fetchall()
        return [self._row(r) for r in rows]

    def recent(self,limit=200,skill=''):
        q='SELECT id,event_id,ts,schema_version,event_type,actor,actor_type,source,skill,run_id,correlation_id,idempotency_key,payload,signature FROM events'; args=[]
        if skill: q+=' WHERE skill=?'; args.append(skill)
        q+=' ORDER BY id DESC LIMIT ?'; args.append(int(limit))
        with self._connect() as db: rows=db.execute(q,args).fetchall()
        return [self._row(r) for r in rows]
    def health(self):
        with self._connect() as db:
            n=db.execute('SELECT COUNT(*) FROM events').fetchone()[0]
            jobs=db.execute('SELECT COUNT(*) FROM jobs').fetchone()[0]
        return {'events':n,'jobs':jobs,'schema_version':SCHEMA_VERSION,'path':self.path}

    def create_job(self,job_id,kind,payload):
        now=time.time()
        with self._lock, self._connect() as db:
            db.execute('INSERT INTO jobs(id,created_at,updated_at,kind,status,payload) VALUES(?,?,?,?,?,?)',(job_id,now,now,kind,'queued',self._dump(payload)))
    def update_job(self,job_id,status,result=None):
        with self._lock, self._connect() as db:
            db.execute('UPDATE jobs SET updated_at=?,status=?,result=? WHERE id=?',(time.time(),status,self._dump(result) if result is not None else None,job_id))
    def get_job(self,job_id):
        with self._connect() as db: r=db.execute('SELECT id,created_at,updated_at,kind,status,payload,result FROM jobs WHERE id=?',(job_id,)).fetchone()
        if not r:return None
        return {'id':r[0],'created_at':r[1],'updated_at':r[2],'kind':r[3],'status':r[4],'payload':self._load(r[5]),'result':self._load(r[6])}
    def recent_jobs(self,limit=100):
        with self._connect() as db: rows=db.execute('SELECT id,created_at,updated_at,kind,status,payload,result FROM jobs ORDER BY created_at DESC LIMIT ?',(int(limit),)).fetchall()
        return [{'id':r[0],'created_at':r[1],'updated_at':r[2],'kind':r[3],'status':r[4],'payload':self._load(r[5]),'result':self._load(r[6])} for r in rows]
