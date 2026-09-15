from __future__ import annotations
import math

class SkillRouter:
    """Selects Skills using compatibility, reliability, cost and latency signals."""
    def __init__(self, marketplace, reputation=None): self.marketplace=marketplace; self.reputation=reputation
    def rank(self,task,environment=None,agent_id=''):
        env=environment or {}; rows=self.marketplace.search(task,100)
        ranked=[]
        for r in rows:
            compat=r.get('compatibility') or {}; score=float(r.get('score',0)); rel=float(r.get('reliability',0)); sec=float(r.get('security_rating',0)); cost=float(r.get('cost',0)); lat=float(r.get('latency_ms',0))
            env_ok=sum(1 for k,v in env.items() if compat.get(k)==v)
            value=0.5*score+0.25*rel+0.15*sec+0.1*min(1,env_ok/max(1,len(env))) - 0.0001*cost - 0.0005*lat
            ranked.append({**r,'router_score':value})
        return sorted(ranked,key=lambda x:x['router_score'],reverse=True)
    def select(self,*args,**kwargs):
        rows=self.rank(*args,**kwargs); return rows[0] if rows else None
