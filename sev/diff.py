from __future__ import annotations
import difflib
from pathlib import Path
from .skill import iter_files


def unified_diff(before: Path, after: Path) -> str:
    paths = sorted({p.relative_to(before).as_posix() for p in iter_files(before)} | {p.relative_to(after).as_posix() for p in iter_files(after)})
    chunks = []
    for rel in paths:
        a = before / rel
        b = after / rel
        old = a.read_text(encoding='utf-8', errors='replace').splitlines(keepends=True) if a.exists() else []
        new = b.read_text(encoding='utf-8', errors='replace').splitlines(keepends=True) if b.exists() else []
        if old == new:
            continue
        chunks.extend(difflib.unified_diff(old, new, fromfile=f'a/{rel}', tofile=f'b/{rel}'))
    return ''.join(chunks)
