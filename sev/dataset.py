from __future__ import annotations
import json, hashlib
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor
from .skill import snapshot
from .eval_guard import stage_case


def _case_id(text: str) -> str:
    return 'agent-seed-' + hashlib.sha256(text.encode()).hexdigest()[:12]

def _json(text):
    t=text.strip()
    if t.startswith('```'): t=t.split('\n',1)[1].rsplit('```',1)[0]
    return json.loads(t)

def generate_seed_cases(providers, skills: list[str], count_per_skill: int = 3) -> list[dict]:
    out=[]
    def one(pair):
        name, text, i = pair
        prompt = f'''You are constructing an evaluation dataset for a production Agent Skill.\nSkill: {name}\nSkill contents:\n{text}\nGenerate one realistic user request that this skill should solve, including success_criteria, constraints, mandatory, and adversarial_notes. Return ONLY JSON.'''
        p=providers[i % len(providers)]
        try:
            d=_json(p.generate('You create rigorous evaluation cases; never alter the skill itself.',prompt).text)
            d.setdefault('id',_case_id(name+str(i)+json.dumps(d,sort_keys=True)))
            d.setdefault('mandatory',True); d.setdefault('weight',1.0); d.setdefault('provenance',{'source':'skill-seed','skill':name})
            return d
        except Exception:
            return None
    jobs=[]
    for path in skills:
        snap=snapshot(Path(path)); text='\n\n'.join(v['content'] for v in snap['files'].values())
        name=Path(path).name
        jobs.extend((name,text,i) for i in range(count_per_skill))
    with ThreadPoolExecutor(max_workers=min(len(jobs), max(1,len(providers)))) as ex:
        out=[x for x in ex.map(one,jobs) if x]
    return out

def suite_case_count(suite_path):
    p=Path(suite_path)
    if not p.exists(): return 0
    try:
        raw=json.loads(p.read_text())
        return len(raw.get('cases',[])) if isinstance(raw,dict) else len(raw) if isinstance(raw,list) else 0
    except Exception:
        return 0

def strengthen_suite(providers, skill_paths, suite_path, count_per_skill=3):
    suite=Path(suite_path); suite.parent.mkdir(parents=True,exist_ok=True)
    raw={}
    if suite.exists():
        try: raw=json.loads(suite.read_text())
        except Exception: raw={}
    wrapper=isinstance(raw,dict)
    data=list(raw.get('cases',[])) if wrapper else (raw if isinstance(raw,list) else [])
    existing={x.get('id') for x in data if isinstance(x,dict)}
    added=0
    for case in generate_seed_cases(providers, skill_paths, count_per_skill):
        validation=stage_case(suite.parent/'..'/'registry' if False else suite.parent/'registry', case, source='auto-skill-seed')
        if validation['validation']['accepted'] and case.get('id') not in existing:
            data.append(case); existing.add(case['id']); added+=1
    payload={'cases':data} if wrapper else data
    suite.write_text(json.dumps(payload,indent=2,ensure_ascii=False))
    return {'added': added, 'count': len(data)}
