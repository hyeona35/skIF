from __future__ import annotations
import json,shutil,subprocess,hashlib,datetime
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
from .config import FrameworkConfig
from .roles import ensure_roles,role_provider_pool
from .skill import snapshot
from .gitops import *
from .agent import evaluate_skill
from .evals import load_suite,append_case
from .deployment import deploy
from .provenance import snapshot_hash,write_attestation
from .prompts import *
from .battle import red_blue_battle
from .errors import recent_errors,review_signal
from .registry import list_methodologies,add_methodology,propose_skill
from .dataset import strengthen_suite, suite_case_count
from .graph import analyze as analyze_skill_graph
from .shadow import ShadowEngine, load_requests
from .stats import paired_bootstrap
from .compatibility import discover_interactions, evaluate_cross_skill_compat
from .judge import calibrate_judges
from .review import ReviewQueue
from .eventstore import EventStore
from .runtime import ProviderRuntime, SubprocessRuntime
from .production import KillSwitch
from .knowledge import KnowledgeGraph
from .reputation import ReputationEngine

class EvolutionError(RuntimeError): pass

def _json(text):
 t=text.strip()
 if t.startswith('```'): t=t.split('\n',1)[1].rsplit('```',1)[0]
 return json.loads(t)

def role_providers(config): return {r: role_provider_pool(config,r) for r in ('worker','critic','improver','judge','red_team','blue_team','reviewer')}

