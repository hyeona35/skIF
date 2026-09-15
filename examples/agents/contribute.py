from __future__ import annotations
import json, os, urllib.request

BASE=os.environ.get('SKIF_URL','http://127.0.0.1:8787').rstrip('/')
TOKEN=os.environ.get('SKIF_API_TOKEN','')

def post(path, payload):
    data=json.dumps(payload).encode()
    req=urllib.request.Request(BASE+path,data=data,headers={'Content-Type':'application/json',**({'Authorization':f'Bearer {TOKEN}'} if TOKEN else {})})
    with urllib.request.urlopen(req,timeout=10) as r:
        return json.loads(r.read())

agent_id=os.environ.get('SKIF_AGENT_ID','example-agent')
skill=os.environ.get('SKIF_SKILL','demo')
print(post('/api/agents/register',{'agent_id':agent_id,'installation_id':os.environ.get('SKIF_INSTALLATION_ID','local')}))
print(post('/api/telemetry',{'agent_id':agent_id,'skill':skill,'event_type':'skill_usage','payload':{'outcome':'success'}}))
print(post('/api/community/vote',{'agent_id':agent_id,'skill':skill,'run_id':'example-run','candidate':'c1','choice':'yes','confidence':0.8}))
