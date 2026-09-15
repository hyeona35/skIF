from __future__ import annotations
import hashlib,hmac,json,os
from pathlib import Path

def sha256_file(p):
    h=hashlib.sha256(); h.update(Path(p).read_bytes()); return h.hexdigest()
def snapshot_hash(root):
    entries=[]
    for p in sorted(Path(root).rglob('*')):
        if p.is_file() and '.git' not in p.parts and 'data/runs' not in p.parts:
            entries.append((str(p.relative_to(root)),sha256_file(p)))
    return hashlib.sha256(json.dumps(entries,sort_keys=True).encode()).hexdigest()
def write_attestation(path,payload,key_env=''):
    body=json.dumps(payload,sort_keys=True,separators=(',',':')).encode()
    out={'algorithm':'sha256','payload_sha256':hashlib.sha256(body).hexdigest(),'payload':payload}
    key=os.environ.get(key_env,'') if key_env else ''
    if key:
        out['signature_algorithm']='HMAC-SHA256'; out['signature']=hmac.new(key.encode(),body,hashlib.sha256).hexdigest()
    Path(path).write_text(json.dumps(out,indent=2,ensure_ascii=False))
