from __future__ import annotations
import os
from .providers import Provider
from .prompts import METHODOLOGY_SYSTEM, methodology_prompt
from .registry import add_methodology
from .github import create_gist

def curate_observation(provider:Provider, observation, registry_dir, github=None):
    raw=provider.generate(METHODOLOGY_SYSTEM, methodology_prompt(observation)).text.strip()
    item={'title':'','content':raw}
    try:
        import json
        d=json.loads(raw); item.update({k:d[k] for k in ('title','content','tags') if k in d})
    except Exception: pass
    saved=add_methodology(registry_dir,item.get('title') or 'Agent-derived methodology',item.get('content') or raw,provider.config.name,item.get('tags',[]))
    gist=None
    if github and github.get('enabled') and github.get('token') and github.get('publish'):
        gist=create_gist(github['token'],{'METHODOLOGY.md':saved['content']},saved['title'],False)
        saved['gist_url']=gist.get('html_url')
    return saved
