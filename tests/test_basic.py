from pathlib import Path
from sev.skill import snapshot, snapshot_hash


def test_snapshot_stable():
    root = Path(__file__).resolve().parents[1] / 'examples' / 'demo_skill'
    a = snapshot(root)
    b = snapshot(root)
    assert snapshot_hash(a) == snapshot_hash(b)
