from __future__ import annotations
import json
from .prompts import RED_SYSTEM, BLUE_SYSTEM, red_prompt, blue_prompt

def _json(t):
 t=t.strip()
 if t.startswith('```'): t=t.split('\n',1)[1].rsplit('```',1)[0]
 return json.loads(t)

def red_blue_battle(candidate, base_eval, red_providers, blue_providers, rounds=2):
    red=[]; blue=[]
    for rnd in range(max(1,rounds)):
        for p in red_providers:
            try: d=_json(p.generate(RED_SYSTEM,red_prompt(candidate,base_eval,rnd+1)).text)
            except Exception as e: d={'score':0,'findings':[str(e)],'severity':'high'}
            red.append({'round':rnd+1,'agent':p.config.name,**d})
        attack='\n'.join(json.dumps(x,ensure_ascii=False) for x in red[-len(red_providers):])
        for p in blue_providers:
            try: d=_json(p.generate(BLUE_SYSTEM,blue_prompt(candidate,base_eval,attack,rnd+1)).text)
            except Exception as e: d={'score':0,'fixes':[],'reason':str(e)}
            blue.append({'round':rnd+1,'agent':p.config.name,**d})
    red_score=sum(float(x.get('score',0)) for x in red)/max(1,len(red)); blue_score=sum(float(x.get('score',0)) for x in blue)/max(1,len(blue))
    return {'red':red,'blue':blue,'red_score':red_score,'blue_score':blue_score,'passed':red_score>=0.5 and blue_score>=0.5}
