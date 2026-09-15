import json, subprocess
from pathlib import Path
from sev.config import FrameworkConfig, ProviderConfig, RoleConfig
from sev.providers import ProviderResult
from sev.runtime import SubprocessRuntime
from sev.errors import report_error, recent_errors, review_signal
from sev.registry import propose_skill
from sev.skill_proposals import review_and_materialize

class P:
    def __init__(self,name='p'): self.config=type('C',(),{'name':name,'input_cost_per_million':1,'output_cost_per_million':2})()
    def generate(self,system,prompt):
        if 'Reviewer' in system: return ProviderResult(json.dumps({'approved':True,'reason':'ok'}),{})
        if 'Judge' in system: return ProviderResult(json.dumps({'approved':True,'confidence':1}),{})
        return ProviderResult('ok',{})

def test_subprocess_runtime_collects_trajectory(tmp_path):
    rt=SubprocessRuntime("python -c \"import json; print(json.dumps({\'output\':\'ok\',\'tool_calls\':[{\'name\':\'shell\',\'arguments\':{\'cmd\':\'echo hi\'},\'result\':\'hi\'}]}))\"")
    t=rt.run(tmp_path,{'prompt':'x'})
    assert t.output=='ok' and t.tool_calls[0].name=='shell'

def test_error_threshold_and_delta(tmp_path):
    for _ in range(6): report_error(tmp_path,'s','boom')
    e=recent_errors(tmp_path,'s',60); assert review_signal(e,5,.5)['review']

def test_skill_proposal_materializes(tmp_path):
    c=FrameworkConfig(); c.voting_enabled=True; c.proposals.vote_threshold=.5
    c.registry_dir=str(tmp_path)
    c.providers['p']=ProviderConfig('p','custom','x')
    c.roles['reviewer']=RoleConfig(['p']); c.roles['judge']=RoleConfig(['p'])
    prop=propose_skill(tmp_path,'Cool Skill','desc',payload={'files':{'SKILL.md':'# Cool'}})
    out=review_and_materialize(c,prop['id'],tmp_path,[P('r')],[P('j')])
    assert out['accepted'] and (Path(out['materialized_path'])/'SKILL.md').exists()

def test_vote_can_be_disabled_and_custom_compat_persists(tmp_path, monkeypatch):
    from sev.config import save_config, load_config
    c=FrameworkConfig(voting_enabled=False)
    c.providers['custom']=ProviderConfig('custom','custom','m',api_key_env='CUSTOM_KEY',endpoint='http://example.invalid',api_compat='anthropic')
    monkeypatch.setattr('sev.config.CONFIG_PATH',tmp_path/'config.json')
    save_config(c); d=load_config()
    assert d.voting_enabled is False and d.providers['custom'].api_compat=='anthropic'
