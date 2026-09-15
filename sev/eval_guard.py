from __future__ import annotations
import re, hashlib, json
from pathlib import Path

POISON_PATTERNS=[
    r'ignore (the )?(evaluator|judge|rubric|previous instructions)',
    r'change (the )?(evaluation|eval) (criteria|rubric|dataset)',
    r'mark this (case|answer) as (pass|passing)',
    r'do not evaluate',
    r'grade yourself as',
    r'admin password|api[_ -]?key|secret|authorization: bearer',
]

def validate_case(case):
    text=json.dumps(case,ensure_ascii=False).lower()
    hits=[p for p in POISON_PATTERNS if re.search(p,text,re.I)]
    required=['id','prompt','success_criteria']
    missing=[x for x in required if not case.get(x)]
    return {'accepted':not hits and not missing,'poison_flags':hits,'missing':missing,'fingerprint':hashlib.sha256(text.encode()).hexdigest()[:16]}

def stage_case(registry_dir, case, source='agent'):
    v=validate_case(case)
    root=Path(registry_dir)/'eval-proposals'; root.mkdir(parents=True,exist_ok=True)
    ident=case.get('id') or v['fingerprint']
    p=root/f'{ident}.json'
    payload={'source':source,'validation':v,'case':case,'status':'proposed'}
    p.write_text(json.dumps(payload,indent=2,ensure_ascii=False))
    return payload
