from __future__ import annotations

import hashlib
import json
from pathlib import Path

EXCLUDED = {'.git', '__pycache__', '.DS_Store'}
TEXT_EXTS = {'.md', '.txt', '.json', '.yaml', '.yml', '.toml', '.py', '.js', '.ts', '.tsx', '.jsx', '.sh'}


def iter_files(root: Path):
    for p in sorted(root.rglob('*')):
        if not p.is_file():
            continue
        if any(part in EXCLUDED for part in p.parts):
            continue
        if p.suffix.lower() in TEXT_EXTS:
            yield p


def snapshot(root: Path) -> dict:
    files = {}
    for p in iter_files(root):
        rel = p.relative_to(root).as_posix()
        data = p.read_bytes()
        files[rel] = {
            'sha256': hashlib.sha256(data).hexdigest(),
            'content': data.decode('utf-8', errors='replace'),
        }
    return {'root': str(root.resolve()), 'files': files}


def snapshot_hash(snap: dict) -> str:
    payload = {k: v['sha256'] for k, v in snap['files'].items()}
    return hashlib.sha256(json.dumps(payload, sort_keys=True).encode()).hexdigest()


def materialize(snapshot_data: dict, dest: Path) -> None:
    dest.mkdir(parents=True, exist_ok=True)
    for rel, item in snapshot_data['files'].items():
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(item['content'], encoding='utf-8')
