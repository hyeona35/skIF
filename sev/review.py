from __future__ import annotations
import json, uuid, time
from pathlib import Path

class ReviewQueue:
    def __init__(self,root='data/registry/reviews'):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
    def enqueue(self,kind,payload,priority='normal',reason=''):
        row={'id':str(uuid.uuid4()),'created_at':time.time(),'kind':kind,'priority':priority,'reason':reason,'status':'pending','payload':payload}
        (self.root/f'{row["id"]}.json').write_text(json.dumps(row,indent=2,ensure_ascii=False)); return row
    def list(self,status=None):
        out=[]
        for p in sorted(self.root.glob('*.json')):
            try:
                x=json.loads(p.read_text())
                if status is None or x.get('status')==status: out.append(x)
            except Exception: pass
        return out
    def decide(self,ident,approved,actor='human',note=''):
        p=self.root/f'{ident}.json'
        if not p.exists(): raise ValueError('review item not found')
        x=json.loads(p.read_text()); x.update({'status':'approved' if approved else 'rejected','decided_at':time.time(),'actor':actor,'note':note}); p.write_text(json.dumps(x,indent=2,ensure_ascii=False)); return x
