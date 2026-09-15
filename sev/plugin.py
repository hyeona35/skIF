from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class PluginRegistry:
    plugins:dict[str,object]=field(default_factory=dict)
    def register(self,name,plugin):
        if not name or plugin is None:raise ValueError('plugin name/object required')
        self.plugins[name]=plugin; return {'name':name,'registered':True}
    def get(self,name): return self.plugins.get(name)
    def names(self): return sorted(self.plugins)
    def health(self):
        out={}
        for k,v in self.plugins.items():
            try: out[k]={'ok':bool(getattr(v,'health',lambda:True)())}
            except Exception as e: out[k]={'ok':False,'error':str(e)}
        return out
