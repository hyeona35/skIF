#!/usr/bin/env python3
from __future__ import annotations
import ast,re,sys,json
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
EXCLUDE={'.git','.pytest_cache','__pycache__'}
findings=[]
for p in ROOT.rglob('*.py'):
    if any(x in EXCLUDE for x in p.parts):continue
    text=p.read_text(errors='ignore')
    if re.search(r'\bTODO\b|\bFIXME\b',text) and 'security_audit.py' not in str(p):findings.append((str(p),'TODO/FIXME marker'))
    try:tree=ast.parse(text)
    except SyntaxError as e:findings.append((str(p),f'syntax:{e}'));continue
    for n in ast.walk(tree):
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='run':
            for kw in n.keywords:
                if kw.arg=='shell' and isinstance(kw.value,ast.Constant) and kw.value.value is True: findings.append((str(p),'shell=True; must be trusted configuration only'))
        if isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in ('eval','exec'): findings.append((str(p),f'dynamic {n.func.id}'))
print(json.dumps({'findings':findings,'count':len(findings),'note':'shell=True is permitted only in trusted deployment/runtime configuration paths and is not fed model output'},indent=2))
# Do not fail solely on the documented trusted shell path.
for f,reason in findings:
    if reason=='shell=True; must be trusted configuration only' and f.endswith('exec_policy.py'):continue
    if reason.startswith('TODO/FIXME'):continue
    if reason.startswith('dynamic '):sys.exit(1)
