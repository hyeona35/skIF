from __future__ import annotations
import json
from dataclasses import dataclass
from .providers import Provider
from .runtime import AgentRuntime,ProviderRuntime

@dataclass
class AgentCaseResult:
    case_id:str; output:str; score:float; passed:bool; reason:str; failures:list[str]; usage:dict; trace:dict; journal:dict

def _json(text):
    t=text.strip()
    if t.startswith('```'): t=t.split('\n',1)[1].rsplit('```',1)[0]
    return json.loads(t)

def _usage(provider,usage):
    u=dict(usage or {}); inp=int(u.get('input_tokens',u.get('prompt_tokens',0)) or 0); out=int(u.get('output_tokens',u.get('completion_tokens',0)) or 0)
    u['input_tokens']=inp; u['output_tokens']=out; u['total_tokens']=int(u.get('total_tokens',inp+out) or inp+out)
    u['estimated_cost_usd']=inp/1_000_000*float(getattr(provider.config,'input_cost_per_million',0))+out/1_000_000*float(getattr(provider.config,'output_cost_per_million',0))
    return u

def run_case(worker:Provider,evaluator:Provider,skill_dir,skill_text,case,runtime:AgentRuntime|None=None,methodologies=None):
    runtime=runtime or ProviderRuntime()
    trace=runtime.run(skill_dir,case,worker,methodologies)
    ep=json.dumps({'task':case['prompt'],'criteria':case.get('success_criteria',[]),'constraints':case.get('constraints',[]),'agent_response':trace.output,'tool_trace':[x.__dict__ for x in trace.tool_calls],'events':trace.events,'methodologies':methodologies or []},ensure_ascii=False)
    try: d=_json(evaluator.generate('You are the skIF Critic. Return ONLY JSON. Also return evidence, checks, confidence, and risk_flags.',ep).text)
    except Exception as e: d={'score':0,'passed':False,'reason':f'invalid evaluator: {e}','failures':['invalid evaluator output']}
    journal={'reason':str(d.get('reason','')),'evidence':d.get('evidence',[]),'checks':d.get('checks',[]),'confidence':float(d.get('confidence',0) or 0),'risk_flags':d.get('risk_flags',[])}
    wu=_usage(worker,trace.usage); eu=_usage(evaluator,{})
    usage={'input_tokens':wu['input_tokens']+eu['input_tokens'],'output_tokens':wu['output_tokens']+eu['output_tokens'],'total_tokens':wu['total_tokens']+eu['total_tokens'],'estimated_cost_usd':wu['estimated_cost_usd']+eu['estimated_cost_usd']}
    return AgentCaseResult(case['id'],trace.output,float(d.get('score',0)),bool(d.get('passed',False)),str(d.get('reason','')),list(d.get('failures',[])),usage,{'worker_provider':worker.config.name,'critic_provider':evaluator.config.name,'tool_calls':[x.__dict__ for x in trace.tool_calls],'events':trace.events},journal)

def evaluate_skill(worker,evaluators,skill_dir,skill_text,cases,runtime=None,trials=1,methodologies=None):
    results=[]
    for case in cases[:]:
        allr=[run_case(worker,evaluators[0],skill_dir,skill_text,case,runtime,methodologies) for _ in range(max(1,trials))]
        results.append({'id':case['id'],'score':sum(x.score for x in allr)/len(allr),'passed':all(x.passed for x in allr),'trials':[x.__dict__ for x in allr],'mandatory':case.get('mandatory',True)})
    total=sum(float(c.get('weight',1)) for c in cases[:len(results)]) or 1
    score=sum(r['score']*float(next(c.get('weight',1) for c in cases if c['id']==r['id'])) for r in results)/total
    usage={'input_tokens':0,'output_tokens':0,'total_tokens':0,'estimated_cost_usd':0.0}
    for r in results:
        for t in r['trials']:
            u=t.get('usage',{}) or {}
            for k in usage: usage[k]+=float(u.get(k,0) or 0)
    return {'score':score,'mandatory_failures':sum(1 for r in results if r['mandatory'] and not r['passed']),'cases':results,'usage':usage}
