from __future__ import annotations
import json,time,hashlib
from pathlib import Path

def lineage(skill_dir):
    p=Path(skill_dir); manifest=p/'skill.json'; data=json.loads(manifest.read_text()) if manifest.exists() else {}
    parent=data.get('fork_of') or data.get('composed_from') or data.get('merge_of') or []
    if isinstance(parent,str):parent=[parent]
    return {'skill':data.get('name',p.name),'version':data.get('version',''),'parents':parent,'branch':data.get('branch','main'),'generated_at':time.time(),'digest':hashlib.sha256((p/'SKILL.md').read_bytes() if (p/'SKILL.md').exists() else b'').hexdigest()}
