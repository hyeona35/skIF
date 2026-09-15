from __future__ import annotations
import json, time, statistics, uuid
from pathlib import Path
from .agent import run_case
from .stats import paired_bootstrap
from .production import scrub, fingerprint_request

class ShadowEngine:
    """Mirror the same request corpus through baseline and candidate Skills."""
    def __init__(self, worker, evaluator, runtime=None):
        self.worker=worker; self.evaluator=evaluator; self.runtime=runtime
    def run(self, baseline_dir, candidate_dir, cases, methodology=None, mirror_id='', max_requests=None, min_requests=0, alpha=0.05, min_effect=0.0):
        rows=[]; seen=set(); limit=max_requests or len(cases)
        for case in cases[:limit]:
            case=scrub(case); fp=fingerprint_request(case)
            if fp in seen: continue
            seen.add(fp)
            b=run_case(self.worker,self.evaluator,baseline_dir,'',case,self.runtime,methodology)
            c=run_case(self.worker,self.evaluator,candidate_dir,'',case,self.runtime,methodology)
            rows.append({'case_id':case['id'],'baseline':b.__dict__,'candidate':c.__dict__,'score_delta':c.score-b.score,'passed_delta':int(c.passed)-int(b.passed)})
        bs=[x['baseline']['score'] for x in rows]; cs=[x['candidate']['score'] for x in rows]
        deltas=[x['score_delta'] for x in rows]
        stat=paired_bootstrap(deltas,alpha=alpha)
        return {'mirror_id':mirror_id or str(uuid.uuid4()),'cases':rows,
                'baseline_score':statistics.mean(bs) if bs else 0,'candidate_score':statistics.mean(cs) if cs else 0,
                'score_delta':(statistics.mean(cs)-statistics.mean(bs)) if bs and cs else 0,
                'baseline_pass_rate':statistics.mean([x['baseline']['passed'] for x in rows]) if rows else 0,
                'candidate_pass_rate':statistics.mean([x['candidate']['passed'] for x in rows]) if rows else 0,
                'n':len(rows),'statistics':stat.__dict__,'significant_improvement':stat.significance and stat.mean_delta>min_effect,
                'gate_passed': len(rows)>=min_requests and stat.mean_delta>=min_effect and stat.improvement_significant if min_requests else stat.improvement_significant}

def append_request(path, request):
    p=Path(path); p.parent.mkdir(parents=True,exist_ok=True)
    row={'id':request.get('id') or str(uuid.uuid4()),'ts':time.time(),**request}
    with p.open('a') as f: f.write(json.dumps(row,ensure_ascii=False)+'\n')
    return row

def load_requests(path, limit=1000):
    p=Path(path)
    if not p.exists(): return []
    rows=[]
    for line in p.read_text().splitlines()[-limit:]:
        try: rows.append(json.loads(line))
        except: pass
    return rows
