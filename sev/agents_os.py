from __future__ import annotations
from .teams import AgentTeam
from .router import SkillRouter

class AgentOS:
    """Machine-friendly facade over core ecosystem operations."""
    def __init__(self,reputation,marketplace,mesh,resource_governor):
        self.reputation=reputation; self.marketplace=marketplace; self.mesh=mesh; self.resources=resource_governor
    def recommend(self,task,environment=None,agent_id=''):
        return SkillRouter(self.marketplace,self.reputation).rank(task,environment,agent_id)[:5]
    def team(self,objective,budget=100): return AgentTeam(objective=objective,budget=budget)
