from __future__ import annotations
import argparse,json
from pathlib import Path
from .config import *

def yn(q,d=True):
 s=input(f'{q} [{"Y/n" if d else "y/N"}]: ').strip().lower(); return d if not s else s.startswith('y')

def onboarding(_):
 c=load_config(); print('=== skIF onboarding ===')
 while True:
  more=yn('Configure another provider?',not bool(c.providers))
  if not more: break
  t={'1':'openai','2':'claude','3':'custom'}.get(input('Type 1=OpenAI 2=Claude 3=Custom: ').strip(),'openai'); name=input('Profile name: ').strip() or f'{t}-{len(c.providers)+1}'
  model=input('Model: ').strip() or ('gpt-5.6' if t=='openai' else 'claude-sonnet-4-6' if t=='claude' else 'custom')
  env=input('API key env: ').strip() or ('OPENAI_API_KEY' if t=='openai' else 'ANTHROPIC_API_KEY' if t=='claude' else 'CUSTOM_API_KEY')
  endpoint=input('Endpoint (blank=default): ').strip(); compat='native'
  if t=='custom': compat={'1':'openai','2':'anthropic','3':'native'}.get(input('Custom protocol 1=OpenAI-compatible 2=Anthropic-compatible 3=native: ').strip(),'openai')
  c.providers[name]=ProviderConfig(name,t,model,env,endpoint,compat)
 names=list(c.providers); same=yn('Use the same provider for every core role?',True)
 if same:
  n=input(f'Provider [{names[0]}]: ').strip() or names[0]
  for r in ROLES: c.roles[r]=RoleConfig([n],True,r=='judge')
 else:
  for r in ROLES:
   ns=input(f'{r} providers (comma-separated, blank disables): ').strip(); c.roles[r]=RoleConfig([x.strip() for x in ns.split(',') if x.strip()],bool(ns),r=='judge')
 c.voting_enabled=yn('Enable VOTE?',True); c.vote_mode='pairwise' if input('Vote mode 1=pairwise 2=pointwise [1]: ').strip()!='2' else 'pointwise'; c.submission_mode={'1':'feedback_only','2':'patch_only','3':'feedback_or_patch'}[input('Agent authority 1=feedback 2=patch 3=both [3]: ').strip() or '3']; c.patch_mode='auto' if yn('Auto-create patches from feedback?',False) else 'approval'
 c.alternatives=int(input('Alternatives [4]: ') or 4); c.budget.max_generations=int(input('Generations [2]: ') or 2); c.budget.max_parallel=int(input('Parallel [4]: ') or 4); c.vote_threshold=float(input('Vote threshold [0.5]: ') or .5); c.pareto_enabled=yn('Use Pareto frontier?',True); c.battle.enabled=yn('Run Red/Blue battle before promotion?',True)
 c.runtime.mode='subprocess' if yn('Use an external Agent runtime?',False) else 'provider'; c.runtime.command=input('Runtime command (blank if provider): ').strip(); c.require_human_approval_to_promote=yn('Human approval before promotion?',True)
 c.errors.absolute_threshold=int(input('Error review threshold [5]: ') or 5); c.errors.delta_threshold=float(input('Error delta threshold [0.5]: ') or .5); c.methodology.auto_collect=yn('Collect reusable methodologies?',True); c.proposals.enabled=yn('Enable Agent Skill proposals?',True); c.methodology.gist_publication=yn('Publish methodologies as GitHub Gists?',False); save_config(c); print('Saved:',CONFIG_PATH)

def main():
 p=argparse.ArgumentParser(prog='skif'); s=p.add_subparsers(dest='cmd',required=True); q=s.add_parser('onboarding');q.set_defaults(fn=onboarding); q=s.add_parser('doctor');q.set_defaults(fn=lambda a:print(json.dumps(load_config().to_json(),indent=2,ensure_ascii=False))); q=s.add_parser('serve');q.add_argument('--host',default='127.0.0.1');q.add_argument('--port',type=int,default=8787);q.set_defaults(fn=lambda a:__import__('sev.api',fromlist=['serve']).serve(a.host,a.port));q=s.add_parser('evolve');q.add_argument('--skill',required=True);q.add_argument('--suite',required=True);q.add_argument('--feedback');q.add_argument('--patch');q.add_argument('--alternatives',type=int);q.add_argument('--promote',action='store_true');q.add_argument('--force',action='store_true');q.add_argument('--generations',type=int);q.set_defaults(fn=evolve); args=p.parse_args(); args.fn(args)

def evolve(a):
 from .evolution import EvolutionEngine
 c=load_config();fb=json.loads(Path(a.feedback).read_text()) if a.feedback else None;pt=json.loads(Path(a.patch).read_text()) if a.patch else None; print(json.dumps(EvolutionEngine(c,Path(c.artifacts_dir)).run(Path(a.skill),Path(a.suite),feedback=fb,agent_patch=pt,alternatives=a.alternatives,promote=a.promote,force_approval=a.force,generations=a.generations),indent=2,ensure_ascii=False,default=str))
