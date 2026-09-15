from __future__ import annotations
import hashlib, json, time
from .eventstore import EventStore

class Idempotency:
    def __init__(self,store:EventStore):self.store=store
    @staticmethod
    def key(value):return hashlib.sha256(str(value).encode()).hexdigest()
    def claim(self,key,scope='global',ttl=86400):
        with self.store._lock, self.store._connect() as db:
            now=time.time(); db.execute('CREATE TABLE IF NOT EXISTS idempotency (scope TEXT NOT NULL, key TEXT NOT NULL, created_at REAL NOT NULL, result TEXT, PRIMARY KEY(scope,key))')
            row=db.execute('SELECT created_at,result FROM idempotency WHERE scope=? AND key=?',(scope,key)).fetchone()
            if row and now-float(row[0])<ttl:return False, json.loads(row[1]) if row[1] else None
            db.execute('INSERT OR REPLACE INTO idempotency(scope,key,created_at,result) VALUES(?,?,?,?)',(scope,key,now,None)); return True,None
    def complete(self,key,result,scope='global'):
        with self.store._lock, self.store._connect() as db:db.execute('UPDATE idempotency SET result=? WHERE scope=? AND key=?',(json.dumps(result,ensure_ascii=False,default=str),scope,key))
