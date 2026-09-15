from __future__ import annotations
import json
from pathlib import Path
from .prompts import JUDGE_SYSTEM,REVIEWER_SYSTEM
from .registry import list_skill_proposals

def _json(t):
 t=t.strip()
 if t.startswith('```'): t=t.split('\n',1)[1].rsplit('```',1)[0]
 return json.loads(t)

def review_and_materialize(config, proposal_id, registry_root, reviewers, judges):
    proposals=list_skill_proposals(registry_root); p=next((x for x in proposals if x.get('id')==proposal_id),None)
    if not p: raise ValueError('Unknown skill proposal')
    payload=p.get('payload',{}); rubric=json.dumps({'name':p.get('name'),'description':p.get('description'),'payload':payload},ensure_ascii=False)
    reviews=[]
    for r in reviewers:
        try: reviews.append({'agent':r.config.name,**_json(r.generate(REVIEWER_SYSTEM,rubric).text)})
        except Exception as e: reviews.append({'agent':r.config.name,'approved':False,'reason':str(e)})
    votes=[]
    if config.voting_enabled:
        for j in judges:
            try: votes.append({'agent':j.config.name,**_json(j.generate(JUDGE_SYSTEM,rubric).text)})
            except Exception as e: votes.append({'agent':j.config.name,'approved':False,'confidence':0,'reason':str(e)})
    approved_review=any(bool(x.get('approved')) for x in reviews) if reviews else False
    weighted=sum(float(x.get('confidence',1) or 0) for x in votes if x.get('approved'))
    total=sum(float(x.get('confidence',1) or 0) for x in votes) or 1
    approved_vote=bool(votes) and weighted/total>=config.proposals.vote_threshold
    accepted=approved_vote if config.voting_enabled and votes else approved_review
    out={'proposal_id':proposal_id,'accepted':accepted,'reviews':reviews,'votes':votes,'vote_share':weighted/total if votes else 0}
    if not accepted: return out
    root=Path(registry_root)/'materialized' / str(p.get('name','skill')).lower().replace(' ','-')
    root.mkdir(parents=True,exist_ok=True)
    files=payload.get('files',{})
    if not files and payload.get('skill_md'): files={'SKILL.md':payload['skill_md']}
    for rel,content in files.items():
        rp=Path(rel)
        if rp.is_absolute() or '..' in rp.parts: raise ValueError('unsafe proposal path')
        dest=root/rp; dest.parent.mkdir(parents=True,exist_ok=True); dest.write_text(str(content))
    p['status']='materialized'; p['materialized_path']=str(root); (Path(registry_root)/'skills'/f"proposal-{proposal_id}.json").write_text(json.dumps(p,indent=2,ensure_ascii=False))
    out['materialized_path']=str(root); return out
