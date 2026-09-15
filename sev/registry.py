from __future__ import annotations
import json, uuid
from pathlib import Path

def _write(root,name,obj):
 p=Path(root); p.mkdir(parents=True,exist_ok=True); ident=obj.get('id') or str(uuid.uuid4()); obj['id']=ident; (p/f'{name}-{ident}.json').write_text(json.dumps(obj,indent=2,ensure_ascii=False)); return obj

def propose_skill(root,name,description,source='agent',payload=None): return _write(Path(root)/'skills' ,'proposal',{'name':name,'description':description,'source':source,'status':'proposed','payload':payload or {}})
def list_skill_proposals(root): return [_load(p) for p in sorted((Path(root)/'skills').glob('proposal-*.json'))]
def add_methodology(root,title,content,author='agent',tags=None): return _write(Path(root)/'methodologies','entry',{'title':title,'content':content,'author':author,'tags':tags or [],'status':'candidate'})
def list_methodologies(root): return [_load(p) for p in sorted((Path(root)/'methodologies').glob('entry-*.json'))]
def _load(p): return json.loads(p.read_text())
