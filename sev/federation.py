from __future__ import annotations
import hashlib,hmac,json,time,uuid
from pathlib import Path

KIND_LIMITS={'skill':2_000_000,'eval':1_000_000,'methodology':250_000,'telemetry':500_000,'benchmark':2_000_000,'provenance':1_000_000}

class SignedArtifact:
    def __init__(self, secret='', require_secret=True):
        self.secret=secret.encode() if secret else b''; self.require_secret=require_secret
    def sign(self,kind,payload,origin):
        if self.require_secret and not self.secret: raise RuntimeError('signing-key-required')
        body={'artifact_id':str(uuid.uuid4()),'kind':kind,'origin':origin,'created_at':time.time(),'payload':payload}
        raw=json.dumps(body,sort_keys=True,separators=(',',':')).encode(); body['signature']=hmac.new(self.secret,raw,hashlib.sha256).hexdigest();return body
    def verify(self,artifact,trusted_origins=None):
        kind=str(artifact.get('kind','')); payload=artifact.get('payload')
        if kind not in KIND_LIMITS:return {'valid':False,'reason':'unknown-kind'}
        if trusted_origins is not None and trusted_origins and artifact.get('origin') not in trusted_origins:return {'valid':False,'reason':'untrusted-origin'}
        if self.require_secret and not self.secret:return {'valid':False,'reason':'signing-key-not-configured'}
        try:raw=json.dumps({k:artifact[k] for k in ('artifact_id','kind','origin','created_at','payload')},sort_keys=True,separators=(',',':')).encode()
        except Exception:return {'valid':False,'reason':'malformed-artifact'}
        expected=hmac.new(self.secret,raw,hashlib.sha256).hexdigest()
        if not hmac.compare_digest(expected,str(artifact.get('signature',''))):return {'valid':False,'reason':'bad-signature'}
        size=len(json.dumps(payload,ensure_ascii=False).encode())
        if size>KIND_LIMITS[kind]:return {'valid':False,'reason':'oversize'}
        return {'valid':True,'kind':kind,'origin':artifact.get('origin'),'size':size}

class FederationStore:
    def __init__(self,root='data/federation',signer=None,trusted_origins=None,quarantine=True):
        self.root=Path(root);self.root.mkdir(parents=True,exist_ok=True);self.path=self.root/'artifacts.jsonl';self.quarantine_path=self.root/'quarantine.jsonl';self.nodes_path=self.root/'nodes.json';self.signer=signer or SignedArtifact('',True);self.trusted_origins=set(trusted_origins or []);self.quarantine_enabled=quarantine
    def ingest(self,artifact,*,auto_release=False):
        check=self.signer.verify(artifact,self.trusted_origins)
        if not check['valid']:
            self._quarantine(artifact,check['reason']);raise ValueError(check['reason'])
        status='trusted' if auto_release else 'quarantine'
        row=dict(artifact);row['status']=status;self._append(self.quarantine_path if status=='quarantine' else self.path,row)
        return check|{'status':status,'artifact_id':artifact.get('artifact_id')}
    def _append(self,path,row):
        with path.open('a',encoding='utf-8') as f:f.write(json.dumps(row,ensure_ascii=False)+'\n')
    def _quarantine(self,artifact,reason):self._append(self.quarantine_path,{'artifact':artifact,'reason':reason,'quarantined_at':time.time()})
    def release(self,artifact_id,reviewer):
        rows=[]
        for line in self.quarantine_path.read_text().splitlines() if self.quarantine_path.exists() else []:
            x=json.loads(line); a=x.get('artifact',x)
            if a.get('artifact_id')==artifact_id: a['status']='trusted';a['released_by']=reviewer;a['released_at']=time.time();self._append(self.path,a);continue
            rows.append(x)
        self.quarantine_path.write_text(''.join(json.dumps(x,ensure_ascii=False)+'\n' for x in rows));return {'released':artifact_id,'reviewer':reviewer}
    def quarantine(self):
        if not self.quarantine_path.exists():return []
        return [json.loads(x) for x in self.quarantine_path.read_text().splitlines() if x.strip()]
    def list(self,kind='',trusted_only=True):
        if not self.path.exists():return []
        out=[]
        for line in self.path.read_text().splitlines():
            if not line:continue
            x=json.loads(line)
            if (not kind or x.get('kind')==kind) and (not trusted_only or x.get('status','trusted')=='trusted'):out.append(x)
        return out[-1000:]
    def sync(self,artifacts):
        accepted=[];rejected=[]
        for a in artifacts:
            try:accepted.append(self.ingest(a))
            except Exception as exc:rejected.append({'reason':str(exc),'artifact':a.get('kind','unknown')})
        return {'accepted':len(accepted),'rejected':len(rejected),'rejections':rejected,'quarantined':len([x for x in accepted if x.get('status')=='quarantine'])}
    def register_node(self,node_id,origin,capabilities=None,public_key=''):
        nodes=json.loads(self.nodes_path.read_text()) if self.nodes_path.exists() else {}; row={'node_id':str(node_id),'origin':origin,'capabilities':capabilities or [],'public_key':public_key,'last_seen':time.time(),'trust':'pending' if origin not in self.trusted_origins else 'trusted'};nodes[str(node_id)]=row;self.nodes_path.write_text(json.dumps(nodes,ensure_ascii=False,indent=2));return row
    def heartbeat(self,node_id):
        nodes=json.loads(self.nodes_path.read_text()) if self.nodes_path.exists() else {}
        if str(node_id) not in nodes:raise KeyError(node_id)
        nodes[str(node_id)]['last_seen']=time.time();self.nodes_path.write_text(json.dumps(nodes,ensure_ascii=False,indent=2));return nodes[str(node_id)]
    def nodes(self):return list((json.loads(self.nodes_path.read_text()) if self.nodes_path.exists() else {}).values())
