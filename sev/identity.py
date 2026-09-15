from __future__ import annotations
import hashlib, json, time, uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

CAPABILITIES = {'telemetry','vote','feedback','patch','evaluation','review','red_team','blue_team','methodology','federation','marketplace','admin'}
TRUST_LEVELS = ('unknown','observed','contributor','trusted','verified','maintainer','host')

@dataclass
class AgentIdentity:
    agent_id: str
    installation_id: str = ''
    public_key: str = ''
    display_name: str = ''
    capabilities: set[str] = field(default_factory=set)
    trust_level: str = 'unknown'
    created_at: float = 0.0
    last_seen: float = 0.0
    metadata: dict[str, Any] = field(default_factory=dict)

class IdentityStore:
    def __init__(self, path='data/identity.json'):
        self.path=Path(path); self.path.parent.mkdir(parents=True,exist_ok=True)
    def _load(self):
        if not self.path.exists(): return {}
        try:return json.loads(self.path.read_text())
        except Exception:return {}
    def _save(self,x):self.path.write_text(json.dumps(x,ensure_ascii=False,indent=2))
    @staticmethod
    def derive_id(installation_id, public_key=''):
        return hashlib.sha256(f'{installation_id}\0{public_key}'.encode()).hexdigest()[:32]
    def register(self, installation_id='', public_key='', display_name='', capabilities=None, metadata=None, requested_id=''):
        data=self._load(); aid=requested_id or self.derive_id(installation_id or str(uuid.uuid4()),public_key)
        now=time.time(); cur=data.get(aid)
        caps={c for c in (capabilities or []) if c in CAPABILITIES}
        row=AgentIdentity(aid,installation_id,public_key,display_name,caps,(cur or {}).get('trust_level','unknown'),(cur or {}).get('created_at',now),now,metadata or {})
        data[aid]=asdict(row); data[aid]['capabilities']=sorted(caps); self._save(data); return data[aid]
    def get(self,agent_id): return self._load().get(agent_id)
    def set_trust(self,agent_id,trust_level):
        if trust_level not in TRUST_LEVELS: raise ValueError('invalid trust level')
        data=self._load(); row=data.get(agent_id)
        if not row: raise KeyError(agent_id)
        row['trust_level']=trust_level; row['last_seen']=time.time(); self._save(data); return row
    def list(self): return list(self._load().values())
    def authorize(self,agent_id,capability):
        row=self.get(agent_id)
        return bool(row and (capability in row.get('capabilities',[]) or 'admin' in row.get('capabilities',[])))
