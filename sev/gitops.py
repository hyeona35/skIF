from __future__ import annotations
import subprocess
from pathlib import Path
class GitError(RuntimeError): pass
def run_git(repo,*args,check=True):
    p=subprocess.run(['git',*args],cwd=repo,text=True,capture_output=True)
    if check and p.returncode: raise GitError(p.stderr.strip() or p.stdout.strip())
    return p.stdout.strip()
def ensure_repo(repo):
    if not (repo/'.git').exists():
        run_git(repo,'init'); run_git(repo,'add','.'); subprocess.run(['git','-c','user.name=skIF','-c','user.email=skif@localhost','commit','-m','chore: initialize skill'],cwd=repo,text=True,capture_output=True)
def clean(repo): return run_git(repo,'status','--porcelain')==''
def head(repo): return run_git(repo,'rev-parse','HEAD')
def branch(repo): return run_git(repo,'branch','--show-current')
def worktree_add(repo,path,ref): Path(path).parent.mkdir(parents=True,exist_ok=True); run_git(repo,'worktree','add','--detach',str(path),ref)
def worktree_remove(repo,path): subprocess.run(['git','worktree','remove','--force',str(path)],cwd=repo,text=True,capture_output=True)
def commit_all(repo,msg):
    run_git(repo,'add','.')
    p=subprocess.run(['git','-c','user.name=skIF Agent','-c','user.email=agent@localhost','commit','-m',msg],cwd=repo,text=True,capture_output=True)
    if p.returncode and 'nothing to commit' not in (p.stdout or ''): raise GitError(p.stderr.strip() or p.stdout.strip() or 'commit failed')
    return head(repo)
def cherry_pick(repo,commit):
    p=subprocess.run(['git','-c','user.name=skIF Promoter','-c','user.email=promoter@localhost','cherry-pick',commit],cwd=repo,text=True,capture_output=True)
    if p.returncode: raise GitError(p.stderr.strip() or p.stdout.strip() or 'cherry-pick failed')
    return head(repo)
