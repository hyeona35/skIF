from __future__ import annotations
import hashlib, json, os, re, subprocess, threading, time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

_SECRET_PATTERNS = [
    re.compile(r'(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+'),
    re.compile(r'(?i)(api[_-]?key\s*[:=]\s*)[^\s,;]+'),
    re.compile(r'(?i)(secret\s*[:=]\s*)[^\s,;]+'),
    re.compile(r'(?i)(password\s*[:=]\s*)[^\s,;]+'),
    re.compile(r'(?i)(cookie\s*[:=]\s*)[^\s,;]+'),
]
_EMAIL = re.compile(r'\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b', re.I)
_PHONE = re.compile(r'(?<!\d)(?:\+?\d[\d .()\-]{7,}\d)(?!\d)')


def scrub_text(value: str) -> str:
    value = _EMAIL.sub('[REDACTED_EMAIL]', value)
    value = _PHONE.sub('[REDACTED_PHONE]', value)
    for pattern in _SECRET_PATTERNS:
        value = pattern.sub(lambda m: m.group(1) + '[REDACTED]', value)
    return value


def scrub(value: Any) -> Any:
    if isinstance(value, str):
        return scrub_text(value)
    if isinstance(value, list):
        return [scrub(v) for v in value]
    if isinstance(value, dict):
        out = {}
        for k, v in value.items():
            if re.search(r'(?i)(authorization|cookie|api[_-]?key|secret|password|token)', str(k)):
                out[k] = '[REDACTED]'
            else:
                out[k] = scrub(v)
        return out
    return value


def fingerprint_request(request: dict[str, Any]) -> str:
    body = scrub(request)
    raw = json.dumps(body, sort_keys=True, ensure_ascii=False, separators=(',', ':'))
    return hashlib.sha256(raw.encode()).hexdigest()


class KillSwitch:
    def __init__(self, path='data/production/kill_switch.json'):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()

    def status(self) -> dict[str, Any]:
        if not self.path.exists():
            return {'enabled': False, 'reason': '', 'updated_at': None}
        try:
            return json.loads(self.path.read_text())
        except Exception:
            return {'enabled': False, 'reason': 'invalid-state'}

    def set(self, enabled: bool, reason='') -> dict[str, Any]:
        row = {'enabled': bool(enabled), 'reason': scrub_text(reason), 'updated_at': time.time()}
        with self._lock:
            self.path.write_text(json.dumps(row, indent=2, ensure_ascii=False))
        return row


class DeploymentLock:
    def __init__(self, path='data/production/deploy.lock'):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.fd = None

    def acquire(self) -> bool:
        try:
            import fcntl
            self.fd = self.path.open('a+')
            fcntl.flock(self.fd.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            self.fd.write(f'{os.getpid()} {time.time()}\n'); self.fd.flush()
            return True
        except (BlockingIOError, OSError):
            return False

    def release(self):
        if self.fd:
            try:
                import fcntl
                fcntl.flock(self.fd.fileno(), fcntl.LOCK_UN)
            finally:
                self.fd.close(); self.fd = None


@dataclass
class CircuitBreaker:
    failure_threshold: int = 5
    reset_seconds: int = 60
    failures: int = 0
    opened_at: float | None = None
    _lock: threading.Lock = field(default_factory=threading.Lock, repr=False)

    def allow(self) -> bool:
        with self._lock:
            if self.opened_at is None:
                return True
            if time.time() - self.opened_at >= self.reset_seconds:
                self.failures = 0; self.opened_at = None
                return True
            return False

    def record(self, success: bool):
        with self._lock:
            if success:
                self.failures = 0; return
            self.failures += 1
            if self.failures >= self.failure_threshold:
                self.opened_at = time.time()


@dataclass
class CanaryGate:
    stages: list[int]
    minimum_sample: int = 10
    max_error_rate: float = 0.05
    max_latency_ratio: float = 1.25

    def evaluate_stage(self, baseline: dict[str, Any], candidate: dict[str, Any], percent: int) -> dict[str, Any]:
        b_err = float(baseline.get('error_rate', 0)); c_err = float(candidate.get('error_rate', 0))
        b_lat = max(float(baseline.get('p95_latency_ms', 1)), 1.0); c_lat = float(candidate.get('p95_latency_ms', 0))
        n = int(candidate.get('n', 0))
        passed = n >= self.minimum_sample and c_err <= max(self.max_error_rate, b_err + self.max_error_rate) and (c_lat / b_lat) <= self.max_latency_ratio
        return {'traffic_percent': percent, 'sample_count': n, 'baseline_error_rate': b_err, 'candidate_error_rate': c_err,
                'latency_ratio': c_lat / b_lat, 'passed': passed}


def route_percent(key: str, percent: int) -> bool:
    bucket = int(hashlib.sha256(key.encode()).hexdigest()[:8], 16) % 100
    return bucket < max(0, min(percent, 100))


def run_trusted_command(command: str, cwd: str | Path, env: dict[str, str] | None = None, timeout=900) -> dict[str, Any]:
    if not command:
        return {'returncode': 0, 'stdout': '', 'stderr': '', 'skipped': True}
    p = run_trusted_command(command, cwd=str(cwd), env=env or os.environ.copy(), timeout=timeout, allow_shell=True)
    return {'returncode': p.returncode, 'stdout': scrub_text(p.stdout[-8000:]), 'stderr': scrub_text(p.stderr[-8000:])}
