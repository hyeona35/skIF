from __future__ import annotations
import json, sqlite3, time, hashlib
from pathlib import Path
from collections import deque

class KnowledgeMesh:
    """Federated, provenance-aware knowledge graph with local/remote visibility."""
    def __init__(self, path='data/knowledge_mesh.db'):
        self.db_path=str(path); Path(self.db_path).parent.mkdir(parents=True,exist_ok=True)
        with self._db() as db:
            db.execute('CREATE TABLE IF NOT EXISTS nodes(id TEXT PRIMARY KEY, kind TEXT NOT NULL, visibility TEXT NOT NULL, origin TEXT NOT NULL, payload TEXT NOT NULL, ts REAL NOT NULL)')
            db.execute('CREATE TABLE IF NOT EXISTS edges(src TEXT NOT NULL, relation TEXT NOT NULL, dst TEXT NOT NULL, origin TEXT NOT NULL, confidence REAL NOT NULL DEFAULT 0, ts REAL NOT NULL, PRIMARY KEY(src,relation,dst,origin))')
            db.execute('CREATE INDEX IF NOT EXISTS idx_mesh_kind ON nodes(kind)')
            db.execute('CREATE INDEX IF NOT EXISTS idx_mesh_origin ON nodes(origin)')
            db.execute('CREATE INDEX IF NOT EXISTS idx_mesh_src ON edges(src)')
            db.execute('CREATE INDEX IF NOT EXISTS idx_mesh_dst ON edges(dst)')
    def _db(self):
        db=sqlite3.connect(self.db_path,timeout=30); db.execute('PRAGMA journal_mode=WAL'); db.execute('PRAGMA busy_timeout=30000'); return db
    def put_node(self,node_id,kind,payload,visibility='community',origin='local'):
        if visibility not in ('private','community','federation','public'): raise ValueError('invalid visibility')
        clean=dict(payload or {}); clean.pop('secret',None); clean.pop('token',None); clean.pop('api_key',None)
        with self._db() as db: db.execute('INSERT OR REPLACE INTO nodes VALUES(?,?,?,?,?,?)',(node_id,kind,visibility,origin,json.dumps(clean,ensure_ascii=False),time.time()))
        return self.node(node_id)
    def put_edge(self,src,relation,dst,origin='local',confidence=1.0):
        with self._db() as db: db.execute('INSERT OR REPLACE INTO edges VALUES(?,?,?,?,?,?)',(src,relation,dst,origin,float(confidence),time.time()))
        return {'src':src,'relation':relation,'dst':dst,'origin':origin,'confidence':float(confidence)}
    def node(self,node_id):
        with self._db() as db:r=db.execute('SELECT id,kind,visibility,origin,payload,ts FROM nodes WHERE id=?',(node_id,)).fetchone()
        if not r:return None
        return {'id':r[0],'kind':r[1],'visibility':r[2],'origin':r[3],'payload':json.loads(r[4]),'ts':r[5]}
    def query(self,kind=None,origin=None,visibility=None,visibilities=None,limit=200):
        q='SELECT id,kind,visibility,origin,payload,ts FROM nodes WHERE 1=1'; args=[]
        for col,val in (('kind',kind),('origin',origin)):
            if val:q+=f' AND {col}=?';args.append(val)
        if visibility:
            q+=' AND visibility=?';args.append(visibility)
        elif visibilities:
            vals=tuple(sorted(set(visibilities)))
            if vals:
                q+=' AND visibility IN ('+','.join('?' for _ in vals)+')';args.extend(vals)
        q+=' ORDER BY ts DESC LIMIT ?';args.append(int(limit))
        with self._db() as db:rows=db.execute(q,args).fetchall()
        return [{'id':r[0],'kind':r[1],'visibility':r[2],'origin':r[3],'payload':json.loads(r[4]),'ts':r[5]} for r in rows]
    def neighborhood(self,start,depth=2,visibility='community',visibilities=None):
        allowed=set(visibilities or ([visibility] if visibility and visibility!='community' else ['community','federation','public']))
        seen={start}; q=deque([(start,0)]); nodes=[]; edges=[]
        while q:
            cur,d=q.popleft()
            n=self.node(cur)
            if not n or n['visibility'] not in allowed:
                if d==0: return {'start':start,'nodes':[],'edges':[]}
                continue
            nodes.append(n)
            if d>=int(depth):continue
            with self._db() as db:
                rs=db.execute('SELECT src,relation,dst,origin,confidence FROM edges WHERE src=? OR dst=?',(cur,cur)).fetchall()
            for src,rel,dst,org,conf in rs:
                other=dst if src==cur else src
                other_node=self.node(other)
                if not other_node or other_node['visibility'] not in allowed:
                    continue
                edges.append({'src':src,'relation':rel,'dst':dst,'origin':org,'confidence':conf})
                if other not in seen:seen.add(other);q.append((other,d+1))
        return {'start':start,'nodes':nodes,'edges':edges}
    def path(self,source,target,max_depth=8,visibilities=None):
        allowed=set(visibilities or ('community','federation','public'))
        src_node=self.node(source); dst_node=self.node(target)
        if not src_node or not dst_node or src_node['visibility'] not in allowed or dst_node['visibility'] not in allowed:
            return None
        q=deque([(source,[])]);seen={source}
        while q:
            cur,p=q.popleft()
            if cur==target:return p
            with self._db() as db:rs=db.execute('SELECT relation,dst,confidence FROM edges WHERE src=?',(cur,)).fetchall()
            for rel,dst,conf in rs:
                node=self.node(dst)
                if not node or node['visibility'] not in allowed: continue
                if dst not in seen and len(p)<max_depth:
                    seen.add(dst);q.append((dst,p+[{'from':cur,'relation':rel,'to':dst,'confidence':conf}]))
        return None
    def export_bundle(self,visibility='federation',origin='local'):
        nodes=self.query(visibility=visibility); ids={x['id'] for x in nodes};
        with self._db() as db: rs=db.execute('SELECT src,relation,dst,origin,confidence,ts FROM edges').fetchall()
        edges=[{'src':a,'relation':b,'dst':c,'origin':d,'confidence':e,'ts':f} for a,b,c,d,e,f in rs if a in ids and c in ids]
        bundle={'version':'1','origin':origin,'nodes':nodes,'edges':edges,'digest':hashlib.sha256(json.dumps({'nodes':nodes,'edges':edges},sort_keys=True).encode()).hexdigest()}
        return bundle
    def import_bundle(self,bundle,trusted_origins=None):
        origin=str(bundle.get('origin',''))
        if trusted_origins is not None and origin not in set(trusted_origins): raise PermissionError('untrusted mesh origin')
        nodes=list(bundle.get('nodes',[])); edges=list(bundle.get('edges',[]))
        expected=str(bundle.get('digest',''))
        if not expected: raise ValueError('mesh-bundle-digest-required')
        canonical={'nodes':nodes,'edges':edges}
        actual=hashlib.sha256(json.dumps(canonical,sort_keys=True).encode()).hexdigest()
        if not hmac_compare(actual,expected): raise ValueError('mesh-bundle-digest-mismatch')
        for n in nodes:self.put_node(n['id'],n['kind'],n.get('payload',{}),n.get('visibility','federation'),origin)
        for e in edges:self.put_edge(e['src'],e['relation'],e['dst'],origin,e.get('confidence',0))
        return {'imported_nodes':len(nodes),'imported_edges':len(edges),'origin':origin,'digest_verified':True}

def hmac_compare(a,b):
    import hmac
    return hmac.compare_digest(str(a),str(b))
