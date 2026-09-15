from __future__ import annotations
import threading, time
from dataclasses import dataclass
from typing import Any, Callable

@dataclass
class _Entry:
    value: Any
    expires: float

class TTLCache:
    def __init__(self, ttl_seconds: float = 30.0, max_items: int = 2048):
        self.ttl = max(0.1, float(ttl_seconds)); self.max_items = max(16, int(max_items)); self._data: dict[str,_Entry] = {}; self._lock = threading.RLock()
    def get(self, key: str, default=None):
        with self._lock:
            e = self._data.get(key); now=time.time()
            if not e: return default
            if e.expires <= now:
                self._data.pop(key,None); return default
            return e.value
    def set(self,key,value,ttl=None):
        with self._lock:
            if len(self._data) >= self.max_items:
                self._data.pop(next(iter(self._data)),None)
            self._data[key] = _Entry(value,time.time()+(self.ttl if ttl is None else max(0.1,float(ttl))))
            return value
    def get_or_set(self,key,fn:Callable[[],Any],ttl=None):
        v=self.get(key,None)
        if v is not None:return v
        return self.set(key,fn(),ttl)
    def invalidate(self,prefix=''):
        with self._lock:
            if not prefix:self._data.clear()
            else:
                for k in list(self._data):
                    if k.startswith(prefix):self._data.pop(k,None)
    def stats(self):
        with self._lock:return {'items':len(self._data),'max_items':self.max_items,'ttl_seconds':self.ttl}
