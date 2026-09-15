#!/usr/bin/env python3
from __future__ import annotations
import argparse,tempfile,time,json,sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from sev.eventstore import EventStore
from sev.reputation import ReputationEngine
from sev.knowledge import KnowledgeGraph
from sev.mesh import KnowledgeMesh
from sev.cache import TTLCache

def bench(fn,n):
    t=time.perf_counter()
    for _ in range(n):fn()
    elapsed=(time.perf_counter()-t)*1000
    return {'iterations':n,'total_ms':round(elapsed,3),'per_op_ms':round(elapsed/n,6)}

def main():
    ap=argparse.ArgumentParser();ap.add_argument('--iterations',type=int,default=100);a=ap.parse_args()
    with tempfile.TemporaryDirectory() as d:
        store=EventStore(f'{d}/events.db');kg=KnowledgeGraph(f'{d}/kg.db');mesh=KnowledgeMesh(f'{d}/mesh.db');rep=ReputationEngine(store);cache=TTLCache(30,4096)
        for i in range(max(200,a.iterations*2)): store.emit('skill_usage',actor=f'a{i%20}',skill=f's{i%10}',payload={'ok':True})
        for i in range(50):
            kg.link(f'skill:s{i%10}','solved_by',f'methodology:m{i%5}')
            mesh.put_node(f's{i%10}','skill',{'name':f's{i%10}'})
        for i in range(5): mesh.put_node(f'm{i}','methodology',{'name':f'm{i}'}); mesh.put_edge(f's{i}','solved_by',f'm{i}')
        results={
            'event_recent':bench(lambda:store.recent(50),a.iterations),
            'reputation':bench(lambda:rep.score('a1'),max(10,a.iterations//2)),
            'knowledge_neighborhood':bench(lambda:kg.neighborhood('skill:s1',2),max(10,a.iterations//2)),
            'knowledge_mesh_path':bench(lambda:mesh.path('s1','m1'),max(10,a.iterations//2)),
            'cache_get_set':bench(lambda:(cache.set('k',1),cache.get('k')),a.iterations),
        }
        print(json.dumps(results,indent=2))
if __name__=='__main__':main()
