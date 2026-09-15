from __future__ import annotations
import time
from dataclasses import dataclass
import os
from .exec_policy import run_trusted_command

def _run(cmd,cwd,env,timeout):
    p=run_trusted_command(cmd,cwd=cwd,env=env or os.environ.copy(),timeout=timeout,allow_shell=True)
    return {"returncode":p.returncode,"stdout":p.stdout[-8000:],"stderr":p.stderr[-8000:]}

@dataclass
class CanaryResult:
    enabled: bool
    stages: list[dict]
    passed: bool
    rolled_back: bool


def run_canary(cfg, skill_dir, run_dir, stages=None, smoke_command=None, rollback_command=None):
    if not getattr(cfg,'enabled',False):
        return CanaryResult(False,[],True,False).__dict__
    stages = stages or getattr(cfg,'stages',[1,5,25,50,100])
    out=[]; ok=True; rolled=False
    for pct in stages:
        stage={'traffic_percent':pct,'started_at':time.time()}
        if smoke_command:
            r=_run(smoke_command,skill_dir,{'SKIF_CANARY_PERCENT':str(pct),'SKIF_SKILL_DIR':str(skill_dir),'SKIF_RUN_DIR':str(run_dir)},getattr(cfg,'timeout_seconds',900))
            stage['check']=r; stage['passed']=r['returncode']==0
        else:
            stage['passed']=True
        stage['ended_at']=time.time(); out.append(stage)
        if not stage['passed']:
            ok=False
            if rollback_command:
                rr=_run(rollback_command,skill_dir,{},getattr(cfg,'timeout_seconds',900)); stage['rollback']=rr; rolled=rr['returncode']==0 or rolled
            break
    return CanaryResult(True,out,ok,rolled).__dict__
