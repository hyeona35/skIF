from __future__ import annotations
import json
from dataclasses import dataclass, field
from pathlib import Path
from collections import deque

@dataclass
class SkillNode:
    name: str
    path: str
    requires: list[str] = field(default_factory=list)
    provides: list[str] = field(default_factory=list)

class DependencyGraphError(ValueError):
    pass

def _load_manifest(path: Path) -> SkillNode:
    manifest = path / 'skill.json'
    data = {}
    if manifest.exists():
        try:
            data = json.loads(manifest.read_text())
        except json.JSONDecodeError as exc:
            raise DependencyGraphError(f'invalid skill manifest: {manifest}: {exc}')
    name = str(data.get('name') or path.name)
    requires = list(data.get('requires', []))
    provides = list(data.get('provides', []))
    return SkillNode(name, str(path), requires, provides)

def discover_skills(root: str | Path) -> dict[str, SkillNode]:
    root = Path(root)
    if not root.exists():
        return {}
    nodes = {}
    for p in sorted(root.iterdir()):
        if p.is_dir() and (p / 'SKILL.md').exists():
            n = _load_manifest(p); nodes[n.name] = n
    if (root / 'SKILL.md').exists():
        n = _load_manifest(root); nodes[n.name] = n
    return nodes

def build_dag(nodes: dict[str, SkillNode]) -> dict[str, set[str]]:
    graph = {name: set() for name in nodes}
    for name, node in nodes.items():
        for dep in node.requires:
            if dep in nodes:
                graph[name].add(dep)
    indegree = {n: 0 for n in graph}
    for n, deps in graph.items():
        for dep in deps: indegree[dep] += 1
    q = deque([n for n, d in indegree.items() if d == 0])
    seen = 0
    while q:
        n = q.popleft(); seen += 1
        for dep in graph[n]:
            indegree[dep] -= 1
            if indegree[dep] == 0: q.append(dep)
    if seen != len(graph):
        raise DependencyGraphError('skill dependency graph contains a cycle')
    return graph

def transitive_impact(graph: dict[str, set[str]], changed: list[str]) -> dict[str, list[str]]:
    reverse = {n: set() for n in graph}
    for child, deps in graph.items():
        for dep in deps:
            reverse.setdefault(dep, set()).add(child)
    impacted = {}
    for start in changed:
        seen, q = set(), deque(reverse.get(start, set()))
        while q:
            x = q.popleft()
            if x in seen: continue
            seen.add(x); q.extend(reverse.get(x, set()))
        impacted[start] = sorted(seen)
    return impacted

def analyze(root: str | Path, changed: list[str] | None = None) -> dict:
    nodes = discover_skills(root); graph = build_dag(nodes)
    changed = changed or list(nodes)
    return {
        'nodes': {k: {'path': v.path, 'requires': v.requires, 'provides': v.provides} for k, v in nodes.items()},
        'edges': [{'skill': k, 'depends_on': sorted(v)} for k, v in graph.items() if v],
        'impact': transitive_impact(graph, changed),
    }
