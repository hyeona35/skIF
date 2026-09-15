from __future__ import annotations
import tempfile
from pathlib import Path
from .agent import run_case
from .skill import snapshot

def discover_interactions(root, changed):
    root=Path(root); changed=set(changed); pairs=[]
    for p in root.iterdir() if root.exists() else []:
        if not p.is_dir() or not (p/"SKILL.md").exists() or p.name in changed: continue
        pairs.append(p)
    return pairs

def evaluate_cross_skill_compat(worker, critic, skill_dir, sibling_dirs, runtime=None, methodologies=None):
    rows=[]
    for sibling in sibling_dirs:
        with tempfile.TemporaryDirectory(prefix="skif-compat-") as td:
            merged=Path(td); (merged/Path(skill_dir).name).mkdir(); (merged/Path(sibling).name).mkdir()
            for src,dst in ((Path(skill_dir),merged/Path(skill_dir).name),(Path(sibling),merged/Path(sibling).name)):
                for f in src.rglob("*"):
                    if f.is_file() and ".git" not in f.parts:
                        d=dst/f.relative_to(src); d.parent.mkdir(parents=True,exist_ok=True); d.write_bytes(f.read_bytes())
            case={'id':f'compat:{Path(skill_dir).name}+{Path(sibling).name}','prompt':f'Validate interoperability between skills {Path(skill_dir).name} and {Path(sibling).name}. Use both Skill definitions in this workspace. Identify contract conflicts, overlapping responsibilities, and shared assumptions.','success_criteria':['no breaking contract conflict','clear interoperability'],'constraints':[],'mandatory':False}
            result=run_case(worker,critic,merged,'',case,runtime,methodologies)
            rows.append({'pair':case['id'],'score':result.score,'passed':result.passed,'reason':result.reason,'trace':result.trace})
    score=sum(x['score'] for x in rows)/len(rows) if rows else 1.0
    return {'pairs':rows,'score':score,'passed':all(x['passed'] for x in rows) if rows else True}
