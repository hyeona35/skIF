from __future__ import annotations
import sqlite3, time
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any

@dataclass(frozen=True)
class KGEdge:
    source: str
    relation: str
    target: str
    weight: float = 1.0
    metadata: dict[str, Any] | None = None

class KnowledgeGraph:
    def __init__(self, path='data/knowledge.db'):
        self.path=str(path); Path(self.path).parent.mkdir(parents=True,exist_ok=True)
        with self._db() as db:
            db.execute('PRAGMA journal_mode=WAL')
            db.execute('CREATE TABLE IF NOT EXISTS nodes (id TEXT PRIMARY KEY, kind TEXT NOT NULL, label TEXT NOT NULL, metadata TEXT NOT NULL, updated_at REAL NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS edges (source TEXT NOT NULL, relation TEXT NOT NULL, target TEXT NOT NULL, weight REAL NOT NULL, metadata TEXT NOT NULL, updated_at REAL NOT NULL, PRIMARY KEY(source,relation,target))')
            db.execute('CREATE INDEX IF NOT EXISTS idx_edges_target ON edges(target)')
            db.execute('CREATE INDEX IF NOT EXISTS idx_edges_relation ON edges(relation)')

    def _db(self): return sqlite3.connect(self.path,timeout=30)
    @staticmethod
    def _dump(v):
        import json; return json.dumps(v or {},ensure_ascii=False,default=str)
    @staticmethod
    def _load(v):
        import json; return json.loads(v) if v else {}
    def upsert_node(self,node_id,kind,label,metadata=None):
        now=time.time()
        with self._db() as db: db.execute('INSERT INTO nodes(id,kind,label,metadata,updated_at) VALUES(?,?,?,?,?) ON CONFLICT(id) DO UPDATE SET kind=excluded.kind,label=excluded.label,metadata=excluded.metadata,updated_at=excluded.updated_at',(node_id,kind,label,self._dump(metadata),now))
    def link(self, source, relation, target, weight=1.0, metadata=None):
        self.upsert_node(source,source.split(':',1)[0],source); self.upsert_node(target,target.split(':',1)[0],target)
        with self._db() as db: db.execute('INSERT INTO edges(source,relation,target,weight,metadata,updated_at) VALUES(?,?,?,?,?,?) ON CONFLICT(source,relation,target) DO UPDATE SET weight=excluded.weight,metadata=excluded.metadata,updated_at=excluded.updated_at',(source,relation,target,float(weight),self._dump(metadata),time.time()))
    def ingest_event(self,event: dict[str,Any]):
        typ=event.get('event_type',''); p=event.get('payload') or {}; actor=event.get('actor',''); skill=event.get('skill','')
        if skill: self.upsert_node(f'skill:{skill}','skill',skill,p)
        if actor: self.upsert_node(f'agent:{actor}','agent',actor)
        if actor and skill: self.link(f'agent:{actor}','contributed_to',f'skill:{skill}')
        mapping={'skill_usage':'used','skill_feedback':'suggested','skill_commit':'improved','methodology_shared':'shared_methodology','error_reported':'reported_error','skill_vote':'voted_on','community_vote':'voted_on','security_incident':'affected'}
        if actor and typ in mapping and skill: self.link(f'agent:{actor}',mapping[typ],f'skill:{skill}')
        for rel,key,kind in [('solved_by','methodology','methodology'),('tested_by','eval','eval'),('affected_by','error','error'),('improved_by','commit','commit'),('deployed_as','version','version')]:
            val=p.get(key) or p.get(f'{key}_id')
            if val and skill:
                target=f'{kind}:{val}'; self.link(f'skill:{skill}',rel,target,metadata={'event_type':typ})
        for dep in p.get('depends_on',[]) or []:
            self.link(f'skill:{skill}','depends_on',f'skill:{dep}')
    def bulk_ingest(self,events):
        for e in events: self.ingest_event(e)
    def graph(self,root: str | None=None):
        with self._db() as db:
            nodes=[{'id':r[0],'kind':r[1],'label':r[2],'metadata':self._load(r[3]),'updated_at':r[4]} for r in db.execute('SELECT id,kind,label,metadata,updated_at FROM nodes ORDER BY id').fetchall()]
            edges=[asdict(KGEdge(r[0],r[1],r[2],r[3],self._load(r[4]))) for r in db.execute('SELECT source,relation,target,weight,metadata FROM edges ORDER BY source,relation,target').fetchall()]
        if root: edges=[e for e in edges if e['source']==root or e['target']==root]
        return {'nodes':nodes,'edges':edges}
    def neighborhood(self,node_id,depth=2):
        current={node_id}; seen={node_id}
        for _ in range(max(0,int(depth))):
            nxt=set()
            with self._db() as db:
                q=tuple(current) or ('',)
                qs=','.join('?' for _ in q)
                for r in db.execute(f'SELECT source,target FROM edges WHERE source IN ({qs}) OR target IN ({qs})',q+q).fetchall(): nxt.update(r)
            nxt-=seen; seen|=nxt; current=nxt
        with self._db() as db:
            members=tuple(seen) or ('',)
            qs=','.join('?' for _ in members)
            rows=db.execute(f'SELECT id,kind,label,metadata,updated_at FROM nodes WHERE id IN ({qs})',members).fetchall()
            nodes=[{'id':r[0],'kind':r[1],'label':r[2],'metadata':self._load(r[3]),'updated_at':r[4]} for r in rows]
            edge_rows=db.execute(f'SELECT source,relation,target,weight,metadata FROM edges WHERE source IN ({qs}) AND target IN ({qs})',members+members).fetchall()
            edges=[asdict(KGEdge(r[0],r[1],r[2],r[3],self._load(r[4]))) for r in edge_rows]
        return {'node':node_id,'depth':depth,'members':sorted(seen),'graph':{'nodes':nodes,'edges':edges}}
    def explain_path(self, source, target, max_depth=5):
        from collections import deque
        q=deque([(source,[source])]); seen={source}
        with self._db() as db: edges=db.execute('SELECT source,relation,target FROM edges').fetchall()
        adj={}
        for a,r,b in edges: adj.setdefault(a,[]).append((b,r))
        while q:
            node,path=q.popleft()
            if node==target:
                return {'found':True,'path':path}
            if len(path)>max_depth: continue
            for nxt,rel in adj.get(node,[]):
                if nxt not in seen: seen.add(nxt); q.append((nxt,path+[rel,nxt]))
        return {'found':False,'path':[]}
