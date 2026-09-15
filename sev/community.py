from __future__ import annotations
from .eventstore import EventStore

EVENTS={'usage':'skill_usage','vote':'skill_vote','feedback':'skill_feedback','commit':'skill_commit','methodology':'methodology_shared'}

def record(store, skill, actor, kind, payload=None, run_id=''):
    et=EVENTS.get(kind,kind)
    return store.emit(et,actor=actor,skill=skill,run_id=run_id,payload=payload or {})

def contribution_summary(store, skill, limit=1000):
    rows=store.recent(limit,skill); counts={}
    for r in rows: counts[r['event_type']]=counts.get(r['event_type'],0)+1
    return {'skill':skill,'counts':counts,'contributors':sorted({r['actor'] for r in rows if r['actor']})}
