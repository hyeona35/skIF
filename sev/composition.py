from __future__ import annotations
import hashlib, json, time
from pathlib import Path

def compose(skill_dirs, output, methodologies=None):
    dirs=[Path(x) for x in skill_dirs]; out=Path(output); out.mkdir(parents=True,exist_ok=True)
    sections=[]; deps=[]
    for d in dirs:
        skill=d/'SKILL.md';
        if not skill.exists(): raise FileNotFoundError(skill)
        sections.append(f'## Composite component: {d.name}\n\n'+skill.read_text(encoding='utf-8'))
        deps.append(d.name)
    if methodologies: sections.append('## Shared methodologies\n\n'+'\n\n'.join(map(str,methodologies)))
    body='# Composite Skill\n\n'+ '\n\n'.join(sections)
    (out/'SKILL.md').write_text(body,encoding='utf-8')
    manifest={'name':out.name,'version':'0.1.0','requires':deps,'composed_at':time.time()}
    (out/'skill.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    return {'path':str(out),'requires':deps,'sha256':hashlib.sha256(body.encode()).hexdigest()}

def fork(skill_dir, target, branch_name):
    src=Path(skill_dir); dst=Path(target); dst.mkdir(parents=True,exist_ok=True)
    for p in src.rglob('*'):
        rel=p.relative_to(src); q=dst/rel
        if p.is_dir(): q.mkdir(parents=True,exist_ok=True)
        else: q.write_bytes(p.read_bytes())
    manifest=dst/'skill.json'; data=json.loads(manifest.read_text()) if manifest.exists() else {'name':dst.name}
    data['fork_of']=str(src); data['branch']=branch_name; data['forked_at']=time.time(); manifest.write_text(json.dumps(data,ensure_ascii=False,indent=2))
    return {'path':str(dst),'fork_of':str(src),'branch':branch_name}

def merge(skill_a, skill_b, target, methodology=None): return compose([skill_a,skill_b],target,[methodology] if methodology else [])
