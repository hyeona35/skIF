from __future__ import annotations
import json
from pathlib import Path

def load_suite(path): return json.loads(Path(path).read_text())['cases']

def append_case(path,case):
    p=Path(path); raw=json.loads(p.read_text()) if p.exists() else {'cases':[]}; raw.setdefault('cases',[])
    if not any(x.get('id')==case['id'] for x in raw['cases']): raw['cases'].append(case); p.write_text(json.dumps(raw,indent=2,ensure_ascii=False))


def stage_generated_case(registry_dir,case,source='agent'):
    from .eval_guard import stage_case
    return stage_case(registry_dir,case,source)
