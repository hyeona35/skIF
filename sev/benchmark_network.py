from __future__ import annotations
import hashlib,json,time
from pathlib import Path

class GlobalBenchmarkNetwork:
    def __init__(self,path='data/global_benchmarks.jsonl'):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
    def publish(self,origin,rows,signature=''):
        bundle={'origin':origin,'rows':rows,'signature':signature,'ts':time.time()}
        bundle['digest']=hashlib.sha256(json.dumps({'origin':origin,'rows':rows},sort_keys=True).encode()).hexdigest()
        with self.path.open('a',encoding='utf-8') as f:f.write(json.dumps(bundle,ensure_ascii=False)+'\n')
        return bundle
    def list(self,origin=None):
        if not self.path.exists():return []
        out=[]
        for line in self.path.read_text().splitlines():
            try:
                x=json.loads(line)
                if not origin or x.get('origin')==origin:out.append(x)
            except Exception:pass
        return out
    def leaderboard(self,subject=None):
        rows=[]
        for b in self.list():
            for r in b.get('rows',[]):
                if subject and r.get('subject')!=subject:continue
                rows.append({**r,'origin':b.get('origin')})
        return sorted(rows,key=lambda x:(-float(x.get('score',0)),-float(x.get('pass_rate',0)),float(x.get('cost',0)),float(x.get('latency_ms',0))))[:500]
