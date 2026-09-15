from __future__ import annotations
import base64, hashlib, json, math, os, secrets, time
from collections import defaultdict
from cryptography.fernet import Fernet

SENSITIVE={'email','phone','ip','ip_address','authorization','cookie','api_key','password','token','session','customer_id','user_id','name','address','prompt'}

def redact(value):
    if isinstance(value,dict): return {k:('[REDACTED]' if k.lower() in SENSITIVE else redact(v)) for k,v in value.items()}
    if isinstance(value,list): return [redact(v) for v in value]
    return value

def local_aggregate(events, key='event_type'):
    counts=defaultdict(int)
    for e in events: counts[str(e.get(key,'unknown'))]+=1
    return dict(counts)

def laplace(scale: float):
    u=secrets.randbits(53)/(2**53)
    return -scale * (1 if u<0.5 else -1) * math.log(1-2*abs(u-0.5))

def differential_private_counts(counts, epsilon=1.0):
    eps=max(float(epsilon),1e-9); return {k:max(0,int(round(v+laplace(1/eps)))) for k,v in counts.items()}

class TelemetryProtector:
    def __init__(self, key: bytes|None=None):
        if key is None: key=Fernet.generate_key()
        self.fernet=Fernet(key)
    @classmethod
    def from_env(cls, env='SKIF_TELEMETRY_KEY'):
        raw=os.environ.get(env)
        if not raw:return cls()
        return cls(raw.encode())
    def encrypt(self,payload: dict) -> str: return self.fernet.encrypt(json.dumps(redact(payload),ensure_ascii=False).encode()).decode()
    def decrypt(self,token: str) -> dict: return json.loads(self.fernet.decrypt(token.encode()).decode())
    def selective_disclosure(self,payload: dict, fields):
        clean=redact(payload); return {k:clean[k] for k in fields if k in clean}
    def fingerprint(self,payload): return hashlib.sha256(json.dumps(redact(payload),sort_keys=True,ensure_ascii=False).encode()).hexdigest()
