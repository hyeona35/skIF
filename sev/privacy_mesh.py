from __future__ import annotations
import hashlib,json,math,secrets
from .privacy import redact,TelemetryProtector

class PrivacyBudget:
    def __init__(self,epsilon=3.0): self.epsilon=float(epsilon)
    def consume(self,amount):
        amount=float(amount)
        if amount<0 or amount>self.epsilon: raise ValueError('privacy budget exceeded')
        self.epsilon-=amount; return self.epsilon

class SecureTelemetry:
    def __init__(self,protector=None,budget=None): self.protector=protector or TelemetryProtector(); self.budget=budget or PrivacyBudget()
    def aggregate(self,events,epsilon_cost=0.5):
        from .privacy import local_aggregate,differential_private_counts
        self.budget.consume(epsilon_cost); return differential_private_counts(local_aggregate([redact(e) for e in events]),epsilon=max(epsilon_cost,0.01))
    def selective_query(self,payload,fields,epsilon_cost=0.1):
        self.budget.consume(epsilon_cost); return self.protector.selective_disclosure(payload,fields)
    def digest(self,payload): return hashlib.sha256(json.dumps(redact(payload),sort_keys=True,ensure_ascii=False).encode()).hexdigest()
