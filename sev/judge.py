from __future__ import annotations
import json, statistics
from .evals import load_suite

def _json(t):
    t=t.strip()
    if t.startswith('```'): t=t.split('\n',1)[1].rsplit('```',1)[0]
    return json.loads(t)

def calibrate_judges(judges, gold_cases, min_score=0.75):
    results=[]
    for j in judges:
        hits=0; rows=[]
        for case in gold_cases:
            expected=case.get('expected_decision',case.get('expected_pass',True))
            try:
                prompt=json.dumps({'case':case,'instruction':'Return ONLY JSON: {"passed":true|false,"confidence":0..1,"reason":"..."}. Solve and judge this gold case.'},ensure_ascii=False)
                d=_json(j.generate('You are being calibrated on trusted gold cases.',prompt).text)
                passed=bool(d.get('passed',False))
                hit=passed==bool(expected); hits+=int(hit); rows.append({'id':case.get('id'),'hit':hit,'response':d})
            except Exception as exc: rows.append({'id':case.get('id'),'hit':False,'error':str(exc)})
        acc=hits/len(gold_cases) if gold_cases else 0.0
        results.append({'judge':j.config.name,'accuracy':acc,'eligible':acc>=min_score,'cases':rows})
    return {'results':results,'eligible_judges':[x['judge'] for x in results if x['eligible']], 'mean_accuracy':statistics.mean([x['accuracy'] for x in results]) if results else 0.0}
