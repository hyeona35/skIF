import json, threading, time
from http.client import HTTPConnection
from pathlib import Path

from sev.eventstore import EventStore
from sev.reputation import ReputationEngine
from sev.governance import VoteGovernor
from sev.knowledge import KnowledgeGraph
from sev.resilience import AgentGuard
from sev.config import FrameworkConfig


def test_reputation_is_bounded_and_learns_from_history(tmp_path):
    store=EventStore(str(tmp_path/'events.db')); rep=ReputationEngine(store)
    agent='alice'; rep.register(agent,'install-1')
    for _ in range(10):
        store.emit('skill_commit',actor=agent,skill='demo',payload={'accepted':True,'content_hash':str(time.time_ns())})
    store.emit('patch_result',actor=agent,skill='demo',payload={'accepted':True})
    score=rep.score(agent)
    assert 0 <= score['reputation'] <= 1
    assert 0 < score['vote_weight'] <= 2
    assert score['metrics']['patch_acceptance'] > 0


def test_duplicate_vote_and_influence_cap(tmp_path):
    store=EventStore(str(tmp_path/'events.db')); rep=ReputationEngine(store); gov=VoteGovernor(store,rep)
    d=gov.decide('new-agent','demo','run-1','c1','yes')
    assert d['accepted'] and d['weight'] <= 1.0
    store.emit('community_vote',actor='new-agent',skill='demo',run_id='run-1',payload={'candidate':'c1','choice':'yes','weight':d['weight']})
    again=gov.decide('new-agent','demo','run-1','c1','yes')
    assert not again['accepted'] and again['reason']=='duplicate-vote-window'


def test_knowledge_graph_relations_and_path(tmp_path):
    kg=KnowledgeGraph(str(tmp_path/'knowledge.db'))
    kg.upsert_node('skill:a','skill','a'); kg.upsert_node('methodology:m','methodology','m'); kg.upsert_node('error:e','error','e')
    kg.link('skill:a','solved_by','methodology:m'); kg.link('methodology:m','derived_from','error:e')
    g=kg.graph(); assert any(e['relation']=='solved_by' for e in g['edges'])
    p=kg.explain_path('skill:a','error:e'); assert p['found']


def test_knowledge_graph_ingests_events(tmp_path):
    store=EventStore(str(tmp_path/'events.db')); kg=KnowledgeGraph(str(tmp_path/'knowledge.db'))
    store.subscribe(kg.ingest_event)
    store.emit('methodology_shared',actor='agent-a',skill='demo',payload={'methodology':'m1'})
    g=kg.graph(); ids={x['id'] for x in g['nodes']}; assert 'skill:demo' in ids and 'agent:agent-a' in ids


def test_agent_guard_blocks_burst_and_failure(tmp_path):
    g=AgentGuard(max_events_per_minute=2,max_failures=2,block_seconds=60)
    assert g.allow('a'); assert g.allow('a'); assert not g.allow('a')
    g.reset('b'); g.record_failure('b'); g.record_failure('b'); assert not g.allow('b')


def test_config_roundtrip_has_20_controls(tmp_path, monkeypatch):
    cfg=FrameworkConfig()
    assert cfg.reputation.enabled and cfg.knowledge.enabled and cfg.resilience.enabled
    assert cfg.reputation.max_vote_weight == 2.0
