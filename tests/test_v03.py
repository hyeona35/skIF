import json, subprocess
from sev.config import FrameworkConfig, ProviderConfig, RoleConfig
from sev.evolution import EvolutionEngine
from sev.providers import ProviderResult

class FakeProvider:
    def __init__(self,name='fake'): self.config=type('C',(),{'name':name})()
    def generate(self, system, prompt):
        if 'Improver' in system:
            return ProviderResult(json.dumps({'files':[{'path':'SKILL.md','operation':'replace','content':'# Skill\nImproved behavior\n'}]}), {})
        if 'Judge' in system:
            return ProviderResult(json.dumps({'decision':'accept','candidate':0,'confidence':1.0,'reason':'better'}), {})
        if 'Critic' in system:
            score=1.0 if 'Improved behavior' in prompt else 0.5
            return ProviderResult(json.dumps({'score':score,'passed':True,'reason':'ok','failures':[]}), {})
        return ProviderResult('Agent output', {})

def test_git_tournament(tmp_path, monkeypatch):
    skill=tmp_path/'skill'; skill.mkdir(); (skill/'SKILL.md').write_text('# Skill\nBaseline\n')
    subprocess.run(['git','init'],cwd=skill,check=True,capture_output=True); subprocess.run(['git','add','.'],cwd=skill,check=True,capture_output=True); subprocess.run(['git','-c','user.name=Test','-c','user.email=test@example.com','commit','-m','baseline'],cwd=skill,check=True,capture_output=True)
    suite=tmp_path/'evals.json'; suite.write_text(json.dumps({'cases':[{'id':'basic','prompt':'do task','success_criteria':['good'],'mandatory':True}]}))
    c=FrameworkConfig(alternatives=1,require_human_approval_to_promote=False,use_git=True,create_worktrees=True,min_score_delta=0)
    f=FakeProvider(); c.providers['fake']=ProviderConfig('fake','custom','fake'); c.roles={r:RoleConfig(providers=['fake']) for r in ('worker','critic','improver','judge')}; monkeypatch.setattr('sev.evolution.role_providers',lambda config:{r:[f] for r in ('worker','critic','improver','judge')})
    engine=EvolutionEngine(c,tmp_path/'runs')
    result=engine.run(skill,suite,feedback={'severity':'low','finding':'improve'},promote=True,force_approval=True)
    assert result['accepted'] is True
    assert result['promoted'] is True
    assert 'Improved behavior' in (skill/'SKILL.md').read_text()
