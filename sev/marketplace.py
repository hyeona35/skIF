from __future__ import annotations
import json, time, hashlib
from dataclasses import asdict, dataclass
from pathlib import Path

CERT_LEVELS = ("unrated", "bronze", "silver", "gold", "platinum")

@dataclass
class SkillRecord:
    skill_id: str
    name: str
    owner: str = ''
    maintainer: str = ''
    version: str = '0.0.0'
    description: str = ''
    dependencies: list[str] | None = None
    compatibility: dict | None = None
    score: float = 0.0
    cost: float = 0.0
    latency_ms: float = 0.0
    security_rating: float = 0.0
    reliability: float = 0.0
    methodologies: list[str] | None = None
    telemetry_health: float = 0.0
    certification: str = 'unrated'
    provenance: dict | None = None
    updated_at: float = 0.0

class Marketplace:
    def __init__(self, root='data/marketplace'):
        self.root=Path(root); self.root.mkdir(parents=True, exist_ok=True)
        self.path=self.root/'skills.jsonl'

    def _records(self):
        if not self.path.exists(): return []
        return [json.loads(x) for x in self.path.read_text().splitlines() if x.strip()]

    def publish(self, record: dict) -> dict:
        r=dict(record); r['updated_at']=time.time(); r.setdefault('publisher_trust','unknown'); r.setdefault('publisher_reputation',0.0); r.setdefault('provenance_status','unverified'); r.setdefault('dependencies',[]); r.setdefault('methodologies',[])
        r['skill_id']=r.get('skill_id') or hashlib.sha256(f"{r.get('owner','')}:{r.get('name','')}".encode()).hexdigest()[:16]
        r['certification']=r.get('certification','unrated')
        if r['certification'] not in CERT_LEVELS: raise ValueError('invalid certification')
        rows=[x for x in self._records() if x.get('skill_id')!=r['skill_id']]
        rows.append(r); self.path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows)); return r

    def search(self, query='', limit=20, certification=None, min_security=0.0):
        q=query.lower().strip(); rows=self._records(); out=[]
        for r in rows:
            if certification and r.get('certification')!=certification: continue
            if float(r.get('security_rating',0)) < float(min_security): continue
            hay=' '.join(str(r.get(k,'')) for k in ('name','description','owner','maintainer','skill_id')).lower()
            if q and q not in hay: continue
            out.append(r)
        out.sort(key=lambda x:(float(x.get('score',0)),float(x.get('reliability',0)),float(x.get('security_rating',0))), reverse=True)
        return out[:int(limit)]

    def score_runtime(self, record: dict) -> float:
        cert={'unrated':0.0,'bronze':0.25,'silver':0.5,'gold':0.75,'platinum':1.0}.get(record.get('certification','unrated'),0.0)
        security=float(record.get('security_rating',0)); reliability=float(record.get('reliability',0)); telemetry=float(record.get('telemetry_health',0))
        latency=max(0.0,float(record.get('latency_ms',0))); cost=max(0.0,float(record.get('cost',0)))
        return 0.35*float(record.get('score',0))+0.25*reliability+0.2*security+0.1*telemetry+0.1*cert-0.0002*latency-0.0001*cost

    def install_record(self, skill_id, agent_id, version=''):
        rows=self._records(); found=next((x for x in rows if x.get('skill_id')==skill_id),None)
        if not found: raise KeyError(skill_id)
        if version and found.get('version')!=version: raise ValueError('version unavailable')
        return {'installed':True,'skill_id':skill_id,'version':found.get('version'),'agent_id':agent_id,'certification':found.get('certification','unrated')}

    def certify(self, skill_id, metrics: dict) -> dict:
        def clamp(x): return max(0.0,min(1.0,float(x)))
        coverage=clamp(metrics.get('eval_coverage',0)); regression=clamp(1-float(metrics.get('regression_rate',1)))
        security=clamp(metrics.get('security',0)); shadow=clamp(metrics.get('shadow',0)); canary=clamp(metrics.get('canary',0)); response=clamp(metrics.get('maintainer_response',0)); telemetry=clamp(metrics.get('telemetry_health',0))
        points=(coverage+regression+security+shadow+canary+response+telemetry)/7
        level='platinum' if points>=0.95 and min(security,regression,shadow,canary)>=0.9 else 'gold' if points>=0.85 and min(security,regression)>=0.8 else 'silver' if points>=0.7 else 'bronze' if points>=0.5 else 'unrated'
        rows=self._records(); found=None
        for r in rows:
            if r.get('skill_id')==skill_id:
                r['certification']=level; r['certification_score']=points; r['certification_metrics']=metrics; r['updated_at']=time.time(); found=r; break
        if found is None: raise KeyError(skill_id)
        self.path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows)); return found
