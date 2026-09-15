import os, sqlite3, json, threading, time, urllib.request
from http.server import ThreadingHTTPServer

from sev.eventstore import EventStore
from sev.identity import IdentityStore
from sev.eval_corpus import EvalCorpus
from sev.federation import SignedArtifact, FederationStore
from sev.security_lab import SecurityLab
from sev.idempotency import Idempotency
from sev.api import H


def test_event_schema_forward_extension_and_idempotency(tmp_path):
    s=EventStore(tmp_path/'e.db')
    a=s.emit('extension_event',actor='a',payload={'x':1},idempotency_key='k1')
    b=s.emit('extension_event',actor='a',payload={'x':2},idempotency_key='k1')
    assert a['event_id']==b['event_id'] and b['payload']['x']==1
    assert a['schema_version']=='1.0'


def test_legacy_event_store_migrates(tmp_path):
    p=tmp_path/'legacy.db'
    db=sqlite3.connect(p)
    db.execute('CREATE TABLE events (id INTEGER PRIMARY KEY AUTOINCREMENT, ts REAL NOT NULL, event_type TEXT NOT NULL, actor TEXT, skill TEXT, run_id TEXT, payload TEXT NOT NULL)')
    db.execute('INSERT INTO events(ts,event_type,actor,skill,run_id,payload) VALUES(?,?,?,?,?,?)',(time.time(),'legacy_x','a','s','r',json.dumps({'ok':1})));db.commit();db.close()
    s=EventStore(p);rows=s.recent(5,'s')
    assert rows[0]['event_type']=='legacy_x' and rows[0]['source']=='legacy'


def test_identity_capabilities_and_trust(tmp_path):
    i=IdentityStore(tmp_path/'id.json'); row=i.register('inst','pk','A',['vote','telemetry']); assert row['agent_id']; assert i.authorize(row['agent_id'],'vote'); assert not i.authorize(row['agent_id'],'admin'); assert i.set_trust(row['agent_id'],'trusted')['trust_level']=='trusted'


def test_eval_lifecycle_and_leakage(tmp_path):
    c=EvalCorpus(tmp_path/'corpus'); r=c.create('suite',[{'id':'1','prompt':'safe'}],state='draft'); assert c.transition(r['id'],'proposed')['state']=='proposed'; assert c.transition(r['id'],'reviewed')['state']=='reviewed'; assert c.transition(r['id'],'trusted')['state']=='trusted'
    bad=c.propose_cases([{'id':'x','expected_answer':'secret'}]); assert bad['status']=='rejected' and bad['leakage']['blocked']


def test_federation_quarantine_and_release(tmp_path):
    signer=SignedArtifact('s',True); f=FederationStore(tmp_path/'fed',signer,['n1']); a=signer.sign('skill',{'name':'x'},'n1'); r=f.ingest(a); assert r['status']=='quarantine'; assert len(f.quarantine())==1; assert f.release(a['artifact_id'],'host')['released']==a['artifact_id']; assert len(f.list())==1


def test_security_depth():
    lab=SecurityLab(); assert not lab.dependency_scan(['foo@latest'])['safe']; assert not lab.sandbox_test('python -c "import os; os.system(\'id\')"')['safe']; assert lab.fuzz({'text':'safe'},8)['blocked']


def test_dashboard_role_separation(monkeypatch, tmp_path):
    monkeypatch.setenv('SKIF_HOST_TOKEN','H'); monkeypatch.setenv('SKIF_AGENT_TOKEN','A'); monkeypatch.setenv('SKIF_USER_TOKEN','U'); monkeypatch.setenv('SKIF_CONFIG_DIR',str(tmp_path/'cfg'))
    monkeypatch.setenv('SKIF_API_TOKEN','')
    server=ThreadingHTTPServer(('127.0.0.1',0),H); th=threading.Thread(target=server.serve_forever,daemon=True);th.start();base=f'http://127.0.0.1:{server.server_port}'
    def req(path,token):
        q=urllib.request.Request(base+path,headers={'Authorization':f'Bearer {token}'})
        try:return urllib.request.urlopen(q).status
        except urllib.error.HTTPError as e:return e.code
    assert req('/host','H')==200; assert req('/agent','A')==200; assert req('/user','U')==200
    assert req('/api/production/status','A')==403; assert req('/api/production/status','U')==403
    try:req('/host','A');assert False
    except Exception:pass
    server.shutdown();server.server_close()
