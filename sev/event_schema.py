from __future__ import annotations
import hashlib, json, time, uuid
from dataclasses import asdict, dataclass, field
from typing import Any

SCHEMA_VERSION = '1.0'
EVENT_TYPES = {
    'agent_registered','agent_capability_updated','skill_installed','skill_published','skill_proposed',
    'skill_commit','skill_vote','community_vote','methodology_shared','methodology_used','eval_contribution',
    'eval_proposed','eval_promoted','eval_deprecated','error_reported','error_review','judge_calibration',
    'prediction_result','false_positive_review','security_incident','security_scan','red_team_scan',
    'federation_node_registered','federation_heartbeat','federation_quarantine','federation_artifact_ingested',
    'telemetry','usage','evolution_requested','evolution_completed','shadow_request_recorded','shadow_completed',
    'canary_started','canary_stage','canary_rollback','promotion','rollback','deployment_lock','kill_switch_changed',
    'queue_job_created','queue_job_recovered','queue_job_completed','queue_job_failed','configuration_saved',
}

@dataclass(frozen=True)
class EventEnvelope:
    event_id: str
    ts: float
    schema_version: str
    event_type: str
    actor: str = ''
    actor_type: str = 'agent'
    source: str = 'api'
    skill: str = ''
    run_id: str = ''
    correlation_id: str = ''
    idempotency_key: str = ''
    payload: dict[str, Any] = field(default_factory=dict)
    signature: str = ''

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def fingerprint(payload: Any) -> str:
    raw = json.dumps(payload, sort_keys=True, ensure_ascii=False, default=str, separators=(',', ':')).encode()
    return hashlib.sha256(raw).hexdigest()


def make_event(event_type: str, *, actor: str = '', actor_type: str = 'agent', source: str = 'api', skill: str = '', run_id: str = '', correlation_id: str = '', idempotency_key: str = '', payload: dict[str, Any] | None = None, event_id: str | None = None, ts: float | None = None) -> EventEnvelope:
    # Extension events are permitted for forward compatibility; core contracts remain versioned.
    if not event_type or not isinstance(event_type,str):
        raise ValueError('event_type-required')
    return EventEnvelope(event_id or str(uuid.uuid4()), ts or time.time(), SCHEMA_VERSION, event_type, actor, actor_type, source, skill, run_id, correlation_id, idempotency_key, payload or {})


def validate_event(event: dict[str, Any]) -> tuple[bool, str]:
    required = ('event_id','ts','schema_version','event_type','actor_type','source','payload')
    missing = [k for k in required if k not in event]
    if missing: return False, f'missing:{",".join(missing)}'
    if event.get('schema_version') != SCHEMA_VERSION: return False, 'unsupported-schema-version'
    if not isinstance(event.get('event_type'),str) or not event.get('event_type'): return False, 'invalid-event-type'
    if not isinstance(event.get('payload'), dict): return False, 'payload-must-be-object'
    return True, 'ok'
