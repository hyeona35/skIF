from __future__ import annotations
import json, os
from .exec_policy import run_trusted_command
from dataclasses import dataclass,field
from pathlib import Path
from .providers import Provider

@dataclass
class ToolCall:
    name:str; arguments:dict|str; result:object=None; duration_ms:float|None=None
@dataclass
class AgentTrace:
    output:str
    tool_calls:list[ToolCall]=field(default_factory=list)
    events:list[dict]=field(default_factory=list)
    usage:dict=field(default_factory=dict)

class AgentRuntimeError(RuntimeError): pass

class AgentRuntime:
    def run(self,skill_dir:Path,task:dict,provider:Provider|None=None,methodologies=None)->AgentTrace: raise NotImplementedError

class ProviderRuntime(AgentRuntime):
    def __init__(self, system='You are a skIF Worker agent.'):
        self.system=system
    def run(self,skill_dir,task,provider=None,methodologies=None):
        if provider is None: raise AgentRuntimeError('ProviderRuntime requires a provider')
        prompt=json.dumps({'skill_dir':str(skill_dir),'skill_files':_skill_text(skill_dir),'task':task,'methodologies':methodologies or []},ensure_ascii=False)
        r=provider.generate(self.system,prompt)
        calls=[ToolCall(c.get('name','unknown'),c.get('arguments',{}),c.get('result')) for c in r.tool_calls if isinstance(c,dict)]
        return AgentTrace(r.text,calls,[{'type':'provider_response'}],r.usage or {})

class SubprocessRuntime(AgentRuntime):
    def __init__(self,command,timeout=900): self.command=command; self.timeout=timeout
    def run(self,skill_dir,task,provider=None,methodologies=None):
        if not self.command: raise AgentRuntimeError('Runtime command is not configured')
        env=os.environ.copy(); env['SKIF_SKILL_DIR']=str(skill_dir); env['SKIF_TASK_JSON']=json.dumps(task,ensure_ascii=False); env['SKIF_METHODOLOGIES_JSON']=json.dumps(methodologies or [],ensure_ascii=False)
        p=run_trusted_command(self.command,cwd=skill_dir,env=env,timeout=self.timeout,allow_shell=True)
        if p.returncode: raise AgentRuntimeError(p.stderr.strip() or f'agent runtime exited {p.returncode}')
        try: raw=json.loads(p.stdout)
        except json.JSONDecodeError as e: raise AgentRuntimeError('Runtime must return JSON') from e
        calls=[ToolCall(x.get('name','unknown'),x.get('arguments',{}),x.get('result'),x.get('duration_ms')) for x in raw.get('tool_calls',[]) if isinstance(x,dict)]
        return AgentTrace(str(raw.get('output','')),calls,raw.get('events',[]),raw.get('usage',{}))

def _skill_text(root):
    root=Path(root); parts=[]
    for p in sorted(root.rglob('*')):
        if p.is_file() and '.git' not in p.parts:
            try: parts.append(f'===== {p.relative_to(root)} =====\n{p.read_text()}')
            except UnicodeDecodeError: pass
    return '\n\n'.join(parts)
