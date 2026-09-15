from __future__ import annotations
from dataclasses import dataclass

LEVELS={'unrated':0,'bronze':1,'silver':2,'gold':3,'platinum':4}

@dataclass(frozen=True)
class TrustPolicy:
    security: str='silver'
    reliability: float=0.5
    require_signed: bool=True
    require_portable_identity: bool=True
    allowed_capabilities: tuple[str,...]=()
    def normalize(self):
        s=str(self.security).lower();
        if s not in LEVELS: raise ValueError('invalid security level')
        return TrustPolicy(s,float(self.reliability),bool(self.require_signed),bool(self.require_portable_identity),tuple(sorted(set(self.allowed_capabilities))))

def negotiate(local: TrustPolicy, remote: TrustPolicy) -> dict:
    a=local.normalize(); b=remote.normalize(); effective=TrustPolicy(
        security=max((a.security,b.security),key=lambda x:LEVELS[x]),
        reliability=max(a.reliability,b.reliability),
        require_signed=a.require_signed or b.require_signed,
        require_portable_identity=a.require_portable_identity or b.require_portable_identity,
        allowed_capabilities=tuple(sorted(set(a.allowed_capabilities)&set(b.allowed_capabilities))) if a.allowed_capabilities and b.allowed_capabilities else tuple(sorted(set(a.allowed_capabilities or b.allowed_capabilities))),
    ).normalize()
    compatible = LEVELS[effective.security] >= LEVELS[a.security] and LEVELS[effective.security] >= LEVELS[b.security]
    return {'compatible':compatible,'local':a.__dict__,'remote':b.__dict__,'effective':effective.__dict__}
