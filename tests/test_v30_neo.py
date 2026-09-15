import json, os, tempfile
from pathlib import Path
from sev.portable_identity import PortableIdentityAuthority
from sev.trust_negotiation import TrustPolicy, negotiate
from sev.privacy import TelemetryProtector, local_aggregate, differential_private_counts
from sev.federation_network import FederationNetwork
from sev.research_os import ResearchOS
from sev.neo import AutonomousResearchOrchestrator
from sev.composition import compose, fork, merge
from sev.security_lab import SecurityLab
from sev.eventstore import EventStore


def test_portable_identity_roundtrip():
    a=PortableIdentityAuthority('node-a','secret',ttl_seconds=60)
    c=a.issue('agent-1','node-b',.91,'trusted',['vote','telemetry'])
    assert a.verify(c,expected_subject='node-b')['valid']
    c['reputation']=0
    assert not a.verify(c)['valid']


def test_trust_negotiation_is_strict_enough():
    r=negotiate(TrustPolicy('gold',.8,True,True),TrustPolicy('silver',.6,True,True))
    assert r['effective']['reliability']==.8
    assert r['effective']['security'] in ('gold','silver')


def test_privacy_encryption_redaction_and_dp():
    p=TelemetryProtector()
    cipher=p.encrypt({'email':'a@b.test','skill':'x','n':1})
    plain=p.decrypt(cipher)
    assert plain['email']=='[REDACTED]'
    c=local_aggregate([{'event_type':'a'},{'event_type':'a'},{'event_type':'b'}])
    d=differential_private_counts(c,epsilon=5)
    assert set(d)=={'a','b'}


def test_federation_network_negotiation(tmp_path):
    n=FederationNetwork(tmp_path/'network','A')
    row=n.connect('B','https://b',{'security':'gold','reliability':.8,'require_signed':True,'require_portable_identity':True})
    assert row['status']=='connected'
    assert n.plan_sync('B')['ready']


def test_research_closed_loop_requires_replication(tmp_path):
    store=EventStore(str(tmp_path/'events.db'))
    r=ResearchOS(store,tmp_path/'research')
    def ev(_rid,_obs): return {'passed':True,'score':.9}
    def rep(_rid,_result): return {'replicated':True,'independent':True}
    out=AutonomousResearchOrchestrator(r,ev,rep).create_loop({'error':'x'},'a','skill')
    assert out['phase']=='production'


def test_skill_compose_fork_merge(tmp_path):
    a=tmp_path/'a'; b=tmp_path/'b'; out=tmp_path/'out'; forked=tmp_path/'fork'
    for p,t in ((a,'A'),(b,'B')):
        p.mkdir(); (p/'SKILL.md').write_text(t); (p/'skill.json').write_text(json.dumps({'name':p.name}))
    assert compose([a,b],out)['requires']==['a','b']
    assert fork(a,forked,'secure')['branch']=='secure'
    assert merge(a,b,tmp_path/'merge')['requires']==['a','b']


def test_security_attack_surface(tmp_path):
    lab=SecurityLab()
    assert not lab.federation_attack({'kind':'eval','payload':{}})['safe']
    assert lab.dependency_scan(['requests==2.0'])['safe']
    assert not lab.dependency_scan(['pkg@latest'])['safe']
    assert not lab.vote_attack([{'agent_id':'x'}]*20,100)['safe']

def test_federation_marketplace_import(tmp_path):
    from sev.federation import FederationStore, SignedArtifact
    from sev.federation_network import FederationNetwork
    from sev.federation_marketplace import FederationMarketplace
    from sev.marketplace import Marketplace
    signer=SignedArtifact('secret',True)
    fed=FederationStore(tmp_path/'fed',signer,['remote'],True)
    net=FederationNetwork(tmp_path/'network','local',signer)
    net.connect('remote','https://remote',{'security':'silver','reliability':.5})
    art=signer.sign('skill',{'name':'remote-skill','owner':'r','security_rating':.9,'version':'1.0.0'},'remote')
    row=FederationMarketplace(Marketplace(tmp_path/'market'),fed,net).import_skill(art,{'security':'silver','reliability':.5},.75)
    assert row['provenance_status']=='verified'
