from __future__ import annotations
import json, shutil, time
from pathlib import Path

CURRENT_SCHEMA='3.1Neo'
LEGACY_SCHEMAS=('2.5Rene','3.0Neo')

def snapshot(paths, out='data/migrations'):
    outp=Path(out);outp.mkdir(parents=True,exist_ok=True); dest=outp/f'snapshot-{int(time.time())}';dest.mkdir()
    copied=[]
    for p in paths:
        src=Path(p)
        if src.exists():
            target=dest/src.name
            if src.is_dir():shutil.copytree(src,target)
            else:shutil.copy2(src,target)
            copied.append(str(target))
    (dest/'manifest.json').write_text(json.dumps({'schema':CURRENT_SCHEMA,'created_at':time.time(),'paths':copied},indent=2))
    return str(dest)

def check(paths):
    return {'schema':CURRENT_SCHEMA,'legacy_supported':list(LEGACY_SCHEMAS),'paths':{str(Path(p)):Path(p).exists() for p in paths}}
