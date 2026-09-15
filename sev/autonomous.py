from __future__ import annotations
import json, time, uuid
from pathlib import Path
from .registry import add_methodology, propose_skill

class AutonomousResearchLoop:
    def __init__(self, config, pools, event_store):
        self.config=config; self.pools=pools; self.events=event_store
    def run(self, skill_dir, suite_path=None, loops=None, auto_evolve=False):
        count=int(loops if loops is not None else self.config.autonomous_loops)
        out=[]; skill_text=Path(skill_dir).read_text(encoding='utf-8',errors='ignore') if Path(skill_dir).is_file() else ''
        if not skill_text:
            for p in sorted(Path(skill_dir).glob('**/*.md')):
                skill_text += '\n\n'+p.read_text(encoding='utf-8',errors='ignore')[:12000]
        for i in range(count):
            prompt=json.dumps({'skill':str(skill_dir),'context':skill_text[:30000],'objective':'Find one reproducible weakness, optimization, debugging insight, or missing test that could improve this Skill ecosystem. Return JSON with finding, evidence, recommended_action, methodology, and eval_case.'},ensure_ascii=False)
            provider=self.pools['reviewer'][i%len(self.pools['reviewer'])] if self.pools['reviewer'] else self.pools['improver'][i%len(self.pools['improver'])]
            try:
                text=provider.generate('You are the skIF autonomous research agent. Do not modify protected evaluation policy.',prompt).text
                t=text.strip(); t=t.split('\n',1)[1].rsplit('```',1)[0] if t.startswith('```') else t
                d=json.loads(t)
            except Exception as exc:
                d={'finding':'','recommended_action':'','methodology':'','eval_case':None,'error':str(exc)}
            row={'id':str(uuid.uuid4()),'loop':i+1,'created_at':time.time(),**d}
            if d.get('methodology'):
                m=add_methodology(self.config.registry_dir,f'Autonomous finding {i+1}',str(d['methodology']),provider.config.name,['autonomous-research'])
                row['methodology_id']=m['id']
            if d.get('proposed_skill'):
                row['skill_proposal']=propose_skill(self.config.registry_dir,d['proposed_skill'].get('name','Agent-proposed skill'),d['proposed_skill'].get('description',''),provider.config.name,d['proposed_skill'])
            self.events.emit('autonomous_research',actor=provider.config.name,skill=Path(skill_dir).name,payload=row)
            out.append(row)
        return {'loops':count,'results':out,'auto_evolve_requested':bool(auto_evolve)}
