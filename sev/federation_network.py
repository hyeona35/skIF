from __future__ import annotations
import json, time, uuid
from pathlib import Path
from .federation import SignedArtifact
from .trust_negotiation import TrustPolicy, negotiate

class FederationNetwork:
    def __init__(self, root='data/federation/network', origin='local', signer=None, policy=None):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True)
        self.origin=origin; self.signer=signer; self.policy=(policy or TrustPolicy()).normalize()
        self.nodes_path=self.root/'network.json'
    def _load(self): return json.loads(self.nodes_path.read_text()) if self.nodes_path.exists() else {}
    def _save(self,d): self.nodes_path.write_text(json.dumps(d,ensure_ascii=False,indent=2))
    def connect(self,node_id,url,remote_policy:dict,capabilities=None):
        rp=TrustPolicy(**remote_policy).normalize(); result=negotiate(self.policy,rp)
        if not result['compatible']: raise ValueError('trust-policy-incompatible')
        nodes=self._load(); row={'node_id':node_id,'url':url,'remote_policy':result['remote'],'effective_policy':result['effective'],'capabilities':capabilities or [],'status':'connected','last_sync':0.0}; nodes[str(node_id)]=row; self._save(nodes); return row|{'negotiation':result}
    def disconnect(self,node_id):
        nodes=self._load(); row=nodes.pop(str(node_id),None); self._save(nodes); return row
    def nodes(self): return list(self._load().values())
    def plan_sync(self,node_id,artifact_kinds=None):
        row=self._load().get(str(node_id));
        if not row: raise KeyError(node_id)
        return {'node_id':node_id,'artifact_kinds':artifact_kinds or ['skill','eval','methodology','benchmark','telemetry','provenance'],'requires':row['effective_policy'],'ready':row['status']=='connected'}
    def reputation(self,node_id,events=None):
        row=self._load().get(str(node_id))
        if not row: raise KeyError(node_id)
        ev=events or {}
        incidents=float(ev.get('security_incidents',0)); success=float(ev.get('successful_syncs',0)); failures=float(ev.get('failed_syncs',0))
        total=max(1,success+failures)
        score=max(0.0,min(1.0,0.5+0.5*(success/total)-0.2*incidents))
        return {'node_id':node_id,'reputation':score,'successful_syncs':success,'failed_syncs':failures,'security_incidents':incidents}

    def trusted_for(self,node_id,min_reputation=0.6):
        return self.reputation(node_id).get('reputation',0)>=float(min_reputation)

    def mark_sync(self,node_id,count=0):
        nodes=self._load(); nodes[str(node_id)]['last_sync']=time.time(); nodes[str(node_id)]['last_sync_count']=int(count); self._save(nodes); return nodes[str(node_id)]
