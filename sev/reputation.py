from __future__ import annotations
import hashlib, math, time
from dataclasses import dataclass, asdict
from typing import Any

POSITIVE = {
    'skill_usage': 0.1,
    'skill_feedback': 0.5,
    'skill_commit': 2.0,
    'methodology_shared': 1.0,
    'community_vote': 0.15,
    'error_reported': 0.3,
    'eval_contribution': 1.2,
    'research_result': 0.8,
}

@dataclass
class AgentProfile:
    agent_id: str
    installation_id: str = ''
    first_seen: float = 0.0
    last_seen: float = 0.0
    events: int = 0
    trusted: bool = False
    reputation: float = 0.5
    vote_weight: float = 0.25
    judge_weight: float = 0.25
    proposal_priority: float = 0.25
    research_budget: float = 0.25
    auto_approval: float = 0.0

class ReputationEngine:
    """Event-derived reputation with bounded influence and coarse Sybil resistance.

    This is an anti-abuse heuristic, not a cryptographic proof of personhood.
    Influence is bounded, fresh identities are damped, and repeated identical
    contributions within a short window are capped.
    """
    def __init__(self, store, freshness_halflife_days: float = 30.0, duplicate_window_seconds: int = 3600):
        self.store = store
        self.freshness_halflife_days = freshness_halflife_days
        self.duplicate_window_seconds = duplicate_window_seconds

    @staticmethod
    def _key(agent_id: str, installation_id: str = '') -> str:
        raw=f'{agent_id}\0{installation_id}'.encode()
        return hashlib.sha256(raw).hexdigest()[:20]

    def register(self, agent_id: str, installation_id: str = '', trusted: bool = False, metadata: dict[str, Any] | None = None):
        now=time.time()
        return self.store.emit('agent_registered',actor=agent_id,payload={
            'installation_id': installation_id, 'identity_key': self._key(agent_id,installation_id),
            'trusted': bool(trusted), 'metadata': metadata or {},
        })

    def _events(self, agent_id: str, limit: int = 5000):
        if hasattr(self.store,'recent_by_actor'): return self.store.recent_by_actor(agent_id,limit)
        return [e for e in self.store.recent(limit=limit) if e.get('actor') == agent_id]

    def _duplicate_factor(self, event, events):
        fp=(event.get('payload') or {}).get('request_fingerprint') or (event.get('payload') or {}).get('content_hash')
        if not fp: return 1.0
        cutoff=float(event.get('ts',0))-self.duplicate_window_seconds
        repeated=sum(1 for x in events if x.get('id')!=event.get('id') and x.get('ts',0)>=cutoff and ((x.get('payload') or {}).get('request_fingerprint') or (x.get('payload') or {}).get('content_hash'))==fp)
        return 1.0 / min(5, repeated+1)

    def score(self, agent_id: str) -> dict[str, Any]:
        events=self._events(agent_id); now=time.time()
        positive=0.0; negative=0.0; counts={}; metrics={'patch_acceptance':0.0,'regression_rate':0.0,'error_report_accuracy':0.0,'judge_calibration':0.0,'prediction_calibration':0.0,'methodology_usefulness':0.0,'false_positive_rate':0.0,'security_incidents':0.0}
        patch_total=patch_ok=reg_total=reg_bad=err_total=err_ok=judge_total=judge_ok=pred_total=pred_good=method_total=method_good=fp_total=fp_bad=0
        security=0
        latest=0.0
        for e in events:
            latest=max(latest,float(e.get('ts',0)))
            typ=e.get('event_type',''); counts[typ]=counts.get(typ,0)+1
            decay=math.exp(-max(0,now-float(e.get('ts',now)))/(self.freshness_halflife_days*86400))
            mult=self._duplicate_factor(e,events)*decay
            positive += POSITIVE.get(typ,0.0)*mult
            p=e.get('payload') or {}
            if typ in ('skill_commit','patch_result'):
                patch_total+=1; patch_ok+=int(bool(p.get('accepted') or p.get('merged') or p.get('promoted')))
                reg_total+=int('regressed' in p); reg_bad+=int(bool(p.get('regressed')))
            elif typ in ('error_review','error_reported'):
                err_total+=int('reviewed' in p or 'accurate' in p); err_ok+=int(bool(p.get('accurate') or p.get('accepted')))
            elif typ=='judge_calibration':
                a=p.get('accuracy');
                if isinstance(a,(int,float)): judge_total+=1; judge_ok += float(a)
            elif typ=='prediction_result':
                pred_total+=1; pred_good+=int(bool(p.get('calibrated') or p.get('correct')))
            elif typ in ('methodology_review','methodology_used'):
                method_total+=1; method_good+=int(bool(p.get('useful') or p.get('accepted')))
            elif typ in ('false_positive','false_positive_review'):
                fp_total+=1; fp_bad+=int(bool(p.get('confirmed_false_positive',True)))
            elif typ=='security_incident': security+=1; negative += 3.0*mult
            elif typ in ('review_rejected','proposal_rejected','patch_rejected'):
                negative += 0.5*mult
        base=1-math.exp(-positive/8.0)
        penalties=min(0.85, negative/8.0 + security*0.1)
        rep=max(0.0,min(1.0,0.5 + 0.5*base - penalties))
        age_days=(now-(latest or now))/86400.0
        freshness=min(1.0,math.exp(-age_days/30.0)) if latest else 0.15
        maturity=min(1.0, events.__len__()/25.0)
        diversity=min(1.0,len(counts)/8.0)
        # Sybil damping: fresh/low-diversity identities can contribute, but never dominate.
        influence=max(0.05,min(2.0,0.15 + 0.85*rep*(0.35+0.65*maturity)*(0.5+0.5*diversity)))
        trusted=any((e.get('payload') or {}).get('trusted') for e in events if e.get('event_type')=='agent_registered')
        if trusted: influence=min(2.0, influence*1.25)
        metrics.update({
            'patch_acceptance':patch_ok/patch_total if patch_total else 0.0,
            'regression_rate':reg_bad/reg_total if reg_total else 0.0,
            'error_report_accuracy':err_ok/err_total if err_total else 0.0,
            'judge_calibration':judge_ok/judge_total if judge_total else 0.0,
            'prediction_calibration':pred_good/pred_total if pred_total else 0.0,
            'methodology_usefulness':method_good/method_total if method_total else 0.0,
            'false_positive_rate':fp_bad/fp_total if fp_total else 0.0,
            'security_incidents':security,
        })
        return asdict(AgentProfile(agent_id=agent_id,first_seen=min([e['ts'] for e in events],default=0.0),last_seen=latest,events=len(events),trusted=trusted,reputation=rep,vote_weight=influence,judge_weight=influence,proposal_priority=influence,research_budget=influence*0.8,auto_approval=max(0.0,min(1.0,(rep-0.85)/0.15)))) | {'metrics':metrics,'event_counts':counts,'freshness':freshness,'maturity':maturity}

    def vote_weight(self, agent_id: str, cap: float = 2.0) -> float:
        return min(cap, max(0.05, float(self.score(agent_id)['vote_weight'])))

    def can_auto_approve(self, agent_id: str, threshold: float = 0.92) -> bool:
        s=self.score(agent_id); return bool(s['reputation']>=threshold and s['metrics']['regression_rate']<=0.02 and s['metrics']['security_incidents']==0)
