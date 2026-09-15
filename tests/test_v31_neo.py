import json
from pathlib import Path
from sev.mesh import KnowledgeMesh
from sev.teams import AgentTeam
from sev.router import SkillRouter
from sev.resources import ResourceGovernor,ResourcePolicy
from sev.prediction import PredictionMarket
from sev.plugin import PluginRegistry
from sev.privacy_mesh import SecureTelemetry,PrivacyBudget
from sev.governance_os import DecisionLedger
from sev.marketplace import Marketplace
from sev.eventstore import EventStore
from sev.security_lab import SecurityControlPlane
from sev.config import FrameworkConfig,save_config,load_config,CONFIG_DIR


def test_knowledge_mesh_and_path(tmp_path):
    m=KnowledgeMesh(tmp_path/'mesh.db')
    m.put_node('a','skill',{'name':'A'},'federation','A'); m.put_node('b','methodology',{'name':'B'},'federation','A'); m.put_edge('a','solved_by','b','A',.9)
    assert m.path('a','b')[0]['relation']=='solved_by'
    assert m.neighborhood('a',2)['nodes']
    bundle=m.export_bundle('federation','A'); m2=KnowledgeMesh(tmp_path/'mesh2.db'); assert m2.import_bundle(bundle,['A'])['imported_nodes']==2


def test_agent_team_and_router(tmp_path):
    mp=Marketplace(tmp_path/'market'); mp.publish({'name':'network','owner':'a','score':.9,'reliability':.9,'security_rating':.9,'compatibility':{'os':'linux'},'certification':'gold','version':'1'})
    r=SkillRouter(mp); assert r.select('network',{'os':'linux'})['name']=='network'
    t=AgentTeam(objective='x'); t.add('a','security',1,['security']); out=t.assign(['audit'],['security']); assert out['assignments'][0]['agent']=='a'


def test_resources_plugins_predictions(tmp_path):
    g=ResourceGovernor(ResourcePolicy(max_usd=1,max_tokens=10)); assert not g.admit({'usd':2})['allowed']
    p=PluginRegistry(); p.register('x',object()); assert 'x' in p.names()
    market=PredictionMarket(tmp_path/'p.jsonl'); row=market.create('a','candidate succeeds',.8); market.resolve(row['id'],True); assert market.calibration('a')['count']==1


def test_privacy_budget_and_decision(tmp_path):
    st=EventStore(tmp_path/'e.db'); secure=SecureTelemetry(budget=PrivacyBudget(1)); x=secure.aggregate([{'event_type':'x'},{'event_type':'x'}],.2); assert 'x' in x
    d=DecisionLedger(st).record('promote','skill-x',['eval:1'],{'quality':'>=0.9'},['judge-a'],.9); assert d['event_type']=='governance_decision'


def test_security_hardening_surfaces():
    s=SecurityControlPlane(); assert not s.scan_supply_chain(['foo@latest'])['safe']; assert not s.scan_sandbox_escape(['rm -rf /'])['safe']; assert s.scan_federation({'require_signed':True,'min_security':.5},{'signature_status':'verified','security_rating':.9})['safe']


def test_config_roundtrip_31(tmp_path,monkeypatch):
    import sev.config as cfg
    monkeypatch.setattr(cfg,'CONFIG_DIR',tmp_path)
    monkeypatch.setattr(cfg,'CONFIG_PATH',tmp_path/'config.json')
    c=FrameworkConfig(deployment_mode='federated',node_id='n1',prediction_market_enabled=True,host_custom={'theme':'dark'},resource_governance={'max_usd':3})
    cfg.save_config(c); x=cfg.load_config(); assert x.deployment_mode=='federated'; assert x.node_id=='n1'; assert x.host_custom['theme']=='dark'; assert x.prediction_market_enabled is True

def test_http_principal_boundaries(monkeypatch,tmp_path):
    import threading, urllib.request, urllib.error, json
    import sev.api as api
    c=FrameworkConfig(event_store=str(tmp_path/'events.db'),knowledge=type(FrameworkConfig().knowledge)(path=str(tmp_path/'kg.db')),marketplace=type(FrameworkConfig().marketplace)(path=str(tmp_path/'mkt')),federation=type(FrameworkConfig().federation)(path=str(tmp_path/'fed')),registry_dir=str(tmp_path/'registry'),eval_corpus=type(FrameworkConfig().eval_corpus)(root=str(tmp_path/'eval')),deployment_mode='personal',node_id='test')
    monkeypatch.setattr(api,'load_config',lambda:c)
    monkeypatch.setenv('SKIF_HOST_TOKEN','host-secret'); monkeypatch.setenv('SKIF_AGENT_TOKEN','agent-secret'); monkeypatch.setenv('SKIF_USER_TOKEN','user-secret')
    from http.server import ThreadingHTTPServer
    srv=ThreadingHTTPServer(('127.0.0.1',0),api.H); th=threading.Thread(target=srv.serve_forever,daemon=True); th.start(); base=f'http://127.0.0.1:{srv.server_port}'
    def get(path,token=None):
        req=urllib.request.Request(base+path,headers=({'Authorization':f'Bearer {token}'} if token else {}))
        try:
            with urllib.request.urlopen(req,timeout=3) as r:return r.status,r.read().decode()
        except urllib.error.HTTPError as e:return e.code,e.read().decode()
    assert get('/host/neo','agent-secret')[0]==401
    assert get('/host/neo','host-secret')[0]==200
    assert get('/agent/neo','agent-secret')[0]==200
    assert get('/user/neo','user-secret')[0]==200
    assert get('/api/production/status','agent-secret')[0]==403
    assert get('/api/auth/me','agent-secret')[0]==200
    srv.shutdown();srv.server_close()

