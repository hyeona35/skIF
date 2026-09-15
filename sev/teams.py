from __future__ import annotations
import time, uuid
from dataclasses import dataclass, field

@dataclass
class AgentMember:
    agent_id:str
    role:str
    weight:float=1.0
    capabilities:list[str]=field(default_factory=list)

class AgentTeam:
    def __init__(self, team_id=None, objective='', budget=100.0):
        self.team_id=team_id or str(uuid.uuid4()); self.objective=objective; self.budget=float(budget); self.members=[]; self.created_at=time.time()
    def add(self,agent_id,role,weight=1.0,capabilities=None):
        self.members.append(AgentMember(agent_id,role,float(weight),list(capabilities or []))); return self.members[-1].__dict__
    def plan(self,task,required_capabilities=None):
        req=set(required_capabilities or []); chosen=[]
        for m in sorted(self.members,key=lambda x:x.weight,reverse=True):
            if req and req.isdisjoint(m.capabilities): continue
            chosen.append(m.__dict__); req -= set(m.capabilities)
            if not req: break
        return {'team_id':self.team_id,'objective':task,'members':chosen,'unfilled_capabilities':sorted(req),'budget':self.budget}
    def assign(self,tasks,required_capabilities=None):
        plan=self.plan(tasks[0] if tasks else self.objective,required_capabilities)
        return {'team_id':self.team_id,'assignments':[{'task':t,'agent':plan['members'][i%len(plan['members'])]['agent_id']} for i,t in enumerate(tasks)] if plan['members'] else [],'plan':plan}
