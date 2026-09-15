from __future__ import annotations
import json, urllib.request
from dataclasses import dataclass, field
from typing import Any
from .config import ProviderConfig, get_api_key

@dataclass
class ProviderResult:
    text: str
    raw: dict[str,Any]
    usage: dict[str,Any]=field(default_factory=dict)
    tool_calls: list[dict[str,Any]]=field(default_factory=list)

class ProviderError(RuntimeError): pass

def _request(url,headers,payload):
    req=urllib.request.Request(url,data=json.dumps(payload).encode(),headers=headers,method='POST')
    try:
        with urllib.request.urlopen(req,timeout=300) as r: return json.loads(r.read().decode())
    except Exception as e: raise ProviderError(str(e)) from e

def _openai_text(raw):
    if raw.get('output_text'): return raw['output_text']
    parts=[]
    for item in raw.get('output',[]):
        for c in item.get('content',[]):
            if c.get('type') in ('output_text','text') and c.get('text'): parts.append(c['text'])
    return '\n'.join(parts)

def _anthropic_text(raw): return '\n'.join(b.get('text','') for b in raw.get('content',[]) if b.get('type')=='text')

def make_provider(cfg): return Provider(cfg)

class Provider:
    def __init__(self,cfg): self.config=cfg
    def generate(self,system,prompt)->ProviderResult:
        key=get_api_key(self.config); compat=self.config.api_compat if self.config.kind=='custom' else self.config.kind
        if compat in ('openai','claude','anthropic') and not key: raise ProviderError(f'Missing API key: {self.config.api_key_env}')
        if compat=='openai':
            url=self.config.endpoint or 'https://api.openai.com/v1/responses'
            payload={'model':self.config.model,'instructions':system,'input':prompt,'max_output_tokens':self.config.max_tokens}
            if self.config.temperature is not None: payload['temperature']=self.config.temperature
            raw=_request(url,{'Authorization':f'Bearer {key}','Content-Type':'application/json',**self.config.headers},payload)
            return ProviderResult(_openai_text(raw).strip(),raw,raw.get('usage',{}),raw.get('tool_calls',[]) or [])
        if compat in ('claude','anthropic'):
            url=self.config.endpoint or 'https://api.anthropic.com/v1/messages'
            raw=_request(url,{'x-api-key':key,'anthropic-version':'2023-06-01','Content-Type':'application/json',**self.config.headers},{'model':self.config.model,'max_tokens':self.config.max_tokens,'system':system,'messages':[{'role':'user','content':prompt}]})
            return ProviderResult(_anthropic_text(raw).strip(),raw,raw.get('usage',{}),raw.get('tool_calls',[]) or [])
        if self.config.kind=='custom':
            if not self.config.endpoint: raise ProviderError('Custom provider requires endpoint')
            headers={'Content-Type':'application/json',**self.config.headers}
            if key: headers.setdefault('Authorization',f'Bearer {key}')
            raw=_request(self.config.endpoint,headers,{'model':self.config.model,'system':system,'prompt':prompt,'max_tokens':self.config.max_tokens})
            text=raw.get('text') or raw.get('output') or raw.get('response') or ''
            return ProviderResult(str(text),raw,raw.get('usage',{}),raw.get('tool_calls',[]) or [])
        raise ProviderError(f'Unsupported provider kind/compat: {self.config.kind}/{compat}')