def test_neo_http_agent_and_host_features(monkeypatch,tmp_path):
    import threading, urllib.request, urllib.error, json
    import sev.api as api
    c=FrameworkConfig(event_store=str(tmp_path/'events.db'),knowledge=type(FrameworkConfig().knowledge)(path=str(tmp_path/'kg.db')),marketplace=type(FrameworkConfig().marketplace)(path=str(tmp_path/'mkt')),federation=type(FrameworkConfig().federation)(path=str(tmp_path/'fed')),registry_dir=str(tmp_path/'registry'),eval_corpus=type(FrameworkConfig().eval_corpus)(root=str(tmp_path/'eval')),deployment_mode='federated',node_id='n1',prediction_market_enabled=True)
    monkeypatch.setattr(api,'load_config',lambda:c)
    monkeypatch.setenv('SKIF_HOST_TOKEN','h'); monkeypatch.setenv('SKIF_AGENT_TOKEN','a'); monkeypatch.setenv('SKIF_USER_TOKEN','u')
    from http.server import ThreadingHTTPServer
    srv=ThreadingHTTPServer(('127.0.0.1',0),api.H); th=threading.Thread(target=srv.serve_forever,daemon=True); th.start(); base=f'http://127.0.0.1:{srv.server_port}'
    def call(path,token,body=None):
        req=urllib.request.Request(base+path,data=json.dumps(body).encode() if body is not None else None,headers={'Authorization':f'Bearer {token}','Content-Type':'application/json'})
        try:
            with urllib.request.urlopen(req,timeout=3) as r:
                raw=r.read().decode();
                try: obj=json.loads(raw)
                except Exception: obj={'html':raw}
                return r.status,obj
        except urllib.error.HTTPError as e:return e.code,json.loads(e.read().decode())
    assert call('/agent/neo','a')[0]==200
    assert call('/host/neo','h')[0]==200
    assert call('/user/neo','u')[0]==200
    assert call('/api/control/schema','a')[1]['mode']=='federated'
    status,data=call('/api/knowledge/mesh/node','a',{'id':'skill:x','kind':'skill','payload':{'name':'x'}}); assert status==201, data
    assert call('/api/knowledge/mesh/node','a',{'id':'method:m','kind':'methodology','payload':{'name':'m'}})[0]==201
    assert call('/api/knowledge/mesh/edge','a',{'src':'skill:x','relation':'solved_by','dst':'method:m'})[0]==201
    assert call('/api/knowledge/mesh/path?source=skill%3Ax&target=method%3Am','a')[1]['path'][0]['relation']=='solved_by'
    assert call('/api/resources/admit','a',{'estimate':{'usd':999}})[0]==403
    assert call('/api/federation/sign','a',{'kind':'skill','payload':{}})[0]==403
    assert call('/api/shadow/run','a',{'baseline_skill':'x','candidate_skill':'y'})[0]==403
    assert call('/api/resources/admit','h',{'estimate':{'usd':1}})[1]['allowed']
    assert call('/api/predictions/create','a',{'subject':'x','probability':.7})[0]==201
    srv.shutdown();srv.server_close()


def test_knowledge_mesh_digest_and_visibility(tmp_path):
    m=KnowledgeMesh(tmp_path/'mesh.db')
    m.put_node('private','skill',{'secret':'should-not-escape'},'private','nodeA')
    m.put_node('public','skill',{'name':'public'},'public','nodeA')
    m.put_edge('public','related','private','nodeA',1.0)
    bundle=m.export_bundle('public','nodeA')
    m2=KnowledgeMesh(tmp_path/'mesh2.db')
    assert m2.import_bundle(bundle,['nodeA'])['digest_verified']
    tampered=dict(bundle); tampered['nodes']=[dict(bundle['nodes'][0],payload={'name':'tampered'})]
    try:
        m2.import_bundle(tampered,['nodeA'])
        raise AssertionError('tampered bundle accepted')
    except ValueError as exc:
        assert str(exc)=='mesh-bundle-digest-mismatch'
    assert not m.neighborhood('public',2,visibilities=['community','federation','public'])['edges']
    assert m.neighborhood('private',1,visibilities=['community','federation','public'])['nodes']==[]
