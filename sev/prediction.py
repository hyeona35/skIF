from __future__ import annotations
import json,time,uuid
from pathlib import Path

class PredictionMarket:
    """Optional forecast ledger. It never participates in trust unless explicitly enabled."""
    def __init__(self,path='data/predictions.jsonl'): self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
    def create(self,agent_id,subject,probability,deadline=None,evidence=None):
        p=max(0.0,min(1.0,float(probability))); row={'id':str(uuid.uuid4()),'agent_id':agent_id,'subject':subject,'probability':p,'deadline':deadline,'evidence':evidence or [],'created_at':time.time()}
        with self.path.open('a') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
        return row
    def resolve(self,prediction_id,outcome):
        rows=self._read(); target=None
        for r in rows:
            if r['id']==prediction_id: target=r; r['resolved']=bool(outcome); r['resolved_at']=time.time(); r['brier']=(r['probability']-(1.0 if outcome else 0.0))**2; break
        if not target: raise KeyError(prediction_id)
        self.path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows)); return target
    def _read(self):
        if not self.path.exists():return []
        return [json.loads(x) for x in self.path.read_text().splitlines() if x.strip()]
    def calibration(self,agent_id):
        rs=[x for x in self._read() if x.get('agent_id')==agent_id and 'brier' in x]
        return {'agent_id':agent_id,'count':len(rs),'brier':sum(x['brier'] for x in rs)/len(rs) if rs else None}
