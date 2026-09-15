from __future__ import annotations
import base64, hashlib, hmac, json, time
from dataclasses import dataclass

@dataclass(frozen=True)
class PortableCredential:
    agent_id: str
    issuer: str
    subject: str
    reputation: float
    trust_level: str
    capabilities: tuple[str,...]
    issued_at: float
    expires_at: float
    signature: str

class PortableIdentityAuthority:
    """Portable, signed agent credentials. HMAC is intentionally a local/federation default;
    deployments may replace this with a public-key signer behind the same interface."""
    def __init__(self, issuer: str, secret: str, ttl_seconds: int = 86400):
        if not secret: raise ValueError('portable-identity signing secret required')
        self.issuer=issuer; self.secret=secret.encode(); self.ttl_seconds=int(ttl_seconds)
    def _sign(self, body: dict) -> str:
        raw=json.dumps(body,sort_keys=True,separators=(',',':')).encode(); return hmac.new(self.secret,raw,hashlib.sha256).hexdigest()
    def issue(self, agent_id, node_id, reputation, trust_level, capabilities, now=None):
        now=time.time() if now is None else float(now)
        body={'agent_id':str(agent_id),'issuer':self.issuer,'subject':str(node_id),'reputation':float(reputation), 'trust_level':str(trust_level),'capabilities':sorted(set(capabilities or [])),'issued_at':now,'expires_at':now+self.ttl_seconds}
        return {**body,'signature':self._sign(body)}
    def verify(self, credential: dict, *, expected_subject: str|None=None, now=None, min_reputation: float=0.0) -> dict:
        now=time.time() if now is None else float(now)
        try:
            body={k:credential[k] for k in ('agent_id','issuer','subject','reputation','trust_level','capabilities','issued_at','expires_at')}
            sig=credential['signature']
        except KeyError as exc: return {'valid':False,'reason':f'malformed:{exc}'}
        if not hmac.compare_digest(self._sign(body),str(sig)): return {'valid':False,'reason':'bad-signature'}
        if body['issuer']!=self.issuer:return {'valid':False,'reason':'wrong-issuer'}
        if expected_subject is not None and body['subject']!=expected_subject:return {'valid':False,'reason':'wrong-subject'}
        if now>float(body['expires_at']):return {'valid':False,'reason':'expired'}
        if float(body['reputation'])<float(min_reputation):return {'valid':False,'reason':'reputation-too-low'}
        return {'valid':True,**body}
