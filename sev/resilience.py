from __future__ import annotations
import time, threading
from dataclasses import dataclass

@dataclass
class AgentGuardState:
    failures:int=0
    rate_events:int=0
    blocked_until:float=0.0
    last_event:float=0.0

class AgentGuard:
    """Per-agent rate/failure guard. It is deliberately conservative and fail-closed."""
    def __init__(self, max_events_per_minute=120, max_failures=5, block_seconds=300):
        self.max_events=max(1,int(max_events_per_minute)); self.max_failures=max(1,int(max_failures)); self.block_seconds=max(1,int(block_seconds)); self._lock=threading.Lock(); self._state={}
    def allow(self,agent_id):
        with self._lock:
            s=self._state.setdefault(agent_id,AgentGuardState()); now=time.time()
            if now-s.last_event>60: s.rate_events=0
            if s.blocked_until>now: return False
            if s.rate_events>=self.max_events: s.blocked_until=now+self.block_seconds; return False
            s.rate_events+=1; s.last_event=now; return True
    def record_failure(self,agent_id):
        with self._lock:
            s=self._state.setdefault(agent_id,AgentGuardState()); s.failures+=1
            if s.failures>=self.max_failures: s.blocked_until=time.time()+self.block_seconds
    def reset(self,agent_id):
        with self._lock: self._state.pop(agent_id,None)
    def status(self,agent_id):
        with self._lock:
            s=self._state.get(agent_id,AgentGuardState()); return {'agent_id':agent_id,'failures':s.failures,'rate_events':s.rate_events,'blocked':s.blocked_until>time.time(),'blocked_until':s.blocked_until}
