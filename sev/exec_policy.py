from __future__ import annotations
import os, shlex, subprocess
from pathlib import Path

class TrustedExecutionError(RuntimeError): pass

def run_trusted_command(command,cwd=None,env=None,timeout=900,allow_shell=True):
    """Execute only a Host-configured command. Model output must never be passed here."""
    if not isinstance(command,str) or not command.strip(): raise TrustedExecutionError('trusted command is empty')
    if not allow_shell: args=shlex.split(command)
    else: args=command
    safe_env=os.environ.copy();
    if env: safe_env.update({str(k):str(v) for k,v in env.items()})
    return subprocess.run(args,cwd=str(Path(cwd).resolve()) if cwd else None,shell=bool(allow_shell),text=True,capture_output=True,env=safe_env,timeout=int(timeout))
