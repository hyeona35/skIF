export class SkifClient {
  constructor({baseUrl='http://127.0.0.1:8787', token='' }={}) { this.baseUrl=baseUrl.replace(/\/$/,''); this.token=token; }
  async post(path, body) {
    const headers={'content-type':'application/json'};
    if (this.token) headers.authorization=`Bearer ${this.token}`;
    const res=await fetch(this.baseUrl+path,{method:'POST',headers,body:JSON.stringify(body)});
    const text=await res.text(); let data; try{data=JSON.parse(text)}catch{data={raw:text}}
    if(!res.ok) throw new Error(`${res.status}: ${data.error||text}`); return data;
  }
  telemetry(event_type, payload={}) { return this.post('/api/telemetry',{event_type,...payload}); }
  reportError(payload) { return this.post('/api/errors',payload); }
  vote(payload) { return this.post('/api/community/vote',payload); }
  feedback(payload) { return this.post('/api/feedback',payload); }
  methodology(payload) { return this.post('/api/methodologies',payload); }
  registerAgent(payload) { return this.post('/api/agents/register',payload); }
  reputation(payload) { return this.post('/api/agents/reputation',payload); }
  contributionVote(payload) { return this.post('/api/community/vote',payload); }
  capabilities(payload) { return this.post('/api/agents/capabilities',payload); }
  contribution(payload) { return this.post('/api/contributions',payload); }
  evalProposal(payload) { return this.post('/api/eval/propose',payload); }
  evalCorpora() { return this.get('/api/eval/corpora'); }
  evalLeaderboard() { return this.get('/api/eval/leaderboard'); }
  identity() { return this.get('/api/identity'); }
  killSwitchStatus() { return this.get('/api/kill-switch'); }
  securityFuzz(payload) { return this.post('/api/security/fuzz',payload); }
  securityAdversarial(payload) { return this.post('/api/security/adversarial',payload); }
  eventStoreHealth() { return this.get('/api/eventstore/health'); }
  proposeSkill(payload) { return this.post('/api/skills/propose',payload); }
  reportEvalContribution(payload) { return this.post('/api/eval/validate',payload); }
  knowledgeGraph() { return this.get('/api/knowledge/graph'); }
  marketplaceSearch(query='') { return this.get('/api/marketplace/search?q='+encodeURIComponent(query)); }
  publishSkill(record) { return this.post('/api/marketplace/publish',{record}); }
  certifySkill(skill_id, metrics) { return this.post('/api/marketplace/certify',{skill_id,metrics}); }
  signArtifact(kind, payload, origin='') { return this.post('/api/federation/sign',{kind,payload,origin}); }
  ingestArtifact(artifact) { return this.post('/api/federation/ingest',{artifact}); }
  syncFederation(artifacts) { return this.post('/api/federation/sync',{artifacts}); }
  securityScan(payload) { return this.post('/api/security/scan',{payload}); }
  redTeam(targets, rounds=2) { return this.post('/api/security/red-team',{targets,rounds}); }
  async get(path) { const headers={}; if(this.token) headers.authorization=`Bearer ${this.token}`; const res=await fetch(this.baseUrl+path,{headers}); const text=await res.text(); let data; try{data=JSON.parse(text)}catch{data={raw:text}}; if(!res.ok) throw new Error(`${res.status}: ${data.error||text}`); return data; }
}
