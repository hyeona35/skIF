from __future__ import annotations
import json, statistics, time
from pathlib import Path
from .cache import TTLCache

class BenchmarkStore:
    def __init__(self,path='data/benchmarks.jsonl',cache=None):self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True);self.cache=cache or TTLCache(10)
    def record(self,subject,corpus_id,score,pass_rate=0.0,cost=0.0,latency_ms=0.0,metadata=None):
        row={'subject':subject,'corpus_id':corpus_id,'score':float(score),'pass_rate':float(pass_rate),'cost':float(cost),'latency_ms':float(latency_ms),'metadata':metadata or {},'ts':time.time()}
        with self.path.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
        self.cache.invalidate('leader:'); return row
    def list(self,corpus_id=''):
        if not self.path.exists():return []
        out=[]
        for line in self.path.read_text().splitlines():
            try:
                r=json.loads(line)
                if not corpus_id or r.get('corpus_id')==corpus_id:out.append(r)
            except Exception:pass
        return out
    def leaderboard(self,corpus_id=''):
        return self.cache.get_or_set(f'leader:{corpus_id}',lambda: sorted(self.list(corpus_id),key=lambda x:(-x['score'],-x['pass_rate'],x['cost'],x['latency_ms']))[:100])
