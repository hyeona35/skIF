const http=require('http'); const https=require('https');
class SkifClient{
 constructor(baseURL='http://127.0.0.1:8787',token=''){this.base=baseURL.replace(/\/$/,'');this.token=token;}
 call(path,body=null){return new Promise((resolve,reject)=>{const u=new URL(this.base+path),data=body===null?null:JSON.stringify(body);const opts={method:body===null?'GET':'POST',hostname:u.hostname,port:u.port||undefined,path:u.pathname+u.search,headers:{'Content-Type':'application/json'}};if(this.token)opts.headers.Authorization=`Bearer ${this.token}`;const tr=u.protocol==='https:'?https:http;const req=tr.request(opts,res=>{let s='';res.on('data',c=>s+=c);res.on('end',()=>{let x={};try{x=JSON.parse(s)}catch(_){x={raw:s}};if(res.statusCode>=300)return reject(new Error(`skIF HTTP ${res.statusCode}: ${s}`));resolve(x);});});req.on('error',reject);if(data)req.write(data);req.end();});}
 telemetry(x){return this.call('/api/telemetry',x)} vote(x){return this.call('/api/community/vote',x)}
 researchCreate(x){return this.call('/api/research/create',x)} researchTransition(x){return this.call('/api/research/transition',x)}
 compose(x){return this.call('/api/skills/compose',x)} trustNegotiate(x){return this.call('/api/trust/negotiate',x)} portableVerify(x){return this.call('/api/identity/portable/verify',x)}
 recommend(task,environment={}){return this.call('/api/agent/recommend?task='+encodeURIComponent(task)+'&environment='+encodeURIComponent(JSON.stringify(environment)))}
 teamPlan(x){return this.call('/api/agent/team/plan',x)} errorReport(x){return this.call('/api/errors',x)} methodology(x){return this.call('/api/methodologies',x)}
 knowledgePath(source,target){return this.call('/api/knowledge/mesh/path?source='+encodeURIComponent(source)+'&target='+encodeURIComponent(target))}
 marketplace(q=''){return this.call('/api/marketplace/search?q='+encodeURIComponent(q))}
}
module.exports={SkifClient};
