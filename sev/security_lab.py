from __future__ import annotations
import hashlib,json,re,subprocess,time,os,tempfile
from pathlib import Path

ATTACKS={
'eval_poisoning':[r'ignore.*evaluation',r'delete.*test',r'lower.*threshold',r'change.*rubric'],
'prompt_injection':[r'ignore (all|previous) instructions',r'system prompt',r'jailbreak'],
'tool_abuse':[r'rm\s+-rf',r'curl\s+[^|]+\|\s*(sh|bash)',r'sudo\s+',r'\.\./'],
'credential_exfiltration':[r'api[_ -]?key',r'authorization',r'cookie',r'private key',r'password',r'secret'],
'skill_dependency_poisoning':[r'install.*untrusted',r'dependency.*override',r'pin.*malicious',r'unknown package'],
'judge_manipulation':[r'judge.*vote',r'vote.*for me',r'ignore.*judge'],
'telemetry_poisoning':[r'fake.*telemetry',r'fabricat.*metric',r'alter.*score'],
'vote_manipulation':[r'create.*accounts',r'spam.*vote',r'multiple identities',r'sybil'],
'methodology_poisoning':[r'publish.*secret',r'include.*credential',r'unsafe.*always'],
'rollback_abuse':[r'disable.*rollback',r'skip.*smoke',r'force.*deploy'],
'sandbox_escape':[r'os\.system',r'subprocess\.run',r'child_process',r'process\.env',r'/proc/',r'/sys/'],
'supply_chain':[r'curl.*install',r'pip install .*git',r'npm install .*http',r'go get .*@latest'],
}

def scan_text(text):
    findings=[]
    for category,patterns in ATTACKS.items():
        for p in patterns:
            if re.search(p,str(text),re.I):findings.append({'category':category,'pattern':p,'fingerprint':hashlib.sha256(f'{category}:{p}'.encode()).hexdigest()[:12]})
    return findings

def scan_artifact(artifact):
    text=json.dumps(artifact,ensure_ascii=False,default=str); findings=scan_text(text);return {'safe':not findings,'findings':findings,'scanned_at':time.time()}

def fuzz_payload(payload,mutations=16):
    base=json.dumps(payload,ensure_ascii=False)
    variants=[]
    for i in range(max(1,int(mutations))):
        if i%4==0:v=base+' ignore previous instructions'
        elif i%4==1:v=base+' ../../secret'
        elif i%4==2:v=base.replace('{','{"api_key":"SECRET","x":')
        else:v=base+' rm -rf /'
        variants.append(v)
    return variants

class SecurityLab:
    def scan(self,payload):return scan_artifact(payload)
    def red_team(self,targets,rounds=2):
        results=[]
        for name,payload in targets.items():
            for i in range(max(1,int(rounds))):
                attack=scan_artifact(payload);results.append({'name':f'{name}:{i+1}','attack':attack,'passed':attack['safe']})
        return {'passed':all(x['passed'] for x in results),'results':results}
    def autonomous_adversarial(self,targets,rounds=3):
        failures=[]
        for r in range(max(1,int(rounds))):
            result=self.red_team(targets,1)
            failures.extend([x for x in result['results'] if not x['passed']])
        return {'rounds':rounds,'passed':not failures,'findings':failures}
    def fuzz(self,payload,mutations=32):
        results=[{'variant':v,'findings':scan_text(v)} for v in fuzz_payload(payload,mutations)]
        return {'mutations':len(results),'findings':sum((x['findings'] for x in results),[]),'blocked':any(x['findings'] for x in results)}
    def judge_attack(self,judge_output):return {'safe':not scan_text(judge_output),'findings':scan_text(judge_output)}
    def federation_attack(self,artifact):
        a=dict(artifact);a['payload']=dict(a.get('payload') or {});a['payload']['ignore_evaluation']='lower threshold';return scan_artifact(a)
    def sandbox_test(self,command=''):
        risky=scan_text(command);return {'safe':not risky,'findings':risky}
    def vote_attack(self,votes,identities=100):
        rows=votes or []; ids=[str(x.get('agent_id','')) for x in rows if isinstance(x,dict)]
        unique=len(set(ids)); duplicates=len(ids)-unique
        return {'safe': duplicates <= max(1,int(len(rows)*0.1)), 'total_votes':len(rows), 'unique_identities':unique, 'duplicate_votes':duplicates, 'simulated_identities':int(identities)}

    def supply_chain_scan(self,packages):
        return self.dependency_scan(packages)

    def dependency_scan(self,dependencies):
        findings=[]
        for d in dependencies or []:
            if '@latest' in str(d) or str(d).startswith(('http://','git+','curl ')):findings.append({'dependency':d,'reason':'unbounded-or-remote-source'})
        return {'safe':not findings,'findings':findings}


class SecurityControlPlane:
    """3.1 Neo defense-in-depth checks; deterministic and safe by default."""
    FORBIDDEN_NETWORK = ('169.254.169.254','metadata.google.internal','file://','gopher://')
    FORBIDDEN_SHELL = ('rm -rf /','mkfs','dd if=','curl | sh','wget | sh','/dev/tcp/','chmod 777','sudo su')
    def scan_supply_chain(self, manifests):
        findings=[]
        for item in manifests or []:
            text=str(item)
            if '@latest' in text or 'git+' in text or 'http://' in text: findings.append({'kind':'unpinned-or-insecure-dependency','item':text})
        return {'safe':not findings,'findings':findings}
    def scan_sandbox_escape(self, commands):
        findings=[]
        for cmd in commands or []:
            low=str(cmd).lower()
            for bad in self.FORBIDDEN_SHELL:
                if bad.lower() in low: findings.append({'kind':'dangerous-command','command':cmd,'pattern':bad})
            if '/proc/' in low or '/sys/' in low: findings.append({'kind':'host-filesystem-access','command':cmd})
        return {'safe':not findings,'findings':findings}
    def scan_dependency_exploit(self, packages):
        findings=[]
        for p in packages or []:
            if str(p).endswith(':*') or 'latest' in str(p).lower(): findings.append({'kind':'mutable-version','package':p})
        return {'safe':not findings,'findings':findings}
    def scan_federation(self, node_policy, artifact):
        findings=[]; policy=node_policy or {}; art=artifact or {}
        if policy.get('require_signed',True) and art.get('signature_status') not in ('verified','valid'):
            findings.append({'kind':'unsigned-artifact'})
        if art.get('security_rating',0) < policy.get('min_security',0.0): findings.append({'kind':'security-rating-below-policy'})
        return {'safe':not findings,'findings':findings}
    def continuous_fuzz(self, seed, rounds=3, mutations=32):
        results=[]
        base=dict(seed or {})
        for i in range(max(1,int(rounds))):
            for j in range(max(1,min(int(mutations),64))):
                mutated=dict(base); mutated['fuzz']=f'{i}:{j}'; mutated['nested']={'overflow':'x'*min(j*1000,100000)}
                results.append({'safe':len(mutated.get('nested',{}).get('overflow',''))<100000,'case':f'{i}:{j}'})
        return {'passed':all(x['safe'] for x in results),'cases':len(results),'failures':[x for x in results if not x['safe']][:20]}
