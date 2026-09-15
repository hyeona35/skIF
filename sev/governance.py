from __future__ import annotations
import time
from collections import defaultdict

class VoteGovernor:
    """Applies reputation weights, diversity caps, and duplicate-vote suppression."""
    def __init__(self, store, reputation, per_agent_skill_window=3600):
        self.store=store; self.reputation=reputation; self.window=per_agent_skill_window
    def decide(self, agent_id, skill, run_id, candidate, choice, confidence=0.0):
        now=time.time(); rows=self.store.recent(5000,skill)
        for r in rows:
            if r.get('event_type') not in ('community_vote','skill_vote'): continue
            if r.get('actor')!=agent_id: continue
            if r.get('run_id')!=run_id: continue
            if now-float(r.get('ts',now)) <= self.window:
                return {'accepted':False,'reason':'duplicate-vote-window','weight':0.0}
        weight=self.reputation.vote_weight(agent_id)
        # Fresh identities receive a capped influence; trusted identities can earn more through history.
        score=self.reputation.score(agent_id)
        cap=1.0 if score['events'] < 5 else 2.0
        return {'accepted':True,'weight':min(weight,cap),'reputation':score}

    def aggregate(self, skill, run_id):
        rows=[r for r in self.store.recent(5000,skill) if r.get('event_type')=='community_vote' and r.get('run_id')==run_id]
        totals=defaultdict(float)
        for r in rows:
            p=r.get('payload') or {}; c=p.get('candidate'); totals[str(c)] += float(p.get('weight',0.0))
        total=sum(totals.values()) or 1.0
        return {'run_id':run_id,'skill':skill,'scores':dict(totals),'shares':{k:v/total for k,v in totals.items()},'votes':len(rows)}
