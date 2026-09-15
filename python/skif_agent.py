from __future__ import annotations
import json, urllib.request, urllib.parse

class SkifAgentClient:
    """Small machine-oriented SDK. It intentionally exposes Agent-scoped operations only."""
    def __init__(self, base_url='http://127.0.0.1:8787', token=''):
        self.base=base_url.rstrip('/'); self.token=token
    def _call(self,path,body=None):
        headers={'Content-Type':'application/json'}
        if self.token: headers['Authorization']=f'Bearer {self.token}'
        req=urllib.request.Request(self.base+path,data=(json.dumps(body).encode() if body is not None else None),headers=headers,method='POST' if body is not None else 'GET')
        with urllib.request.urlopen(req,timeout=30) as r:return json.loads(r.read().decode())
    def capabilities(self, **kwargs): return self._call('/api/agents/capabilities',kwargs)
    def telemetry(self, **kwargs): return self._call('/api/telemetry',kwargs)
    def contribute(self, **kwargs): return self._call('/api/contributions',kwargs)
    def vote(self, **kwargs): return self._call('/api/community/vote',kwargs)
    def marketplace(self,q=''): return self._call('/api/marketplace/search?q='+urllib.parse.quote(q))
    def recommend(self,task,environment=None): return self._call('/api/agent/recommend?task='+urllib.parse.quote(task)+(('&environment='+urllib.parse.quote(json.dumps(environment))) if environment else ''))
    def team_plan(self,**kwargs): return self._call('/api/agent/team/plan',kwargs)
    def research_create(self,**kwargs): return self._call('/api/research/create',kwargs)
    def research_transition(self,**kwargs): return self._call('/api/research/transition',kwargs)
    def compose_skill(self,**kwargs): return self._call('/api/skills/compose',kwargs)
    def portable_identity(self,**kwargs): return self._call('/api/identity/portable/verify',kwargs)
    def federation_negotiate(self,**kwargs): return self._call('/api/trust/negotiate',kwargs)
    def knowledge_path(self,source,target): return self._call('/api/knowledge/mesh/path?source='+urllib.parse.quote(source)+'&target='+urllib.parse.quote(target))
    def report_error(self,**kwargs): return self._call('/api/errors',kwargs)
    def methodology(self,**kwargs): return self._call('/api/methodologies',kwargs)
    def eval_propose(self,**kwargs): return self._call('/api/eval/propose',kwargs)