class EvolutionEngine:
    def __init__(self,config,artifacts):
        self.config=config; self.artifacts=Path(artifacts); self.artifacts.mkdir(parents=True,exist_ok=True); ensure_roles(config); self.events=EventStore(getattr(config,'event_store','data/events.db')); self.reputation=ReputationEngine(self.events,getattr(getattr(config,'reputation',None),'freshness_halflife_days',30.0)); self.knowledge=KnowledgeGraph(config.knowledge.path) if getattr(config,'knowledge',None) and config.knowledge.enabled else None
        if self.knowledge:
            self.knowledge.bulk_ingest(self.events.recent(5000)); self.events.subscribe(self.knowledge.ingest_event)
        pools=role_providers(config); self.pools={r:(v if isinstance(v,list) else [v]) for r,v in pools.items()}
        for r in ('worker','critic','improver'):
            if config.roles.get(r) and config.roles[r].enabled and not self.pools[r]: raise EvolutionError(f'No active provider for {r}')
        for r in ('judge','red_team','blue_team','reviewer'): self.pools.setdefault(r,[])
    def skill_text(self,root):
        s=snapshot(Path(root)); return '\n\n'.join(f'===== {p} =====\n{v["content"]}' for p,v in sorted(s['files'].items(),key=lambda x:(x[0]!='SKILL.md',x[0])))
    def _methodologies(self): return list_methodologies(self.config.registry_dir) if self.config.methodology.enabled else []
    def critique(self,root,task,output): return _json(self.pools['critic'][0].generate(CRITIC_SYSTEM,critic_prompt(self.skill_text(root),task,output)).text)
    def proposals(self,root,feedback,count):
        out=[]; base=self.skill_text(root); ps=self.pools['improver']; methods=self._methodologies()
        def one(i): return _json(ps[i%len(ps)].generate(IMPROVER_SYSTEM,improver_prompt(base,feedback,i+1,count,methods)).text)
        with ThreadPoolExecutor(max_workers=min(len(ps),max(1,count))) as ex: out=list(ex.map(one,range(count)))
        return out
    def apply_proposal(self,root,proposal):
        root=Path(root)
        for x in proposal.get('files',[]):
            rel=Path(x['path'])
            if rel.is_absolute() or '..' in rel.parts or str(rel).startswith('.git'): raise EvolutionError(f'unsafe patch path: {rel}')
            p=(root/rel).resolve()
            if root.resolve() not in p.parents and p != root.resolve(): raise EvolutionError(f'unsafe patch path: {rel}')
            op=x.get('operation','replace'); p.parent.mkdir(parents=True,exist_ok=True)
            if op=='replace': p.write_text(x.get('content',''))
            elif op=='append': p.open('a').write(x.get('content',''))
            elif op=='insert_after':
                t=p.read_text(); a=x.get('anchor','')
                if a not in t: raise EvolutionError(f'anchor not found: {x["path"]}')
                p.write_text(t.replace(a,a+'\n'+x.get('content',''),1))
            elif op=='delete' and p.exists(): p.unlink()
            else: raise EvolutionError(f'unsupported operation {op}')
    def _baseline(self,skill):
        ensure_repo(skill)
        if self.config.use_git and not clean(skill): raise EvolutionError('Dirty working tree: commit/stash baseline changes before evolution.')
        return head(skill) if self.config.use_git else ''
    def _candidate(self,run_dir,skill,ref,label,proposal):
        dest=run_dir/'worktrees'/label
        if self.config.use_git and self.config.create_worktrees:
            worktree_add(skill,dest,ref); self.apply_proposal(dest,proposal); commit=commit_all(dest,f'skIF(candidate): {label}')
        else: shutil.copytree(skill,dest); self.apply_proposal(dest,proposal); commit=''
        if self.config.use_git and commit:
            patch_bytes=subprocess.run(['git','show','--format=','--binary',commit],cwd=skill,capture_output=True).stdout; (run_dir/f'{label}.patch').write_bytes(patch_bytes)
        return {'index':int(label.rsplit('-c',1)[1]),'label':label,'dir':str(dest),'commit':commit,'proposal':proposal}
    def _eval_candidate(self,candidate,suite,base_eval):
        ev=evaluate_skill(self.pools['worker'][0],self.pools['critic'],Path(candidate['dir']),self.skill_text(candidate['dir']),suite,methodologies=self._methodologies())
        ev['regressions']=[r['id'] for b,r in zip(base_eval['cases'],ev['cases']) if r['score']+1e-9 < b['score']]
        candidate['cost']=float(ev['usage'].get('estimated_cost_usd',0)); candidate['tokens']=int(ev['usage'].get('total_tokens',0));
        candidate['diff_size']=len(json.dumps(candidate['proposal'],ensure_ascii=False))
        return {'candidate':candidate,'eval':ev}
    def _pareto(self,scored):
        if not scored: return []
        frontier=[]
        for a in scored:
            am=(a['eval']['score'],-a['candidate'].get('cost',0),-a['candidate'].get('tokens',0),-a['candidate'].get('diff_size',0), -len(a['eval']['regressions']))
            dominated=False
            for b in scored:
                if a is b: continue
                bm=(b['eval']['score'],-b['candidate'].get('cost',0),-b['candidate'].get('tokens',0),-b['candidate'].get('diff_size',0),-len(b['eval']['regressions']))
                if all(y>=x for x,y in zip(am,bm)) and any(y>x for x,y in zip(am,bm)): dominated=True; break
            if not dominated: frontier.append(a['candidate']['index'])
        return frontier
    def _calibrate_judges(self):
        if not self.pools['judge']: return {'enabled':False,'eligible':[]}
        gold=Path(getattr(self.config,'judge_gold_suite','evals/gold.json'))
        if not gold.exists(): return {'enabled':False,'eligible':[p.config.name for p in self.pools['judge']]}
        cases=load_suite(gold)
        return calibrate_judges(self.pools['judge'],cases,min_score=getattr(self.config,'judge_min_calibration',0.75))
    def _judge_weight(self, provider):
        role_weight=next((float(r.vote_weight) for r in self.config.roles.values() if provider.config.name in r.providers),1.0)
        rep=self.reputation.score(provider.config.name) if self.config.reputation.enabled else {'judge_weight':1.0}
        # Do not zero-out an otherwise valid Judge; reputation only modulates influence within a bounded range.
        return role_weight * min(2.0,max(0.25,float(rep.get('judge_weight',1.0))))

    def _vote(self,base_eval,scored,feedback=None):
        if not self.config.voting_enabled or not self.pools['judge']:
            ranked=sorted(range(len(scored)),key=lambda i:(scored[i]['eval']['score'],-scored[i]['cost'],-scored[i]['tokens']),reverse=True)
            return {'enabled':False,'mode':'none','winner':ranked[0] if ranked else None,'vote_share':1.0 if ranked else 0.0,'accepted_by_vote':True,'ballots':[]}
        calibration=self._calibrate_judges()
        active=[p for p in self.pools['judge'] if p.config.name in calibration.get('eligible', [p.config.name for p in self.pools['judge']])] if calibration.get('enabled',False) else self.pools['judge']
        if self.config.voting_enabled and self.pools['judge'] and calibration.get('enabled') and not active:
            return {'enabled':True,'mode':self.config.vote_mode,'ballots':[],'vote_scores':{},'winner':None,'vote_share':0.0,'accepted_by_vote':False,'calibration':calibration}
        ballots=[]
        if len(scored) <= 1:
            return {'enabled':True,'mode':self.config.vote_mode,'ballots':[],'vote_scores':{0:1.0} if scored else {},'winner':0 if scored else None,'vote_share':1.0 if scored else 0.0,'accepted_by_vote':bool(scored)}
        if self.config.vote_mode=='pairwise':
            for i,a in enumerate(scored):
                for j,b in enumerate(scored):
                    if i>=j: continue
                    for p in active:
                        try: d=_json(p.generate(JUDGE_SYSTEM,judge_prompt(base_eval,[a['eval'],b['eval']],feedback,'pairwise')).text)
                        except Exception as e: d={'winner':None,'confidence':0,'reason':str(e)}
                        ballots.append({'a':i,'b':j,'judge':p.config.name,**d})
            score={i:0.0 for i in range(len(scored))}
            for b in ballots:
                w=b.get('winner', b.get('candidate')); conf=float(b.get('confidence',b.get('score',1)) or 0)
                weight=self._judge_weight(next((p for p in active if p.config.name==b.get('judge')),active[0] if active else None)) if active else 1.0
                if w in ('a',0): score[b['a']]+=conf*weight
                elif w in ('b',1): score[b['b']]+=conf*weight
                elif isinstance(w,int) and w in score: score[w]+=conf*weight
            ranked=sorted(score,key=score.get,reverse=True); winner=ranked[0] if ranked else None; total=sum(score.values()) or 1; share=score[winner]/total if winner is not None else 0
            return {'enabled':True,'mode':'pairwise','ballots':ballots,'vote_scores':score,'winner':winner,'vote_share':share,'accepted_by_vote':share>=self.config.vote_threshold,'calibration':calibration}
        for i,a in enumerate(scored):
            for p in active:
                try: d=_json(p.generate(JUDGE_SYSTEM,judge_prompt(base_eval,[a['eval']],feedback,'pointwise')).text)
                except Exception as e: d={'decision':'reject','score':0,'confidence':0,'reason':str(e)}
                ballots.append({'candidate':i,'judge':p.config.name,**d})
        score={i:0.0 for i in range(len(scored))}
        for b in ballots:
            provider=next((p for p in active if p.config.name==b.get('judge')),active[0] if active else None)
            score[b['candidate']]+=float(b.get('score',b.get('confidence',0)))* (self._judge_weight(provider) if provider else 1.0)
        ranked=sorted(score,key=score.get,reverse=True); winner=ranked[0] if ranked else None; total=sum(score.values()) or 1; share=score[winner]/total if winner is not None else 0
        return {'enabled':True,'mode':'pointwise','ballots':ballots,'vote_scores':score,'winner':winner,'vote_share':share,'accepted_by_vote':share>=self.config.vote_threshold,'calibration':calibration}
    def _grow_corpus(self,suite_path,feedback,run_dir):
        if not self.config.corpus_growth or not self.config.convert_feedback_to_evals or not feedback: return
        f=feedback.get('suggested_eval')
        if f:
            try: case=json.loads(f) if isinstance(f,str) else f
            except: case=None
            if case and 'id' in case and 'prompt' in case:
                from .eval_guard import stage_case
                staged=stage_case(self.config.registry_dir,case,source='feedback')
                if staged['validation']['accepted']:
                    ReviewQueue(Path(self.config.registry_dir)/'reviews').enqueue('eval',staged,priority='normal',reason='Agent feedback generated a new evaluation case')
                (run_dir/'corpus-growth.json').write_text(json.dumps(staged,indent=2,ensure_ascii=False))
    def _strengthen_dataset(self, suite_path, incoming_skills, run_dir):
        if not self.config.dataset.auto_generate_from_skills or not incoming_skills or not self.pools['critic']:
            return None
        if suite_case_count(suite_path) > 0:
            return {'added': 0, 'count': suite_case_count(suite_path), 'skipped': 'existing_corpus'}
        result = strengthen_suite(self.pools['critic'], [str(x) for x in incoming_skills], suite_path, self.config.dataset.cases_per_skill)
        (run_dir/'dataset-strengthening.json').write_text(json.dumps(result, indent=2, ensure_ascii=False))
        return result

    def _error_review(self,skill_name,run_dir):
        if not self.config.errors.enabled or not self.config.errors.auto_review or not self.pools['reviewer']: return None
        errs=recent_errors(self.config.registry_dir,skill_name,self.config.errors.window_minutes); sig=review_signal(errs,self.config.errors.absolute_threshold,self.config.errors.delta_threshold)
        if not sig['review']: return {'signal':sig,'review':None}
        reviews=[]
        for p in self.pools['reviewer']:
            try: reviews.append({'reviewer':p.config.name,**_json(p.generate(REVIEWER_SYSTEM,error_review_prompt(errs)).text)})
            except Exception as e: reviews.append({'reviewer':p.config.name,'error':str(e)})
        out={'signal':sig,'review':reviews}; (run_dir/'error-review.json').write_text(json.dumps(out,indent=2,ensure_ascii=False)); return out
    def run(self,skill_dir,suite_path,feedback=None,agent_patch=None,alternatives=None,promote=False,force_approval=False,generations=None,incoming_skills=None):
        skill=Path(skill_dir); suite_path=Path(suite_path); rid=datetime.datetime.now().strftime('%Y%m%dT%H%M%S%fZ'); run=self.artifacts/rid; run.mkdir(parents=True,exist_ok=True)
        ref=self._baseline(skill); dataset_result=self._strengthen_dataset(suite_path, incoming_skills or [skill], run); initial_eval=evaluate_skill(self.pools['worker'][0],self.pools['critic'],skill,self.skill_text(skill),load_suite(suite_path),methodologies=self._methodologies()); base_eval=initial_eval
        budget={'total_tokens':int(initial_eval['usage']['total_tokens']),'estimated_cost_usd':float(initial_eval['usage']['estimated_cost_usd'])}; (run/'baseline.json').write_text(json.dumps({'eval':initial_eval,'ref':ref},indent=2,ensure_ascii=False))
        error_review=self._error_review(skill.name,run)
        self._grow_corpus(suite_path,feedback,run)
        if self.config.submission_mode=='feedback_only' and agent_patch: raise EvolutionError('Agent patch forbidden by policy')
        if self.config.submission_mode=='patch_only' and feedback and not agent_patch: raise EvolutionError('Patch required by policy')
        proposals=[]
        if agent_patch: proposals.append(('agent_patch',agent_patch))
        if feedback:
            if self.config.patch_mode=='approval' and not force_approval: (run/'pending-feedback.json').write_text(json.dumps(feedback,indent=2,ensure_ascii=False)); return {'run_id':rid,'status':'awaiting_patch_approval'}
            n=min(alternatives or self.config.alternatives,max(0,self.config.budget.max_candidates-len(proposals))); proposals += [('improved',p) for p in self.proposals(skill,feedback,n)]
        if not proposals: raise EvolutionError('No feedback or patch')
        generations=min(generations or self.config.budget.max_generations,self.config.budget.max_generations); current_base=skill; current_ref=ref; all_generations=[]
        for gen in range(generations):
            candidates=[self._candidate(run,current_base,current_ref,f'g{gen+1}-c{i}',p) for i,(_,p) in enumerate(proposals,1)]
            with ThreadPoolExecutor(max_workers=self.config.budget.max_parallel) as ex:
                futs=[ex.submit(self._eval_candidate,c,load_suite(suite_path),base_eval) for c in candidates]; scored=[f.result() for f in as_completed(futs)]
            for x in scored: budget['total_tokens']+=int(x['eval']['usage']['total_tokens']); budget['estimated_cost_usd']+=float(x['eval']['usage']['estimated_cost_usd'])
            frontier=self._pareto(scored) if self.config.pareto_enabled else [x['candidate']['index'] for x in scored]
            vote=self._vote(base_eval,[x for x in scored if x['candidate']['index'] in frontier],feedback)
            pool=[x for x in scored if x['candidate']['index'] in frontier]; wi=vote['winner']; winner=pool[wi] if wi is not None and wi<len(pool) else None
            battle=red_blue_battle(winner['candidate'],winner['eval'],self.pools['red_team'],self.pools['blue_team'],self.config.battle.red_team_rounds) if winner and self.config.battle.enabled and self.pools['red_team'] and self.pools['blue_team'] else None
            shadow=None
            if winner and self.config.shadow.enabled:
                reqs=load_requests(self.config.shadow.request_store,self.config.shadow.max_requests)
                cases=[]
                for r in reqs:
                    if r.get('case'): cases.append(r['case'])
                    elif r.get('prompt'): cases.append({'id':r['id'],'prompt':r['prompt'],'success_criteria':r.get('success_criteria',[]),'constraints':r.get('constraints',[]),'mandatory':r.get('mandatory',False)})
                if cases:
                    shadow=ShadowEngine(self.pools['worker'][0],self.pools['critic'][0], SubprocessRuntime(self.config.runtime.command,self.config.runtime.timeout_seconds) if self.config.runtime.mode=='subprocess' else ProviderRuntime()).run(current_base,winner['candidate']['dir'],cases,self._methodologies())
                    (run/'shadow.json').write_text(json.dumps(shadow,indent=2,ensure_ascii=False,default=str))
            shadow_ok = True
            if shadow:
                shadow_ok = shadow['candidate_score'] + 1e-9 >= shadow['baseline_score']
                stat=shadow.get('statistics',{})
                if self.config.shadow.significance_required and shadow.get('n',0) >= self.config.shadow.min_requests:
                    shadow_ok = shadow_ok and bool(shadow.get('significant_improvement',False)) and float(stat.get('mean_delta',0)) >= self.config.shadow.min_effect
            compatibility=None
            if winner and self.config.compatibility.enabled:
                siblings=discover_interactions(skill.parent,[skill.name])
                compatibility=evaluate_cross_skill_compat(self.pools['worker'][0],self.pools['critic'][0],winner['candidate']['dir'],siblings,None,self._methodologies())
                (run/'compatibility.json').write_text(json.dumps(compatibility,indent=2,ensure_ascii=False,default=str))
                shadow_ok = shadow_ok and (not self.config.compatibility.require_pass or compatibility['passed'])
            accepted=bool(winner and winner['eval']['mandatory_failures']==0 and len(winner['eval']['regressions'])<=self.config.max_regressions and winner['eval']['score']>=base_eval['score']+self.config.min_score_delta and vote['accepted_by_vote'] and (not battle or battle['passed']) and shadow_ok)
            all_generations.append({'generation':gen+1,'pareto_frontier':frontier,'scored':[{**{k:v for k,v in x.items() if k!='candidate'},'candidate_index':x['candidate']['index'],'candidate_label':x['candidate']['label'],'cost':x['candidate']['cost'],'tokens':x['candidate']['tokens']} for x in scored],'vote':vote,'battle':battle,'shadow':shadow,'compatibility':compatibility,'accepted':accepted,'winner_label':winner['candidate']['label'] if winner else None,'winner_candidate_index':winner['candidate']['index'] if winner else None,'candidates':[{**x['candidate']} for x in scored]})
            if not accepted or gen==generations-1: break
            base_eval=winner['eval']; current_base=Path(winner['candidate']['dir']); current_ref=winner['candidate']['commit']; proposals=[('mutation',_json(self.pools['improver'][gen%len(self.pools['improver'])].generate(IMPROVER_SYSTEM,improver_prompt(self.skill_text(current_base),{'winner':True},1,1,self._methodologies())).text))]
        final=all_generations[-1]
        self.events.emit('evolution_completed',actor='skIF',skill=skill.name,run_id=rid,payload={'accepted':bool(final['accepted']),'candidate':final.get('winner_label')})
        promoted=False; dep=None; pr=None
        if final['accepted'] and promote and (force_approval or self.config.auto_promote or not self.config.require_human_approval_to_promote):
            idx=final.get('winner_candidate_index'); chosen=next((x for x in final.get('candidates',[]) if x.get('index')==idx),None)
            commit=chosen.get('commit') if chosen else None
            if commit and self.config.use_git: cherry_pick(skill,commit); promoted=True
            if promoted and self.config.deployment.enabled and (force_approval or not self.config.deployment.require_approval) and not KillSwitch(self.config.production.kill_switch_path).status().get('enabled'): dep=deploy(self.config.deployment,skill,run,approved=True,canary_cfg=self.config.canary,production_cfg=self.config.production)
        graph = analyze_skill_graph(skill.parent) if skill.parent.exists() else None
        result={'run_id':rid,'baseline_ref':ref,'dependency_graph':graph,'dataset_strengthening':dataset_result,'base_eval':initial_eval,'final_base_eval':base_eval,'budget_used':budget,'generations':all_generations,'accepted':bool(final['accepted']),'winner':final['vote'].get('winner'),'promoted':promoted,'deployment':dep,'baseline_hash':snapshot_hash(skill),'error_review':error_review}
        (run/'result.json').write_text(json.dumps(result,indent=2,ensure_ascii=False,default=str)); write_attestation(run/'provenance.json',{'framework':'skIF','run_id':rid,'result_sha256':hashlib.sha256((run/'result.json').read_bytes()).hexdigest()},self.config.provenance_signing_key_env)
        for wt in (run/'worktrees').glob('*') if (run/'worktrees').exists() else []:
            if self.config.use_git and self.config.create_worktrees: worktree_remove(skill,wt)
        return result

    def run_many(self,items,promote=False):
        out=[]
        with ThreadPoolExecutor(max_workers=self.config.budget.max_parallel) as ex:
            fs=[ex.submit(self.run,Path(x['skill']),Path(x['suite']),feedback=x.get('feedback'),agent_patch=x.get('patch'),promote=promote,incoming_skills=x.get('incoming_skills')) for x in items]
            for f in as_completed(fs): out.append(f.result())
        return out
