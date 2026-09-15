from __future__ import annotations
from dataclasses import dataclass
import time

@dataclass
class ResourcePolicy:
    max_usd:float=10.0
    max_tokens:int=100000
    max_seconds:int=900
    max_concurrent:int=4
    max_federation_bytes:int=10_000_000
    max_research_loops:int=4

class ResourceGovernor:
    def __init__(self,policy=None): self.policy=policy or ResourcePolicy()
    def admit(self,estimate):
        reasons=[]
        if float(estimate.get('usd',0))>self.policy.max_usd:reasons.append('usd-budget')
        if int(estimate.get('tokens',0))>self.policy.max_tokens:reasons.append('token-budget')
        if float(estimate.get('seconds',0))>self.policy.max_seconds:reasons.append('time-budget')
        if int(estimate.get('concurrent',0))>self.policy.max_concurrent:reasons.append('concurrency-budget')
        if int(estimate.get('federation_bytes',0))>self.policy.max_federation_bytes:reasons.append('federation-budget')
        if int(estimate.get('research_loops',0))>self.policy.max_research_loops:reasons.append('research-budget')
        return {'allowed':not reasons,'reasons':reasons,'ts':time.time()}
