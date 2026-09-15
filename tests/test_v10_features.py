import json
from pathlib import Path
from sev.graph import analyze
from sev.dataset import strengthen_suite
from sev.shadow import ShadowEngine, append_request, load_requests
from sev.providers import ProviderResult, Provider

class P:
    def __init__(self): self.config=type('C',(),{'name':'p','input_cost_per_million':1,'output_cost_per_million':1})()
    def generate(self,system,prompt):
        if 'evaluation dataset' in prompt:
            return ProviderResult(json.dumps({'prompt':'solve x','success_criteria':['answer'],'constraints':[],'mandatory':True}),{})
        return ProviderResult(json.dumps({'score':1,'passed':True,'reason':'ok'}),{})

def make_skill(root,name,requires=None):
    p=Path(root)/name; p.mkdir(); (p/'SKILL.md').write_text('# '+name); 
    if requires: (p/'skill.json').write_text(json.dumps({'name':name,'requires':requires}))
    return p

def test_dependency_graph_and_impact(tmp_path):
    a=make_skill(tmp_path,'A'); b=make_skill(tmp_path,'B',['A']); c=make_skill(tmp_path,'C',['B'])
    g=analyze(tmp_path,['A'])
    assert 'B' in g['impact']['A'] and 'C' in g['impact']['A']

def test_dataset_strengthening_preserves_suite_shape(tmp_path):
    suite=tmp_path/'suite.json'; suite.write_text(json.dumps({'cases':[]}))
    out=strengthen_suite([P()], [str(make_skill(tmp_path,'S'))], suite, 1)
    assert out['added']==1 and isinstance(json.loads(suite.read_text()),dict)

def test_shadow_request_record_and_mirror(tmp_path):
    store=tmp_path/'requests.jsonl'; append_request(store,{'prompt':'do x'})
    assert len(load_requests(store))==1
