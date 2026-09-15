from __future__ import annotations
import json, time, uuid
from .research_os import ResearchOS

class AutonomousResearchOrchestrator:
    """Agent Skill OS closed-loop coordinator.

    It never treats a single experiment as proof: evaluation and independent
    replication are explicit phases, and only replicated evidence can produce
    a knowledge/skill action recommendation.
    """
    def __init__(self, research_os, evaluator=None, replicator=None):
        self.research=research_os; self.evaluator=evaluator; self.replicator=replicator
    def create_loop(self, observation, agent='researcher', skill=''):
        row=self.research.create(observation,agent,skill)
        rid=row['research_id']
        hyp={'hypothesis': f"Address the observed issue: {json.dumps(observation,ensure_ascii=False)}", 'success_criteria':['improves measured outcome','does not introduce regression']}
        self.research.transition(rid,'hypothesis',hyp,agent)
        exp={'experiment_plan':'Create an isolated candidate change and evaluate it against the protected corpus.','isolation':'worktree-or-sandbox','replication_required':True}
        self.research.transition(rid,'experiment',exp,agent)
        result=self.evaluator(rid, observation) if self.evaluator else {'status':'planned','note':'attach an evaluator callback to execute the experiment'}
        self.research.transition(rid,'evaluation',result,agent)
        replica=self.replicator(rid,result) if self.replicator else {'status':'pending','require_independent_replication':True}
        self.research.transition(rid,'replication',replica,agent)
        replicated=bool(replica.get('passed') or replica.get('replicated'))
        knowledge={'replicated':replicated,'conclusion':'supported' if replicated else 'unproven','evidence':{'evaluation':result,'replication':replica}}
        self.research.transition(rid,'knowledge',knowledge,agent)
        if replicated:
            self.research.transition(rid,'skill',{'action':'eligible_for_skill_improvement','automatic_promotion':False},agent)
            self.research.transition(rid,'production',{'action':'eligible_for_shadow_or_canary','automatic_deploy':False},agent)
        return self.research.get(rid)
