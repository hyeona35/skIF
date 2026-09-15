from .config import FrameworkConfig
from .providers import make_provider

def role_providers(c,role):
    cfg=c.roles.get(role)
    if not cfg or not cfg.enabled: return []
    return [(name,make_provider(c.providers[name])) for name in cfg.providers if name in c.providers]

def role_provider_pool(c,role): return [p for _,p in role_providers(c,role)]

def ensure_roles(c):
    missing=[r for r in ("worker","critic","improver") if c.roles.get(r) and c.roles[r].enabled and not c.roles[r].providers]
    if missing: raise ValueError('No provider configured for: '+', '.join(missing))
