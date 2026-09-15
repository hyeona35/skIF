from __future__ import annotations
import hashlib,time

class DecisionLedger:
    def __init__(self,store): self.store=store
    def record(self,decision,subject,evidence=None,policy=None,actors=None,confidence=0.0):
        row={'decision':decision,'subject':subject,'evidence':evidence or [],'policy':policy or {},'actors':actors or [],'confidence':float(confidence),'ts':time.time()}
        row['decision_id']=hashlib.sha256(repr(sorted(row.items())).encode()).hexdigest()[:20]
        return self.store.emit('governance_decision',actor='skIF',actor_type='system',source='governance',payload=row,idempotency_key='decision:'+row['decision_id'])
    def explain(self,event):
        return {'decision_id':event.get('payload',{}).get('decision_id'),'why':event.get('payload',{}).get('decision'),'evidence':event.get('payload',{}).get('evidence',[]),'policy':event.get('payload',{}).get('policy',{}),'actors':event.get('payload',{}).get('actors',[]),'confidence':event.get('payload',{}).get('confidence',0.0)}
