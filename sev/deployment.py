from __future__ import annotations
import os
from .exec_policy import run_trusted_command
from pathlib import Path
from .config import DeploymentConfig
from .canary import run_canary
from .production import DeploymentLock,KillSwitch,scrub

def _run(cmd,cwd,env,timeout):
    p=run_trusted_command(cmd,cwd=cwd,env=env,timeout=timeout,allow_shell=True)
    return {'returncode':p.returncode,'stdout':scrub(p.stdout[-8000:]),'stderr':scrub(p.stderr[-8000:])}

def deploy(cfg:DeploymentConfig,skill_dir,run_dir,approved=False,canary_cfg=None,production_cfg=None):
    if not cfg.enabled:return {'attempted':False,'reason':'disabled'}
    if cfg.require_approval and not approved:return {'attempted':False,'reason':'approval_required'}
    if not cfg.command:return {'attempted':False,'reason':'missing_deploy_command'}
    lock=DeploymentLock(getattr(production_cfg,'deployment_lock_path','data/production/deploy.lock') if production_cfg else 'data/production/deploy.lock')
    kill=KillSwitch(getattr(production_cfg,'kill_switch_path','data/production/kill_switch.json') if production_cfg else 'data/production/kill_switch.json')
    if kill.status().get('enabled'):return {'attempted':False,'reason':'kill_switch_enabled'}
    if not lock.acquire():return {'attempted':False,'reason':'deployment_lock_busy'}
    try:
        env=os.environ.copy(); env.update({'SKIF_SKILL_DIR':str(Path(skill_dir).resolve()),'SKIF_RUN_DIR':str(Path(run_dir).resolve())})
        main=_run(cfg.command,skill_dir,env,cfg.timeout_seconds); result={'attempted':True,'deploy':main,'smoke_test':None,'rollback':None,'canary':None,'rolled_back':False}
        if main['returncode']==0 and cfg.smoke_test_command:
            smoke=_run(cfg.smoke_test_command,skill_dir,env,cfg.timeout_seconds); result['smoke_test']=smoke
            if smoke['returncode']!=0 and cfg.rollback_command:
                result['rollback']=_run(cfg.rollback_command,skill_dir,env,cfg.timeout_seconds); result['rolled_back']=True
        if main['returncode']==0 and canary_cfg is not None and getattr(canary_cfg,'enabled',False):
            if canary_cfg.require_approval and not approved: result['canary']={'enabled':True,'passed':False,'reason':'canary approval required','stages':[],'rolled_back':False}
            else: result['canary']=run_canary(canary_cfg,skill_dir,run_dir,smoke_command=cfg.smoke_test_command,rollback_command=cfg.rollback_command)
            if result['canary'] and not result['canary']['passed']: result['rolled_back']=result['canary'].get('rolled_back',False)
        return result
    finally: lock.release()
