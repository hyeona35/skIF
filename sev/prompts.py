import json
CRITIC_SYSTEM='You are skIF Critic. Return strict JSON.'
IMPROVER_SYSTEM='You are skIF Improver. Return strict JSON containing a files array of patch operations.'
JUDGE_SYSTEM='You are skIF Judge. Return strict JSON.'
RED_SYSTEM='You are skIF Red Team. Attack the candidate skill and expose failures. Return strict JSON.'
BLUE_SYSTEM='You are skIF Blue Team. Defend/repair the candidate against the Red Team. Return strict JSON.'
REVIEWER_SYSTEM='You are skIF Incident Reviewer. Reassess a burst of agent-reported errors independently. Return strict JSON.'
METHODOLOGY_SYSTEM='You are skIF Methodology Curator. Extract reusable debugging/coding methodology, not project-specific secrets.'

def critic_prompt(skill,task,output,trace=None,methodologies=None): return json.dumps({'skill':skill,'task':task,'output':output,'tool_trace':trace or [],'methodologies':methodologies or []},ensure_ascii=False)
def improver_prompt(skill,feedback,alternative,total,methodologies=None): return json.dumps({'skill':skill,'feedback':feedback,'alternative':alternative,'total':total,'methodologies':methodologies or [],'schema':{'files':[{'path':'relative/path','operation':'replace|append|insert_after|delete','content':'...','anchor':'...'}]}},ensure_ascii=False)
def judge_prompt(base,candidates,feedback,mode='pairwise'): return json.dumps({'baseline':base,'candidates':candidates,'feedback':feedback,'mode':mode,'instruction':'Prefer correctness, safety, mandatory-pass preservation, low regression risk, low cost. For pairwise, compare candidate pairs; for pointwise, score every candidate.'},ensure_ascii=False)
def red_prompt(candidate,base_eval,round_no): return json.dumps({'candidate':candidate,'baseline_eval':base_eval,'round':round_no,'instruction':'Find adversarial failures, ambiguous instructions, tool misuse, security issues, regression risks.'},ensure_ascii=False)
def blue_prompt(candidate,base_eval,attack,round_no): return json.dumps({'candidate':candidate,'baseline_eval':base_eval,'red_attack':attack,'round':round_no,'instruction':'Defend the candidate, propose mitigations, and score how well it withstands the attack.'},ensure_ascii=False)
def error_review_prompt(errors): return json.dumps({'errors':errors,'instruction':'Determine whether the burst indicates a systemic skill regression or noisy reports. Recommend the next review action.'},ensure_ascii=False)
def methodology_prompt(item): return json.dumps({'observation':item,'instruction':'Extract a reusable, provider-neutral debugging/coding technique. Never include secrets or project-specific credentials.'},ensure_ascii=False)
