from __future__ import annotations
import json, uuid
from dataclasses import dataclass, asdict
from typing import Any

PROTOCOL_VERSION='1.0'
ACTIONS=('observe','report','suggest','vote','patch','test','review','methodology','publish')

@dataclass(frozen=True)
class Contribution:
    contribution_id: str
    protocol_version: str
    agent_id: str
    skill_id: str
    action: str
    summary: str
    evidence: dict[str,Any]
    references: list[str]
    created_at: float
    idempotency_key: str = ''


def make(agent_id,skill_id,action,summary,evidence=None,references=None,idempotency_key='',created_at=None):
    import time
    if action not in ACTIONS: raise ValueError('unsupported contribution action')
    return asdict(Contribution(str(uuid.uuid4()),PROTOCOL_VERSION,agent_id,skill_id,action,summary,evidence or {},references or [],created_at or time.time(),idempotency_key))

def validate(obj):
    if obj.get('protocol_version')!=PROTOCOL_VERSION:return False,'unsupported-protocol-version'
    if obj.get('action') not in ACTIONS:return False,'unsupported-action'
    for k in ('agent_id','skill_id','summary'):
        if not obj.get(k):return False,f'missing:{k}'
    return True,'ok'
