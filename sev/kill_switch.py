from __future__ import annotations
import json, time
from pathlib import Path
class KillSwitchRegistry:
    TYPES=('global','host','agent','federation','deployment','research','evolution','skill')
    def __init__(self,path='data/production/kill_switch.json'):
        self.path=Path(path);self.path.parent.mkdir(parents=True,exist_ok=True)
    def _load(self):
        if not self.path.exists():return {k:{'enabled':False,'reason':'','updated_at':0} for k in self.TYPES}
        x=json.loads(self.path.read_text());
        for k in self.TYPES:x.setdefault(k,{'enabled':False,'reason':'','updated_at':0})
        return x
    def set(self,scope,enabled,reason='',actor='host'):
        if scope not in self.TYPES:raise ValueError('invalid kill-switch scope')
        x=self._load();x[scope]={'enabled':bool(enabled),'reason':str(reason),'updated_at':time.time(),'actor':actor};self.path.write_text(json.dumps(x,indent=2));return x[scope]
    def status(self):return self._load()
    def blocked(self,scope):
        x=self._load();return bool(x.get('global',{}).get('enabled') or x.get(scope,{}).get('enabled'))
