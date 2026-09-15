from __future__ import annotations
import hashlib, json, re, time
from pathlib import Path
from difflib import SequenceMatcher

STATES=('draft','proposed','reviewed','trusted','deprecated','retired')
LEAK_PATTERNS=[r'answer\s*=\s*',r'expected_answer',r'gold_answer',r'correct_answer',r'do not expose',r'ignore evaluation',r'lower.*threshold',r'delete.*test']

class EvalCorpus:
    def __init__(self, root='data/eval_corpus'):
        self.root=Path(root); self.root.mkdir(parents=True,exist_ok=True); self.meta=self.root/'corpora.json'; self.proposals=self.root/'proposals.jsonl'
    def _load(self):
        if not self.meta.exists():return {}
        return json.loads(self.meta.read_text())
    def _save(self,x):self.meta.write_text(json.dumps(x,ensure_ascii=False,indent=2))
    @staticmethod
    def digest(cases):return hashlib.sha256(json.dumps(cases,sort_keys=True,ensure_ascii=False,default=str).encode()).hexdigest()
    def create(self,name,cases,owner='system',version='1.0.0',state='draft'):
        if state not in STATES:raise ValueError('invalid state')
        data=self._load(); cid=f'{name}:{version}'; data[cid]={'id':cid,'name':name,'version':version,'owner':owner,'state':state,'digest':self.digest(cases),'count':len(cases),'created_at':time.time(),'cases':cases}; self._save(data); return data[cid]
    def get(self,cid):return self._load().get(cid)
    def transition(self,cid,state):
        if state not in STATES:raise ValueError('invalid state')
        data=self._load(); row=data[cid]; allowed={ 'draft':{'proposed','retired'}, 'proposed':{'reviewed','draft','retired'}, 'reviewed':{'trusted','draft','deprecated'}, 'trusted':{'deprecated'}, 'deprecated':{'retired','trusted'}, 'retired':set() }
        if state not in allowed.get(row['state'],set()):raise ValueError(f'invalid-transition:{row["state"]}->{state}')
        row['state']=state; row['updated_at']=time.time(); self._save(data); return row
    def propose_cases(self,cases,source='agent',reason=''):
        leak=self.leakage(cases); row={'id':f'proposal-{int(time.time()*1000)}','source':source,'reason':reason,'cases':cases,'leakage':leak,'created_at':time.time(),'status':'rejected' if leak['blocked'] else 'proposed'}
        with self.proposals.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
        return row
    def leakage(self,cases):
        findings=[]; texts=[]
        for i,c in enumerate(cases):
            text=json.dumps(c,ensure_ascii=False)
            texts.append(text)
            for p in LEAK_PATTERNS:
                if re.search(p,text,re.I):findings.append({'case':c.get('id',i),'pattern':p})
        for i,a in enumerate(texts):
            for j,b in enumerate(texts[i+1:],i+1):
                if SequenceMatcher(None,a,b).ratio()>=0.92:findings.append({'case_a':cases[i].get('id',i),'case_b':cases[j].get('id',j),'pattern':'near-duplicate'})
        return {'blocked':bool(findings),'findings':findings}
    def profile(self,cases):
        topics={}; mandatory=0
        for c in cases:
            for t in c.get('tags',[]) or []:topics[t]=topics.get(t,0)+1
            mandatory+=int(bool(c.get('mandatory')))
        return {'count':len(cases),'mandatory':mandatory,'topics':topics,'digest':self.digest(cases),'leakage':self.leakage(cases)}
    def leaderboard(self,results):
        rows=[]
        for r in results:
            score=float(r.get('score',0)); rows.append({'subject':r.get('subject',r.get('skill','unknown')),'score':score,'pass_rate':float(r.get('pass_rate',0)),'cost':float(r.get('cost',0)),'latency_ms':float(r.get('latency_ms',0))})
        rows.sort(key=lambda x:(-x['score'],-x['pass_rate'],x['cost'],x['latency_ms'])); return rows
