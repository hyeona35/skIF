from __future__ import annotations
import json, time, uuid
from pathlib import Path
from .privacy import redact

PHASES=('observation','hypothesis','experiment','evaluation','replication','knowledge','skill','production','observation')

class ResearchOS:
    """Persistent autonomous research state machine. Each transition is explicit and auditable."""
    def __init__(self, event_store, root='data/research'):
        self.events=event_store; self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True); self.path=self.root/'experiments.jsonl'
    def create(self, observation, agent='researcher', skill=''):
        row={'research_id':str(uuid.uuid4()),'phase':'observation','created_at':time.time(),'agent':agent,'skill':skill,'observation':redact(observation)}
        self._append(row); self.events.emit('research_observation',actor=agent,skill=skill,payload=row); return row
    def transition(self,research_id,phase,data=None,agent='researcher'):
        if phase not in PHASES: raise ValueError('invalid research phase')
        rows=self._read(); matches=[r for r in rows if r.get('research_id')==research_id]
        if not matches: raise KeyError(research_id)
        current=matches[-1]
        expected=PHASES[(PHASES.index(current['phase'])+1)%len(PHASES)]
        if phase!=expected and not (current['phase']=='knowledge' and phase=='skill'):
            raise ValueError(f'invalid transition {current["phase"]}->{phase}; expected {expected}')
        row={**current,'phase':phase,'updated_at':time.time(),'data':redact(data or {})}; self._append(row); self.events.emit(f'research_{phase}',actor=agent,skill=current.get('skill',''),payload=row); return row
    def _read(self):
        if not self.path.exists():return []
        return [json.loads(x) for x in self.path.read_text().splitlines() if x.strip()]
    def _append(self,row):
        with self.path.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    def get(self,research_id):
        rows=[r for r in self._read() if r.get('research_id')==research_id]; return rows[-1] if rows else None
    def list(self,limit=100): return self._read()[-int(limit):]
