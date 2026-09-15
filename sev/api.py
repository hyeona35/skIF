from __future__ import annotations
import json, os, time
from http.server import BaseHTTPRequestHandler,ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs
from .config import load_config,save_config,ProviderConfig,RoleConfig,ROLES
from .errors import report_error
from .registry import list_methodologies,list_skill_proposals,propose_skill
from .graph import analyze as analyze_skill_graph
from .dataset import strengthen_suite
from .shadow import append_request,load_requests,ShadowEngine
from .eventstore import EventStore
from .review import ReviewQueue
from .release import generate_contribution_message,manifest as write_contribution_manifest
from .production import KillSwitch,DeploymentLock,CircuitBreaker,scrub
from .traffic import TrafficMirror
from .task_queue import TaskQueue,get_queue
from .evaluation import corpus_profile,generate_mutations,validate_and_propose,counterfactual_report
from .telemetry import normalize_event
from .reputation import ReputationEngine
from .governance import VoteGovernor
from .knowledge import KnowledgeGraph
from .resilience import AgentGuard
from .marketplace import Marketplace
from .federation import FederationStore, SignedArtifact
from .federation_network import FederationNetwork
from .federation_marketplace import FederationMarketplace
from .trust_negotiation import TrustPolicy, negotiate as negotiate_trust
from .portable_identity import PortableIdentityAuthority
from .privacy import TelemetryProtector, local_aggregate, differential_private_counts
from .research_os import ResearchOS
from .composition import compose as compose_skills, fork as fork_skill, merge as merge_skills
from .security_lab import SecurityLab
from .auth import Authenticator
from .identity import IdentityStore
from .eval_corpus import EvalCorpus
from .benchmark import BenchmarkStore
from .idempotency import Idempotency
from .cache import TTLCache
from .kill_switch import KillSwitchRegistry
from .mesh import KnowledgeMesh
from .agents_os import AgentOS
from .resources import ResourceGovernor,ResourcePolicy
from .governance_os import DecisionLedger
from .plugin import PluginRegistry
from .privacy_mesh import SecureTelemetry,PrivacyBudget
from .skill_lineage import lineage
from .security_lab import SecurityControlPlane
from .neo_ui import page as neo_page
from .prediction import PredictionMarket
from .benchmark_network import GlobalBenchmarkNetwork
import hashlib

def _neo_services(c,store,marketplace,rep,cache):
    mesh=KnowledgeMesh(str(getattr(c.knowledge,'path','data/knowledge.db'))+'-mesh')
    gov=DecisionLedger(store)
    resources=ResourceGovernor(ResourcePolicy(**(c.resource_governance or {})))
    plugins=PluginRegistry()
    security=SecurityControlPlane()
    secure_telemetry=SecureTelemetry(budget=PrivacyBudget(3.0))
    agent_os=AgentOS(rep,marketplace,mesh,resources)
    return mesh,gov,resources,plugins,security,secure_telemetry,agent_os

HTML=r'''<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>skIF 3.1 Neo Agent Skill Operating System</title>
<style>
:root{font-family:Inter,ui-sans-serif,system-ui,sans-serif;color:#172033;background:#f4f7fb}*{box-sizing:border-box}body{margin:0}.app{max-width:1440px;margin:auto;padding:20px}.top{position:sticky;top:0;z-index:5;background:#f4f7fbcc;backdrop-filter:blur(12px);display:flex;justify-content:space-between;align-items:center;gap:16px;padding:10px 0 14px}.brand{font-size:26px;font-weight:900;letter-spacing:-.04em}.muted{color:#68748a}.tabs{display:flex;gap:6px;flex-wrap:wrap;margin:6px 0 18px}.tab{border:1px solid #d8deea;background:#fff;padding:10px 13px;border-radius:11px;cursor:pointer}.tab.active{background:#172033;color:#fff}.panel{display:none}.panel.active{display:block}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(250px,1fr));gap:12px}.card{background:#fff;border:1px solid #dfe5ef;border-radius:18px;padding:18px;box-shadow:0 10px 30px #1720330a}.field{margin:9px 0}label{display:block;font-size:13px;font-weight:750;margin-bottom:5px}input,select,textarea{width:100%;border:1px solid #cfd7e5;border-radius:10px;padding:9px 11px;background:#fff}.check{display:flex;align-items:center;gap:8px;margin:7px 0}.check input{width:auto}.btn{border:0;border-radius:10px;padding:9px 13px;cursor:pointer}.primary{background:#172033;color:#fff}.secondary{background:#e9edf5}.danger{background:#fee5e5}.pill{display:inline-block;padding:4px 9px;border-radius:999px;background:#eef2f8;font-size:12px}.ok{background:#e4f7eb}.warn{background:#fff5cf}.bad{background:#ffe3e3}.row{display:flex;justify-content:space-between;align-items:center;gap:8px}.actions{display:flex;gap:7px;flex-wrap:wrap}.metric{font-size:30px;font-weight:900}.list{display:grid;gap:9px}.item{border:1px solid #e7ebf2;border-radius:12px;padding:11px}.sub{font-size:12px}.mono{font-family:ui-monospace,SFMono-Regular,monospace;font-size:12px;white-space:pre-wrap}.fold{border:1px solid #dfe5ef;border-radius:12px;padding:10px;margin-top:10px;background:#fbfcfe}.danger-text{color:#9b2c2c}@media(max-width:800px){.top{align-items:flex-start;flex-direction:column}}
</style></head><body><div class="app"><div class="top"><div><div class="brand">skIF</div><div class="muted">Skill Improvement by selF · 3.1 Neo · Agent Skill Operating System</div></div><div class="actions"><input id="token" style="width:240px" placeholder="SKIF API token"><button class="btn secondary" onclick="setToken()">Set token</button><span id="health" class="pill">checking…</span></div></div>
<div class="tabs"> <button class="tab active" data-tab="home">Overview</button><button class="tab" data-tab="onboard">Onboarding</button><button class="tab" data-tab="skills">Skills</button><button class="tab" data-tab="evolution">Evolution</button><button class="tab" data-tab="shadow">Shadow / Canary</button><button class="tab" data-tab="production">Production</button><button class="tab" data-tab="eval">Eval Intelligence</button><button class="tab" data-tab="queue">Human Review</button><button class="tab" data-tab="ecosystem">Ecosystem</button><button class="tab" data-tab="reputation">Reputation</button><button class="tab" data-tab="knowledge">Knowledge Graph</button><button class="tab" data-tab="marketplace">Marketplace</button><button class="tab" data-tab="federation">Federation</button><button class="tab" data-tab="security">Security Lab</button><button class="tab" data-tab="audit">Audit</button></div>
<section id="home" class="panel active"><div class="grid"><div class="card"><div class="muted">Runs</div><div id="m_runs" class="metric">-</div></div><div class="card"><div class="muted">Promotions</div><div id="m_promoted" class="metric">-</div></div><div class="card"><div class="muted">Pending reviews</div><div id="m_reviews" class="metric">-</div></div><div class="card"><div class="muted">Telemetry agents</div><div id="m_agents" class="metric">-</div></div></div><div class="card"><div class="row"><h2>Recent runs</h2><button class="btn secondary" onclick="refresh()">Refresh</button></div><div id="runs" class="list">Loading…</div></div></section>
<section id="onboard" class="panel"><div class="card"><h2>1 · Providers</h2><div class="muted">Credentials stay in environment variables. Custom APIs support OpenAI-compatible, Anthropic-compatible, or native formats.</div><div id="providers" class="grid"></div><button class="btn secondary" onclick="addProvider()">+ Provider</button></div><div class="card"><h2>2 · Roles</h2><div id="roles" class="grid"></div></div><div class="card"><h2>3 · Governance</h2><div class="grid"><div class="field"><label>VOTE</label><select id="voting_enabled"><option value="true">ON</option><option value="false">OFF</option></select></div><div class="field"><label>Vote mode</label><select id="vote_mode"><option>pairwise</option><option>pointwise</option></select></div><div class="field"><label>Vote threshold</label><input id="vote_threshold" type="number" min="0" max="1" step=".05"></div><div class="field"><label>Min Judge calibration</label><input id="judge_min_calibration" type="number" min="0" max="1" step=".05"></div><div class="field"><label>Autonomous research loops</label><input id="autonomous_loops" type="number" min="0" max="50"></div></div><div class="check"><input id="human" type="checkbox"><span>Require human approval before promotion</span></div><div class="check"><input id="pareto" type="checkbox"><span>Pareto frontier</span></div><div class="check"><input id="battle" type="checkbox"><span>Red/Blue battle</span></div></div><div class="card"><h2>4 · Reliability</h2><div class="grid"><div class="field"><label>Shadow significance</label><select id="shadow_significance"><option value="true">Required</option><option value="false">Not required</option></select></div><div class="field"><label>Shadow minimum mirrored requests</label><input id="shadow_min" type="number"></div><div class="field"><label>Canary stages (percent)</label><input id="canary_stages" placeholder="1,5,25,50,100"></div><div class="field"><label>Cross-skill compatibility</label><select id="compatibility"><option value="true">Required</option><option value="false">Optional</option></select></div></div></div><div class="card"><h2>5 · Save & validate</h2><div class="actions"><button class="btn primary" onclick="saveConfig()">Save onboarding</button><button class="btn secondary" onclick="generateContribution()">Generate Skill contribution message</button></div><pre id="saveout" class="mono"></pre><div id="contribution"></div></div></section>
<section id="skills" class="panel"><div class="grid"><div class="card"><h2>Skill proposal</h2><div class="field"><label>Name</label><input id="prop_name"></div><div class="field"><label>Description</label><textarea id="prop_desc"></textarea></div><button class="btn primary" onclick="proposeSkill()">Submit proposal</button></div><div class="card"><h2>Dependency graph</h2><div class="field"><label>Workspace root</label><input id="graph_root" placeholder="/path/to/skills"></div><button class="btn secondary" onclick="loadGraph()">Analyze DAG</button><pre id="graph" class="mono"></pre></div></div><div class="card"><h2>Registry</h2><div id="registry" class="list">Loading…</div></div></section>
<section id="evolution" class="panel"><div class="card"><h2>Evolution jobs</h2><div class="muted">Use this panel to send one or many Skill jobs. The protected evaluation corpus, Judge calibration, cross-Skill checks, Shadow significance, and deployment gates remain active according to policy.</div><div class="field"><label>Skill path</label><input id="ev_skill"></div><div class="field"><label>Evaluation suite</label><input id="ev_suite"></div><div class="field"><label>Feedback JSON</label><textarea id="ev_feedback" placeholder='{"message":"…"}'></textarea></div><button class="btn primary" onclick="runEvolution()">Start evolution</button><pre id="evout" class="mono"></pre></div></section>
<section id="shadow" class="panel"><div class="grid"><div class="card"><h2>Record production request</h2><textarea id="shadow_request" placeholder='{"prompt":"…","success_criteria":[]}'></textarea><button class="btn primary" onclick="recordShadow()">Mirror later</button></div><div class="card"><h2>Shadow run</h2><div class="field"><label>Baseline Skill</label><input id="shadow_base"></div><div class="field"><label>Candidate Skill</label><input id="shadow_candidate"></div><button class="btn primary" onclick="runShadow()">Run statistical mirror</button><pre id="shadowout" class="mono"></pre></div></div></section>
<section id="production" class="panel"><div class="grid"><div class="card"><h2>Production Safety</h2><div id="prod_status" class="mono">Loading…</div><div class="actions"><button class="btn danger" onclick="killSwitch(true)">Enable kill switch</button><button class="btn secondary" onclick="killSwitch(false)">Resume traffic</button><button class="btn secondary" onclick="loadProduction()">Refresh</button></div></div><div class="card"><h2>Traffic mirror</h2><div class="field"><label>Skill</label><input id="tm_skill"></div><div class="field"><label>Candidate traffic %</label><input id="tm_pct" type="number" value="1" min="0" max="100"></div><textarea id="tm_payload">{"prompt":"…"}</textarea><button class="btn primary" onclick="mirrorTraffic()">Mirror request</button><pre id="tm_out" class="mono"></pre></div></div><div class="card"><h2>Async Jobs</h2><div id="jobs" class="list">Loading…</div></div></section>
<section id="eval" class="panel"><div class="grid"><div class="card"><h2>Corpus profile</h2><input id="eval_suite" placeholder="/path/to/evals.json"><button class="btn secondary" onclick="profileEval()">Profile</button><pre id="eval_profile" class="mono"></pre></div><div class="card"><h2>Mutation lab</h2><div class="muted">Generate ambiguous, failure, permission, concurrency, and adversarial variants. Results stay proposed until reviewed.</div><button class="btn primary" onclick="mutateEval()">Generate mutations</button><pre id="eval_mutation" class="mono"></pre></div></div></section>
<section id="queue" class="panel"><div class="card"><div class="row"><h2>Human Review Queue</h2><button class="btn secondary" onclick="loadQueue()">Refresh</button></div><div id="queue_list" class="list">Loading…</div></div></section>
<section id="ecosystem" class="panel"><div class="grid"><div class="card"><h2>Telemetry</h2><div class="field"><label>Skill</label><input id="tele_skill"></div><div class="field"><label>Agent ID</label><input id="tele_agent"></div><div class="field"><label>Event type</label><input id="tele_type" placeholder="usage / feedback / vote / commit / methodology"></div><div class="field"><label>Payload JSON</label><textarea id="tele_payload">{}</textarea></div><button class="btn primary" onclick="sendTelemetry()">Record telemetry</button></div><div class="card"><h2>Methodology</h2><textarea id="methodology" placeholder="Reusable technique or debugging lesson (no secrets)."></textarea><button class="btn primary" onclick="submitMethodology()">Share methodology</button></div></div><div class="card"><h2>Participation model</h2><p>Agents using a Skill can report telemetry, vote, submit feedback or patches, and share reusable methodology. The maintainer side evaluates those contributions against protected evaluation, compatibility, Red/Blue battle, Shadow, and Canary gates.</p></div></section>
<section id="reputation" class="panel"><div class="grid"><div class="card"><h2>Agent reputation</h2><div class="field"><label>Agent ID</label><input id="rep_agent" placeholder="agent-name"></div><div class="actions"><button class="btn primary" onclick="loadReputation()">Inspect</button><button class="btn secondary" onclick="registerAgent()">Register</button></div><pre id="rep_out" class="mono"></pre></div><div class="card"><h2>Contribution policy</h2><div class="muted">Influence is bounded by history, diversity, freshness and duplicate suppression. Reputation is an anti-abuse heuristic, not proof of human identity.</div><div class="field"><label>Installation ID</label><input id="rep_install" placeholder="stable local installation identifier"></div></div></div></section>
<section id="knowledge" class="panel"><div class="grid"><div class="card"><h2>Knowledge Graph</h2><div class="actions"><button class="btn secondary" onclick="loadKnowledge()">Refresh graph</button></div><pre id="kg_out" class="mono">Loading…</pre></div><div class="card"><h2>Explain path</h2><div class="field"><label>Source node</label><input id="kg_src" placeholder="error:123"></div><div class="field"><label>Target node</label><input id="kg_tgt" placeholder="methodology:456"></div><button class="btn primary" onclick="explainKnowledge()">Find path</button><pre id="kg_path" class="mono"></pre></div></div></section>
<section id="marketplace" class="panel"><div class="grid"><div class="card"><h2>Skill Marketplace</h2><div class="field"><label>Search</label><input id="mp_q" placeholder="network / kubernetes / database"></div><button class="btn primary" onclick="searchMarketplace()">Search</button><div id="mp_list" class="list" style="margin-top:10px"></div></div><div class="card"><h2>Publish / Certify</h2><textarea id="mp_record">{"name":"My Skill","owner":"agent","maintainer":"agent","version":"1.0.0","description":"","dependencies":[],"compatibility":{},"score":0.8,"cost":0,"latency_ms":0,"security_rating":0.9,"reliability":0.9,"methodologies":[],"telemetry_health":0.8}</textarea><div class="actions"><button class="btn primary" onclick="publishMarketplace()">Publish</button><button class="btn secondary" onclick="certifyMarketplace()">Certify Selected</button></div><pre id="mp_out" class="mono"></pre></div></div></section>
<section id="federation" class="panel"><div class="grid"><div class="card"><h2>Trusted Federation</h2><div class="field"><label>Node ID</label><input id="fed_node" placeholder="node-a"></div><div class="field"><label>Origin</label><input id="fed_origin" placeholder="my-org"></div><button class="btn primary" onclick="registerNode()">Register node</button><button class="btn secondary" onclick="loadNodes()">Load nodes</button><pre id="fed_nodes" class="mono"></pre></div><div class="card"><h2>Signed artifact</h2><div class="field"><label>Kind</label><select id="fed_kind"><option>skill</option><option>eval</option><option>methodology</option><option>telemetry</option><option>benchmark</option></select></div><textarea id="fed_payload">{"message":"hello from an Agent"}</textarea><button class="btn primary" onclick="signArtifact()">Sign</button><button class="btn secondary" onclick="loadArtifacts()">Artifacts</button><pre id="fed_out" class="mono"></pre></div></div></section>
<section id="security" class="panel"><div class="grid"><div class="card"><h2>Security Lab</h2><div class="muted">Scan external Skill/eval/methodology payloads before they enter a trusted registry.</div><textarea id="sec_payload">{"text":"safe contribution"}</textarea><button class="btn primary" onclick="scanSecurity()">Scan</button><pre id="sec_out" class="mono"></pre></div><div class="card"><h2>Red Team</h2><div class="field"><label>Targets JSON</label><textarea id="sec_targets">{"skill":{"text":"safe"},"eval":{"text":"normal test"}}</textarea></div><div class="field"><label>Rounds</label><input id="sec_rounds" type="number" value="2" min="1" max="20"></div><button class="btn danger" onclick="redTeamSecurity()">Run red team</button><pre id="red_out" class="mono"></pre></div></div></section>
<section id="audit" class="panel"><div class="card"><div class="row"><h2>Persistent event store</h2><button class="btn secondary" onclick="loadAudit()">Refresh</button></div><pre id="auditlog" class="mono">Loading…</pre></div></section>
</div><script>
let cfg=null,apiToken=localStorage.getItem('skif_api_token')||'';const $=id=>document.getElementById(id);const f=window.fetch.bind(window);window.fetch=(u,o={})=>{o.headers={...(o.headers||{}),...(apiToken?{'Authorization':'Bearer '+apiToken}:{})};return f(u,o)};function setToken(){apiToken=$('token').value.trim();localStorage.setItem('skif_api_token',apiToken);refresh()}function esc(x){return String(x??'').replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;')}
document.querySelectorAll('.tab').forEach(b=>b.onclick=()=>{document.querySelectorAll('.tab').forEach(x=>x.classList.remove('active'));document.querySelectorAll('.panel').forEach(x=>x.classList.remove('active'));b.classList.add('active');$(b.dataset.tab).classList.add('active');refresh()});
function render(){const ps=Object.values(cfg.providers||{});$('providers').innerHTML=ps.map((p,i)=>`<div class="card"><b>Provider ${i+1}</b><div class="field"><label>Name</label><input data-p="name" data-i="${i}" value="${esc(p.name)}"></div><div class="field"><label>Kind</label><select data-p="kind" data-i="${i}"><option ${p.kind==='openai'?'selected':''}>openai</option><option ${p.kind==='claude'?'selected':''}>claude</option><option ${p.kind==='custom'?'selected':''}>custom</option></select></div><div class="field"><label>Model</label><input data-p="model" data-i="${i}" value="${esc(p.model)}"></div><div class="field"><label>API key env</label><input data-p="api_key_env" data-i="${i}" value="${esc(p.api_key_env)}"></div><div class="field"><label>Endpoint</label><input data-p="endpoint" data-i="${i}" value="${esc(p.endpoint)}"></div><div class="field"><label>Compatibility</label><select data-p="api_compat" data-i="${i}"><option ${p.api_compat==='native'?'selected':''}>native</option><option ${p.api_compat==='openai'?'selected':''}>openai</option><option ${p.api_compat==='anthropic'?'selected':''}>anthropic</option></select></div></div>`).join('');
$('roles').innerHTML=['worker','critic','improver','judge','red_team','blue_team','reviewer'].map(r=>{const x=cfg.roles?.[r]||{};return `<div class="card"><h3>${r}</h3><div class="field"><label>Providers</label><input id="r_${r}" value="${esc((x.providers||[]).join(','))}"></div><label class="check"><input id="en_${r}" type="checkbox" ${x.enabled?'checked':''}> enabled</label><label class="check"><input id="vo_${r}" type="checkbox" ${x.voting?'checked':''}> voting role</label></div>`}).join('');
$('voting_enabled').value=String(cfg.voting_enabled);$('vote_mode').value=cfg.vote_mode;$('vote_threshold').value=cfg.vote_threshold;$('judge_min_calibration').value=cfg.judge_min_calibration;$('autonomous_loops').value=cfg.autonomous_loops;$('human').checked=cfg.require_human_approval_to_promote;$('pareto').checked=cfg.pareto_enabled;$('battle').checked=cfg.battle?.enabled!==false;$('shadow_significance').value=String(cfg.shadow?.significance_required!==false);$('shadow_min').value=cfg.shadow?.min_requests??30;$('canary_stages').value=(cfg.canary?.stages||[1,5,25,50,100]).join(',');$('compatibility').value=String(cfg.compatibility?.require_pass!==false);}
function addProvider(){const name=`provider-${Object.keys(cfg.providers||{}).length+1}`;cfg.providers[name]={name,kind:'openai',model:'',api_key_env:'',endpoint:'',api_compat:'native'};render()}
function buildCfg(){const providers={};document.querySelectorAll('[data-p="name"]').forEach((el,i)=>{const g=p=>document.querySelector(`[data-p="${p}"][data-i="${i}"]`);const x={};['name','kind','model','api_key_env','endpoint','api_compat'].forEach(k=>x[k]=g(k)?.value||'');providers[x.name||`provider-${i}`]=x});cfg.providers=providers;cfg.roles=cfg.roles||{};for(const r of ['worker','critic','improver','judge','red_team','blue_team','reviewer'])cfg.roles[r]={...(cfg.roles[r]||{}),providers:($(`r_${r}`)?.value||'').split(',').map(x=>x.trim()).filter(Boolean),enabled:$(`en_${r}`).checked,voting:$(`vo_${r}`).checked};cfg.voting_enabled=$('voting_enabled').value==='true';cfg.vote_mode=$('vote_mode').value;cfg.vote_threshold=Number($('vote_threshold').value);cfg.judge_min_calibration=Number($('judge_min_calibration').value);cfg.autonomous_loops=Number($('autonomous_loops').value);cfg.require_human_approval_to_promote=$('human').checked;cfg.pareto_enabled=$('pareto').checked;cfg.battle.enabled=$('battle').checked;cfg.shadow.significance_required=$('shadow_significance').value==='true';cfg.shadow.min_requests=Number($('shadow_min').value);cfg.canary.stages=$('canary_stages').value.split(',').map(x=>Number(x.trim())).filter(Boolean);cfg.compatibility.require_pass=$('compatibility').value==='true';return cfg}
async function loadCfg(){const r=await (await fetch('/api/config')).json();cfg=r.config;render()}async function saveConfig(){buildCfg();const r=await fetch('/api/onboarding',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(cfg)});$('saveout').textContent=JSON.stringify(await r.json(),null,2)}async function generateContribution(){const skill=prompt('Absolute/local Skill path');if(!skill)return;const r=await fetch('/api/skills/contribution-message',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({skill})});$('contribution').innerHTML='<div class="fold mono">'+esc(JSON.stringify(await r.json(),null,2))+'</div>'}
async function refresh(){try{const h=await (await fetch('/api/health')).json();$('health').textContent='online';const rr=await (await fetch('/api/runs')).json();$('m_runs').textContent=rr.runs.length;$('m_promoted').textContent=rr.runs.filter(x=>x.promoted).length;$('runs').innerHTML=rr.runs.slice(0,12).map(x=>`<div class="item"><b>${esc(x.run_id)}</b> <span class="pill ${x.accepted?'ok':'bad'}">${x.accepted?'accepted':'rejected'}</span> <span class="pill">score ${Number(x.final_score??0).toFixed(3)}</span><div class="sub muted">Pareto ${x.pareto_count??0} · vote ${(100*(x.vote_share??0)).toFixed(0)}%</div></div>`).join('')||'No runs';const q=await (await fetch('/api/reviews')).json();$('m_reviews').textContent=q.items.length;const au=await (await fetch('/api/audit?limit=200')).json();$('m_agents').textContent=new Set(au.events.map(x=>x.actor).filter(Boolean)).size;loadRegistry();loadKnowledge() }catch(e){$('health').textContent='offline/auth'}}
async function loadRegistry(){try{const x=await (await fetch('/api/registry')).json();$('registry').innerHTML=[...(x.skills||[]).map(s=>`<div class="item"><b>Skill proposal:</b> ${esc(s.name)} <span class="pill">${esc(s.status)}</span></div>`),...(x.methodologies||[]).map(s=>`<div class="item"><b>Methodology:</b> ${esc(s.title)} <span class="pill">${esc(s.status)}</span></div>`)].join('')||'Empty'}catch{}}async function proposeSkill(){const r=await fetch('/api/skills/propose',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name:$('prop_name').value,description:$('prop_desc').value,source:'human-or-agent'})});alert(JSON.stringify(await r.json()))}async function loadGraph(){const r=await fetch('/api/graph',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({root:$('graph_root').value})});$('graph').textContent=JSON.stringify(await r.json(),null,2)}async function runEvolution(){const feedback=$('ev_feedback').value?JSON.parse($('ev_feedback').value):null;const r=await fetch('/api/evolve',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({skill:$('ev_skill').value,suite:$('ev_suite').value,feedback})});$('evout').textContent=JSON.stringify(await r.json(),null,2)}async function recordShadow(){const x=JSON.parse($('shadow_request').value);const r=await fetch('/api/shadow/record',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(x)});alert(JSON.stringify(await r.json()))}async function runShadow(){const r=await fetch('/api/shadow/run',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({baseline_skill:$('shadow_base').value,candidate_skill:$('shadow_candidate').value,approved:true})});$('shadowout').textContent=JSON.stringify(await r.json(),null,2)}async function loadQueue(){const r=await (await fetch('/api/reviews')).json();$('queue_list').innerHTML=r.items.map(x=>`<div class="item"><div class="row"><b>${esc(x.kind)}</b><span class="pill ${x.priority==='high'?'bad':'warn'}">${esc(x.priority)}</span></div><div class="sub">${esc(x.reason||'')}</div><div class="actions"><button class="btn primary" onclick="decideReview('${x.id}',true)">Approve</button><button class="btn danger" onclick="decideReview('${x.id}',false)">Reject</button></div></div>`).join('')||'No pending items'}async function decideReview(id,ok){await fetch('/api/reviews/decide',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({id,approved:ok})});loadQueue();refresh()}async function sendTelemetry(){const p=JSON.parse($('tele_payload').value||'{}');const r=await fetch('/api/telemetry',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({skill:$('tele_skill').value,agent_id:$('tele_agent').value,event_type:$('tele_type').value,payload:p})});alert(JSON.stringify(await r.json()))}async function submitMethodology(){const r=await fetch('/api/methodologies',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({observation:{content:$('methodology').value}})});alert(JSON.stringify(await r.json()))}async function loadReputation(){const a=$('rep_agent').value;const r=await (await fetch('/api/reputation?agent='+encodeURIComponent(a))).json();$('rep_out').textContent=JSON.stringify(r,null,2)} async function registerAgent(){const r=await fetch('/api/agents/register',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({agent_id:$('rep_agent').value,installation_id:$('rep_install').value})});$('rep_out').textContent=JSON.stringify(await r.json(),null,2)} async function loadKnowledge(){const r=await (await fetch('/api/knowledge/graph')).json();$('kg_out').textContent=JSON.stringify(r,null,2)} async function explainKnowledge(){const q='?source='+encodeURIComponent($('kg_src').value)+'&target='+encodeURIComponent($('kg_tgt').value);const r=await (await fetch('/api/knowledge/path'+q)).json();$('kg_path').textContent=JSON.stringify(r,null,2)} async function loadAudit(){const r=await (await fetch('/api/audit?limit=300')).json();$('auditlog').textContent=JSON.stringify(r.events,null,2)}async function loadProduction(){const r=await (await fetch('/api/production/status')).json();$('prod_status').textContent=JSON.stringify(r,null,2);loadJobs()}async function killSwitch(enabled){const r=await fetch('/api/production/kill-switch',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({enabled,reason:enabled?'manual emergency stop':'manual resume'})});$('prod_status').textContent=JSON.stringify(await r.json(),null,2)}async function mirrorTraffic(){const x=JSON.parse($('tm_payload').value||'{}');x.skill=$('tm_skill').value;const r=await fetch('/api/traffic/mirror',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({...x,candidate_percent:Number($('tm_pct').value)})});$('tm_out').textContent=JSON.stringify(await r.json(),null,2)}async function loadJobs(){const r=await (await fetch('/api/jobs?limit=20')).json();$('jobs').innerHTML=(r.jobs||[]).map(j=>`<div class="item"><b>${esc(j.kind)}</b> · <span class="pill">${esc(j.status)}</span><div class="sub">${esc(j.id)}</div></div>`).join('')||'No jobs'}async function profileEval(){const r=await fetch('/api/eval/profile',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({suite:$('eval_suite').value})});$('eval_profile').textContent=JSON.stringify(await r.json(),null,2)}async function mutateEval(){const r=await fetch('/api/eval/mutate',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({suite:$('eval_suite').value})});$('eval_mutation').textContent=JSON.stringify(await r.json(),null,2)}
async function searchMarketplace(){const r=await (await fetch('/api/marketplace/search?q='+encodeURIComponent($('mp_q').value))).json();$('mp_list').innerHTML=(r.skills||[]).map(x=>`<div class="item"><b>${esc(x.name)}</b> · <span class="pill">${esc(x.certification||'unrated')}</span><div class="sub">${esc(x.version)} · security ${Number(x.security_rating||0).toFixed(2)} · reliability ${Number(x.reliability||0).toFixed(2)}</div><div class="actions"><button class="btn secondary" onclick="installSkill('${esc(x.skill_id)}')">Install</button><button class="btn secondary" onclick="certifyById('${esc(x.skill_id)}')">Certify</button></div></div>`).join('')||'No Skills'}async function publishMarketplace(){const record=JSON.parse($('mp_record').value);const r=await fetch('/api/marketplace/publish',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({record,agent_id:'control-panel'})});$('mp_out').textContent=JSON.stringify(await r.json(),null,2);searchMarketplace()}async function installSkill(id){const r=await fetch('/api/marketplace/install',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({skill_id:id,agent_id:'control-panel'})});$('mp_out').textContent=JSON.stringify(await r.json(),null,2)}async function certifyById(id){const metrics={eval_coverage:.95,regression_rate:0,security:.9,shadow:.9,canary:.9,maintainer_response:.9,telemetry_health:.9};const r=await fetch('/api/marketplace/certify',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({skill_id:id,metrics})});$('mp_out').textContent=JSON.stringify(await r.json(),null,2);searchMarketplace()}async function certifyMarketplace(){const record=JSON.parse($('mp_record').value);const q=await (await fetch('/api/marketplace/search?q='+encodeURIComponent(record.name))).json();if(q.skills?.[0])return certifyById(q.skills[0].skill_id);$('mp_out').textContent='Publish the Skill first'}async function registerNode(){const r=await fetch('/api/federation/register-node',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({node_id:$('fed_node').value,origin:$('fed_origin').value,capabilities:['skills','evals','methodologies','telemetry']})});$('fed_nodes').textContent=JSON.stringify(await r.json(),null,2)}async function loadNodes(){const r=await (await fetch('/api/federation/nodes')).json();$('fed_nodes').textContent=JSON.stringify(r,null,2)}async function signArtifact(){const payload=JSON.parse($('fed_payload').value);const r=await fetch('/api/federation/sign',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({kind:$('fed_kind').value,payload,origin:$('fed_origin').value||'local'})});$('fed_out').textContent=JSON.stringify(await r.json(),null,2)}async function loadArtifacts(){const r=await (await fetch('/api/federation/artifacts')).json();$('fed_out').textContent=JSON.stringify(r,null,2)}async function scanSecurity(){const payload=JSON.parse($('sec_payload').value);const r=await fetch('/api/security/scan',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({payload,agent_id:'control-panel'})});$('sec_out').textContent=JSON.stringify(await r.json(),null,2)}async function redTeamSecurity(){const targets=JSON.parse($('sec_targets').value);const r=await fetch('/api/security/red-team',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({targets,rounds:Number($('sec_rounds').value),agent_id:'red-team-panel'})});$('red_out').textContent=JSON.stringify(await r.json(),null,2)}
loadCfg();refresh();setInterval(refresh,8000);
</script></body></html>'''

def _principal(handler, required=None):
    c=load_config(); a=Authenticator(c.auth.host_token_env,c.auth.agent_token_env,c.auth.user_token_env); host=handler.client_address[0] if handler.client_address else ''
    return a.authenticate(handler.headers,required,host)

def _authorized(handler):
    return _principal(handler,'host') is not None or _principal(handler,None) is not None


def _safe_path(path,roots):
    p=Path(path).resolve()
    if not roots:return p
    allowed=[Path(x).resolve() for x in roots]
    if any(a==p or a in p.parents for a in allowed):return p
    raise ValueError('path is outside configured workspace_roots')

_SERVICE_CACHE={}
def _services(c):
    key=(c.event_store,c.knowledge.path,c.reputation.freshness_halflife_days,c.resilience.max_agent_events_per_minute,c.cache.ttl_seconds)
    x=_SERVICE_CACHE.get(key)
    if x:return x
    store=EventStore(c.event_store)
    kg=KnowledgeGraph(c.knowledge.path) if c.knowledge.enabled else None
    if kg:
        kg.bulk_ingest(store.recent(5000)); store.subscribe(kg.ingest_event)
    rep=ReputationEngine(store,c.reputation.freshness_halflife_days)
    guard=AgentGuard(c.resilience.max_agent_events_per_minute,c.resilience.max_agent_failures,c.resilience.block_seconds)
    gov=VoteGovernor(store,rep)
    marketplace=Marketplace(c.marketplace.path) if c.marketplace.enabled else None
    federation_key=os.environ.get(c.federation.signing_key_env,'') if c.federation.signing_key_env else ''
    federation=FederationStore(c.federation.path,SignedArtifact(federation_key,require_secret=c.federation.require_signed_artifacts),c.federation.trusted_origins) if c.federation.enabled else None
    security_lab=SecurityLab() if c.security_lab.enabled else None
    identity=IdentityStore()
    corpus=EvalCorpus(c.eval_corpus.root)
    bench=BenchmarkStore(c.eval_corpus.benchmark_path)
    idem=Idempotency(store)
    cache=TTLCache(c.cache.ttl_seconds,c.cache.max_items)
    kills=KillSwitchRegistry(c.production.kill_switch_path)
    x=(store,kg,rep,guard,gov,marketplace,federation,security_lab,identity,corpus,bench,idem,cache,kills); _SERVICE_CACHE[key]=x; return x


HOST_HTML='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>skIF Host Control</title><style>body{font-family:system-ui;max-width:1100px;margin:40px auto;padding:20px;background:#f4f7fb}div{background:#fff;padding:18px;border-radius:14px;margin:12px 0}button{padding:9px 14px;border:0;border-radius:9px}</style></head><body><h1>skIF Host Control Plane</h1><p>Host-only administration, policy, deployment, federation trust, security lab and lifecycle controls.</p><div><button onclick="location=\'/api/health\'">Health</button> <button onclick="location=\'/api/security/status\'">Security</button> <button onclick="location=\'/api/production/status\'">Production</button> <button onclick="location=\'/api/eval/leaderboard\'">Eval Leaderboard</button></div><div><strong>Boundary:</strong> this dashboard accepts only the configured Host token. Agent/User principals cannot enter.</div></body></html>'
AGENT_HTML='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>skIF Agent Console</title><style>body{font-family:system-ui;max-width:900px;margin:40px auto;padding:20px;background:#eef8f3}div{background:#fff;padding:18px;border-radius:14px;margin:12px 0}</style></head><body><h1>skIF Agent Console</h1><p>Contribute telemetry, feedback, votes, patches, evaluations and methodology. Host administration is intentionally unavailable here.</p><div>Agent-facing endpoints: reputation, contributions, capabilities, marketplace, knowledge, methodology and Skill improvement.</div></body></html>'
USER_HTML='<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>skIF User Portal</title><style>body{font-family:system-ui;max-width:900px;margin:40px auto;padding:20px;background:#f7f3ff}div{background:#fff;padding:18px;border-radius:14px;margin:12px 0}</style></head><body><h1>skIF User Portal</h1><p>Browse Skills, certifications and public ecosystem information. Host controls are unavailable.</p><div>Use the Agent Console or API for contributions.</div></body></html>'

class H(BaseHTTPRequestHandler):
    def j(self,code,obj):
        b=json.dumps(obj,ensure_ascii=False,default=str).encode();self.send_response(code);self.send_header('Content-Type','application/json');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b)
    def body(self, max_bytes=2_000_000):
        length=self.headers.get('Content-Length')
        if length is None:
            if self.command=='POST': raise ValueError('Content-Length required')
            return {}
        raw_len=int(length or 0)
        if raw_len<0 or raw_len>max_bytes: raise ValueError('request body too large')
        raw=self.rfile.read(raw_len)
        return json.loads(raw or '{}')
    def do_GET(self):
        path=urlparse(self.path).path;c=load_config()
        if path=='/':
            landing=b'<html><body><h1>skIF</h1><p>Use /host, /agent, or /user with the matching principal token.</p></body></html>';self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(landing)));self.end_headers();self.wfile.write(landing);return
        if path in ('/host/neo','/host/neo/'):
            if _principal(self,'host') is None:return self.j(401,{'error':'host-auth-required'})
            b=neo_page('host').encode();self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        if path in ('/agent/neo','/agent/neo/'):
            if _principal(self,'agent') is None:return self.j(401,{'error':'agent-auth-required'})
            b=neo_page('agent').encode();self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        if path in ('/user/neo','/user/neo/'):
            if _principal(self,'user') is None:return self.j(401,{'error':'user-auth-required'})
            b=neo_page('user').encode();self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        if path in ('/host','/host/'):
            if _principal(self,'host') is None:return self.j(401,{'error':'host-auth-required'})
            b=HOST_HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        if path in ('/agent','/agent/'):
            if _principal(self,'agent') is None:return self.j(401,{'error':'agent-auth-required'})
            b=AGENT_HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        if path in ('/user','/user/'):
            if _principal(self,'user') is None:return self.j(401,{'error':'user-auth-required'})
            b=USER_HTML.encode();self.send_response(200);self.send_header('Content-Type','text/html');self.send_header('Content-Length',str(len(b)));self.end_headers();self.wfile.write(b);return
        principal=_principal(self,'host') or _principal(self,'agent') or _principal(self,'user')
        if principal is None:return self.j(401,{'error':'unauthorized'})
        store,kg,rep,agent_guard,vote_gov,marketplace,federation,security_lab,identity,corpus,bench,idem,cache,kills=_services(c)
        host_only={'/api/config','/api/runs','/api/jobs','/api/audit','/api/reviews','/api/production/status','/api/kill-switch','/api/eventstore/health','/api/federation/quarantine'}
        if path in host_only and principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
        if path.startswith('/api/security/') and principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
        if path=='/api/config':return self.j(200,{'config':c.to_json()})
        if path=='/api/health':return self.j(200,{'ok':True,'name':'skIF','version':'3.1.0-Neo','mode':c.deployment_mode,'node_id':c.node_id,'ts':time.time()})
        if path=='/api/runs':
            base=Path(c.artifacts_dir);base.mkdir(parents=True,exist_ok=True);rows=[]
            for p in sorted(base.glob('*/result.json'),reverse=True)[:100]:
                try:
                    x=json.loads(p.read_text());g=x.get('generations',[]);last=g[-1] if g else {};v=last.get('vote',{});rows.append({'run_id':x.get('run_id',p.parent.name),'promoted':x.get('promoted',False),'accepted':x.get('accepted',False),'vote_share':v.get('vote_share'),'base_score':x.get('base_eval',{}).get('score'),'final_score':x.get('final_base_eval',{}).get('score'),'pareto_count':len(last.get('pareto_frontier',[]))})
                except Exception:pass
            return self.j(200,{'runs':rows})
        if path=='/api/registry':return self.j(200,{'skills':list_skill_proposals(c.registry_dir),'methodologies':list_methodologies(c.registry_dir),'marketplace':marketplace.search('',50) if marketplace else []})
        if path=='/api/jobs':return self.j(200,{'jobs':get_queue(c.event_store,c.queue.workers).recent(int((urlparse(self.path).query.split('limit=')[-1] if 'limit=' in urlparse(self.path).query else 100)))})
        if path=='/api/jobs/recover':return self.j(200,{'recovered':get_queue(c.event_store,c.queue.workers).recover()})
        if path.startswith('/api/jobs/'):
            job=get_queue(c.event_store,c.queue.workers).status(path.rsplit('/',1)[-1]); return self.j(200,job or {'error':'job not found'})
        if path=='/api/reputation':
            agent=urlparse(self.path).query.split('agent=')[-1] if 'agent=' in urlparse(self.path).query else ''
            return self.j(200, rep.score(agent) if agent else {'error':'agent query required'})
        if path in ('/api/knowledge/graph','/api/knowledge/neighborhood','/api/knowledge/path') and principal.kind!='host':
            return self.j(403,{'error':'host-principal-required'})
        if path=='/api/knowledge/graph':
            return self.j(200, kg.graph() if kg else {'nodes':[],'edges':[]})
        if path=='/api/knowledge/neighborhood':
            q=urlparse(self.path).query; node=q.split('node=')[-1].split('&')[0] if 'node=' in q else ''; depth=int(q.split('depth=')[-1]) if 'depth=' in q else c.knowledge.neighborhood_depth
            return self.j(200, kg.neighborhood(node,depth) if kg and node else {'error':'node query required'})
        if path=='/api/knowledge/path':
            q=urlparse(self.path).query; src=q.split('source=')[-1].split('&')[0] if 'source=' in q else ''; tgt=q.split('target=')[-1].split('&')[0] if 'target=' in q else ''
            return self.j(200, kg.explain_path(src,tgt) if kg and src and tgt else {'error':'source and target required'})
        if path=='/api/marketplace/search':
            q=urlparse(self.path).query; query=q.split('q=',1)[1].split('&',1)[0] if 'q=' in q else ''; return self.j(200,{'skills':marketplace.search(query,50,None,c.marketplace.minimum_security) if marketplace else []})
        if path=='/api/federation/artifacts':
            q=urlparse(self.path).query; kind=q.split('kind=',1)[1].split('&',1)[0] if 'kind=' in q else ''; return self.j(200,{'artifacts':federation.list(kind) if federation else []})
        if path=='/api/federation/nodes':return self.j(200,{'nodes':federation.nodes() if federation else []})
        if path=='/api/security/status':return self.j(200,{'enabled':c.security_lab.enabled,'rounds':c.security_lab.rounds,'federation':c.federation.enabled,'marketplace':c.marketplace.enabled,'hardening':'3.1-Neo-defense-in-depth'})
        if path=='/api/production/status':
            return self.j(200,{'kill_switch':kills.status(),'queue':c.queue.__dict__,'canary':c.canary.__dict__,'shadow':c.shadow.__dict__})

        if path=='/api/shadow/requests':return self.j(200,{'requests':load_requests(c.shadow.request_store,c.shadow.max_requests)})
        if path=='/api/reviews':return self.j(200,{'items':ReviewQueue(Path(c.registry_dir)/'reviews').list('pending')})
        if path=='/api/audit':return self.j(200,{'events':EventStore(c.event_store).recent(int((urlparse(self.path).query.split('limit=')[-1] if 'limit=' in urlparse(self.path).query else 200)))})
        if path=='/api/errors/summary':
            from .errors import recent_errors,review_signal
            f=Path(c.registry_dir)/'errors.jsonl';errs=[]
            if f.exists():
                for line in f.read_text().splitlines():
                    try:errs.append(json.loads(line))
                    except:pass
            return self.j(200,review_signal(errs,c.errors.absolute_threshold,c.errors.delta_threshold))
        if path=='/api/identity':return self.j(200,{'agents':identity.list()})
        if path=='/api/eval/corpora':return self.j(200,{'corpora':list(corpus._load().values())})
        if path=='/api/eval/leaderboard':return self.j(200,{'rows':bench.leaderboard()})
        if path=='/api/federation/quarantine':return self.j(200,{'items':federation.quarantine() if federation else []})
        if path=='/api/kill-switch':return self.j(200,kills.status())
        if path=='/api/cache/status':return self.j(200,cache.stats())
        if path=='/api/eventstore/health':return self.j(200,store.health())
        if path=='/api/federation/network':
            net=FederationNetwork(c.federation.path+'/network',c.federation.origin,signer=federation.signer if federation else None); return self.j(200,{'nodes':net.nodes(),'policy':net.policy.__dict__})
        if path=='/api/research':
            ros=ResearchOS(store); return self.j(200,{'experiments':ros.list(100)})
        if path=='/api/identity/portable':
            if principal.kind!='host': return self.j(403,{'error':'host-principal-required'})
            return self.j(200,{'enabled':bool(os.environ.get('SKIF_IDENTITY_KEY')),'issuer':c.federation.origin})
        if path=='/api/auth/me':return self.j(200,{'kind':principal.kind,'subject':principal.subject,'local':principal.local,'mode':c.deployment_mode,'node_id':c.node_id,'capabilities':c.agent_default_capabilities if principal.kind=='agent' else ['host-all'] if principal.kind=='host' else ['user-read']})
        if path=='/api/control/schema':
            return self.j(200,{'mode':c.deployment_mode,'node_id':c.node_id,'host_custom':c.host_custom,'prediction_market_enabled':c.prediction_market_enabled,'plugin_allowlist':c.plugin_allowlist,'agent_default_capabilities':c.agent_default_capabilities,'resource_governance':c.resource_governance})
        if path=='/api/benchmark/global':
            subject=urlparse(self.path).query.split('subject=',1)[1].split('&',1)[0] if 'subject=' in urlparse(self.path).query else None
            return self.j(200,{'rows':GlobalBenchmarkNetwork().leaderboard(subject)})
        if path=='/api/knowledge/mesh':
            q=urlparse(self.path).query; kind=q.split('kind=',1)[1].split('&',1)[0] if 'kind=' in q else None
            mesh,_,_,_,_,_,_= _neo_services(c,store,marketplace,rep,cache)
            allowed=['private','community','federation','public'] if principal.kind=='host' else ['community','federation','public'] if principal.kind=='agent' else ['public']
            return self.j(200,{'nodes':mesh.query(kind=kind,visibilities=allowed),'health':{'enabled':c.knowledge.enabled}})
        if path=='/api/knowledge/mesh/path':
            qs=parse_qs(urlparse(self.path).query); src=qs.get('source',[''])[0]; tgt=qs.get('target',[''])[0]
            mesh,_,_,_,_,_,_= _neo_services(c,store,marketplace,rep,cache)
            allowed=['private','community','federation','public'] if principal.kind=='host' else ['community','federation','public'] if principal.kind=='agent' else ['public']
            return self.j(200,{'path':mesh.path(src,tgt,visibilities=allowed)})
        if path=='/api/agent/recommend':
            qs=parse_qs(urlparse(self.path).query); task=qs.get('task',[''])[0]; agent=qs.get('agent',[principal.subject])[0]
            _,_,resources,_,_,_,agent_os=_neo_services(c,store,marketplace,rep,cache); return self.j(200,{'recommendations':agent_os.recommend(task,agent_id=agent),'resource_policy':resources.policy.__dict__})
        if path=='/api/governance/decisions':return self.j(200,{'events':[e for e in store.recent(200) if e.get('event_type')=='governance_decision']})
        if path=='/api/predictions/calibration':
            if not c.prediction_market_enabled:return self.j(409,{'error':'prediction market disabled'})
            q=urlparse(self.path).query; a=q.split('agent=',1)[1].split('&',1)[0] if 'agent=' in q else principal.subject; return self.j(200,PredictionMarket().calibration(a))
        return self.j(404,{'error':'not found'})
    def do_POST(self):
        path=urlparse(self.path).path;c=load_config();principal=_principal(self,'host') or _principal(self,'agent') or _principal(self,'user')
        if principal is None:return self.j(401,{'error':'unauthorized'})
        store,kg,rep,agent_guard,vote_gov,marketplace,federation,security_lab,identity,corpus,bench,idem,cache,kills=_services(c)
        try:
            body=self.body(c.resilience.max_request_bytes)
            if kills.blocked('agent') and path in ('/api/telemetry','/api/errors','/api/community/vote','/api/contributions','/api/methodologies','/api/skills/propose'):
                return self.j(503,{'error':'agent-kill-switch-enabled'})
            if kills.blocked('federation') and path.startswith('/api/federation/'):
                return self.j(503,{'error':'federation-kill-switch-enabled'})
            if kills.blocked('research') and path.startswith('/api/autonomous/'):
                return self.j(503,{'error':'research-kill-switch-enabled'})
            if kills.blocked('evolution') and path.startswith('/api/evolve'):
                return self.j(503,{'error':'evolution-kill-switch-enabled'})
            agent_id=str(body.get('agent_id') or body.get('source') or 'agent')
            source_ip=self.client_address[0] if self.client_address else 'unknown'
            guard_key=f'{agent_id}@{source_ip}'
            if c.resilience.enabled and not agent_guard.allow(guard_key): return self.j(429,{'error':'agent/source temporarily rate-limited','agent_id':agent_id})
            if path=='/api/federation/marketplace/import-skill':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                net=FederationNetwork(c.federation.path+'/network',c.federation.origin,signer=federation.signer if federation else None)
                bridge=FederationMarketplace(marketplace,federation,net)
                row=bridge.import_skill(body.get('artifact',{}),body.get('remote_policy'),float(body.get('min_security',c.marketplace.minimum_security)))
                store.emit('federated_skill_imported',actor=principal.subject,skill=row.get('skill_id',''),payload=row); return self.j(201,row)
            if path=='/api/federation/network/connect':
                if principal.kind!='host': return self.j(403,{'error':'host-principal-required'})
                net=FederationNetwork(c.federation.path+'/network',c.federation.origin,signer=federation.signer if federation else None)
                policy=body.get('policy',{}) or {}; return self.j(201,net.connect(body.get('node_id',''),body.get('url',''),policy,body.get('capabilities',[])))
            if path=='/api/federation/network/plan-sync':
                if principal.kind not in ('host','agent'): return self.j(403,{'error':'host-or-agent-required'})
                net=FederationNetwork(c.federation.path+'/network',c.federation.origin,signer=federation.signer if federation else None); return self.j(200,net.plan_sync(body.get('node_id',''),body.get('artifact_kinds')))
            if path=='/api/trust/negotiate':
                a=TrustPolicy(**(body.get('local') or {})); b=TrustPolicy(**(body.get('remote') or {})); return self.j(200,negotiate_trust(a,b))
            if path=='/api/identity/portable/issue':
                if principal.kind!='host': return self.j(403,{'error':'host-principal-required'})
                ident=identity.get(str(body.get('agent_id','')))
                if not ident:return self.j(404,{'error':'agent-not-found'})
                secret=os.environ.get('SKIF_IDENTITY_KEY','')
                if not secret:return self.j(503,{'error':'SKIF_IDENTITY_KEY-not-configured'})
                score=rep.score(ident['agent_id']) if hasattr(rep,'score') else {'reputation':0.5}
                auth=PortableIdentityAuthority(c.federation.origin,secret); return self.j(201,auth.issue(ident['agent_id'],body.get('node_id',c.federation.origin),score.get('reputation',0.5),ident.get('trust_level','unknown'),ident.get('capabilities',[])))
            if path=='/api/identity/portable/verify':
                auth=PortableIdentityAuthority(c.federation.origin,os.environ.get('SKIF_IDENTITY_KEY','')) if os.environ.get('SKIF_IDENTITY_KEY') else None
                if not auth:return self.j(503,{'error':'SKIF_IDENTITY_KEY-not-configured'})
                return self.j(200,auth.verify(body.get('credential',{}),expected_subject=body.get('node_id'),min_reputation=float(body.get('min_reputation',0))))
            if path=='/api/telemetry/privacy':
                if principal.kind not in ('agent','host'):return self.j(403,{'error':'agent-or-host-required'})
                events=body.get('events',[]) or []; counts=local_aggregate(events); dp=differential_private_counts(counts,float(body.get('epsilon',1.0))); return self.j(200,{'local':counts,'differential_private':dp,'redacted_sample':TelemetryProtector().selective_disclosure((events[0] if events else {}),body.get('fields',['event_type','skill']))})
            if path=='/api/telemetry/encrypt':
                if principal.kind not in ('agent','host'):return self.j(403,{'error':'agent-or-host-required'})
                prot=TelemetryProtector.from_env(); return self.j(200,{'ciphertext':prot.encrypt(body.get('payload',{}))})
            if path=='/api/telemetry/decrypt':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                prot=TelemetryProtector.from_env(); return self.j(200,prot.decrypt(body.get('ciphertext','')))
            if path=='/api/research/create':
                if principal.kind not in ('host','agent'):return self.j(403,{'error':'host-or-agent-required'})
                ros=ResearchOS(store); return self.j(201,ros.create(body.get('observation',{}),body.get('agent_id',principal.subject),body.get('skill','')))
            if path=='/api/research/transition':
                if principal.kind not in ('host','agent'):return self.j(403,{'error':'host-or-agent-required'})
                ros=ResearchOS(store); return self.j(200,ros.transition(body.get('research_id',''),body.get('phase',''),body.get('data',{}),body.get('agent_id',principal.subject)))
            if path=='/api/skills/compose':
                if principal.kind not in ('host','agent'):return self.j(403,{'error':'host-or-agent-required'})
                paths=[str(_safe_path(x,c.workspace_roots)) for x in body.get('skills',[])]; out=_safe_path(body.get('output',''),c.workspace_roots); return self.j(201,compose_skills(paths,out,body.get('methodologies')))
            if path=='/api/skills/fork':
                if principal.kind not in ('host','agent'):return self.j(403,{'error':'host-or-agent-required'})
                src=_safe_path(body.get('skill',''),c.workspace_roots); dst=_safe_path(body.get('target',''),c.workspace_roots); return self.j(201,fork_skill(src,dst,body.get('branch','fork')))
            if path=='/api/skills/merge':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                a=_safe_path(body.get('skill_a',''),c.workspace_roots); b=_safe_path(body.get('skill_b',''),c.workspace_roots); out=_safe_path(body.get('output',''),c.workspace_roots); return self.j(201,merge_skills(a,b,out,body.get('methodology')))
            if path=='/api/production/kill-switch':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                row=kills.set(str(body.get('scope','global')),bool(body.get('enabled')),body.get('reason',''),principal.subject);store.emit('kill_switch_changed',actor=principal.subject,actor_type='host',payload={'scope':body.get('scope','global'),**row});return self.j(200,row)
            if path=='/api/evolve-async':
                from .evolution import EvolutionEngine
                q=get_queue(c.event_store,c.queue.workers)
                def run_job(payload):
                    skill=_safe_path(payload['skill'],c.workspace_roots);suite=_safe_path(payload['suite'],c.workspace_roots)
                    return EvolutionEngine(c,Path(c.artifacts_dir)).run(skill,suite,feedback=payload.get('feedback'),agent_patch=payload.get('patch'),promote=bool(payload.get('promote',False)))
                return self.j(202,q.submit('evolution',body,run_job))
            if path=='/api/eval/profile':
                suite=json.loads(_safe_path(body.get('suite',''),c.workspace_roots).read_text())['cases']; return self.j(200,corpus_profile(suite))
            if path=='/api/eval/mutate':
                suite=json.loads(_safe_path(body.get('suite',''),c.workspace_roots).read_text())['cases']; muts=generate_mutations(suite,body.get('variants'),int(body.get('max_per_case',c.eval_intelligence.mutations_per_case))); out=validate_and_propose(muts);store.emit('eval_mutation_proposed',actor=body.get('actor','agent'),payload={'count':len(muts),'accepted':len(out['accepted'])});return self.j(200,{'mutations':muts,'validated':out})
            if path=='/api/eval/validate':return self.j(200,validate_and_propose(body.get('cases',[])))
            if path=='/api/agents/capabilities':
                if principal.kind not in ('agent','host'):return self.j(403,{'error':'agent-or-host-required'})
                aid=str(body.get('agent_id',principal.subject)); row=identity.register(aid,body.get('installation_id',''),body.get('public_key',''),body.get('display_name',''),body.get('capabilities',[]),body.get('metadata',{}),requested_id=aid);store.emit('agent_capability_updated',actor=aid,actor_type='agent',payload=row);return self.j(200,row)
            if path=='/api/contributions':
                if principal.kind not in ('agent','host'):return self.j(403,{'error':'agent-or-host-required'})
                from .contribution import make,validate
                item=make(principal.subject,body.get('skill_id',''),body.get('action','observe'),body.get('summary',''),body.get('evidence'),body.get('references'),body.get('idempotency_key',''));ok,reason=validate(item)
                if not ok:return self.j(400,{'error':reason})
                key=item.get('idempotency_key') or f"contribution:{item['contribution_id']}";claimed,existing=idem.claim(key,'contribution')
                if not claimed:return self.j(200,existing or {'deduplicated':True})
                row=store.emit('eval_contribution' if item['action'] in ('evaluation','test') else 'skill_feedback',actor=principal.subject,actor_type=principal.kind,skill=item['skill_id'],payload=item,idempotency_key=key);idem.complete(key,row,'contribution');return self.j(201,row)
            if path=='/api/eval/create':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                row=corpus.create(body.get('name','skill-suite'),body.get('cases',[]),body.get('owner',principal.subject),body.get('version','1.0.0'),body.get('state','draft'));return self.j(201,row)
            if path=='/api/eval/transition':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                return self.j(200,corpus.transition(body['corpus_id'],body['state']))
            if path=='/api/eval/propose':
                if principal.kind not in ('agent','host'):return self.j(403,{'error':'agent-or-host-required'})
                row=corpus.propose_cases(body.get('cases',[]),principal.subject,body.get('reason',''));store.emit('eval_proposed',actor=principal.subject,actor_type=principal.kind,payload=row);return self.j(201,row)
            if path=='/api/benchmark/global/publish':
                if principal.kind not in ('host','agent'):return self.j(403,{'error':'host-or-agent-required'})
                return self.j(201,GlobalBenchmarkNetwork().publish(body.get('origin',c.node_id),body.get('rows',[]),body.get('signature','')))
            if path=='/api/eval/record-benchmark':
                if principal.kind not in ('host','agent'):return self.j(403,{'error':'host-or-agent-required'})
                row=bench.record(body.get('subject','unknown'),body.get('corpus_id',''),body.get('score',0),body.get('pass_rate',0),body.get('cost',0),body.get('latency_ms',0),body.get('metadata'));return self.j(201,row)
            if path=='/api/security/fuzz':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                return self.j(200,security_lab.fuzz(body.get('payload',{}),body.get('mutations',c.security_hardening.fuzz_mutations)))
            if path=='/api/security/adversarial':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                return self.j(200,security_lab.autonomous_adversarial(body.get('targets',{}),body.get('rounds',c.security_hardening.continuous_fuzz_rounds)))
            if path=='/api/security/judge-attack':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                return self.j(200,security_lab.judge_attack(body.get('output','')))
            if path=='/api/security/federation-attack':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                return self.j(200,security_lab.federation_attack(body.get('artifact',{})))
            if path=='/api/security/sandbox-test':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                return self.j(200,security_lab.sandbox_test(body.get('command','')))
            if path=='/api/security/continuous-fuzz':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                result=security_lab.fuzz(body.get('payload',body),int(body.get('mutations',c.security_hardening.fuzz_mutations))); store.emit('security_fuzz',actor=principal.subject,payload=result); return self.j(200,result)
            if path=='/api/security/supply-chain':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                result=security_lab.dependency_scan(body.get('dependencies',[])); store.emit('supply_chain_scan',actor=principal.subject,payload=result); return self.j(200,result)
            if path=='/api/security/simulate-vote-attack':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                result=security_lab.vote_attack(body.get('votes',[]),int(body.get('identities',100))); store.emit('vote_attack_simulation',actor=principal.subject,payload=result); return self.j(200,result)
            if path=='/api/security/dependency-scan':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                return self.j(200,security_lab.dependency_scan(body.get('dependencies',[])))
            if path=='/api/federation/release':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                if not federation:return self.j(409,{'error':'federation disabled'})
                return self.j(200,federation.release(body.get('artifact_id',''),principal.subject))
            if path=='/api/research/team':
                if principal.kind not in ('host','agent'):return self.j(403,{'error':'host-or-agent-required'})
                from .teams import AgentTeam
                team=AgentTeam(objective=body.get('objective',''),budget=float(body.get('budget',100)))
                for m in body.get('members',[]):team.add(m.get('agent_id',''),m.get('role','worker'),m.get('weight',1),m.get('capabilities',[]))
                return self.j(201,team.assign(body.get('tasks',[]),body.get('required_capabilities',[])))
            if path=='/api/knowledge/mesh/export':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                mesh,_,_,_,_,_,_=_neo_services(c,store,marketplace,rep,cache); return self.j(200,mesh.export_bundle(body.get('visibility','federation'),c.node_id))
            if path=='/api/knowledge/mesh/import':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                mesh,_,_,_,_,_,_=_neo_services(c,store,marketplace,rep,cache); return self.j(201,mesh.import_bundle(body.get('bundle',{}),c.federation.trusted_origins))
            if path=='/api/predictions/create':
                if not c.prediction_market_enabled:return self.j(409,{'error':'prediction market disabled'})
                if principal.kind not in ('agent','host'):return self.j(403,{'error':'agent-or-host-required'})
                return self.j(201,PredictionMarket().create(principal.subject,body.get('subject',''),body.get('probability',0),body.get('deadline'),body.get('evidence',[])))
            if path=='/api/predictions/resolve':
                if not c.prediction_market_enabled or principal.kind!='host':return self.j(403,{'error':'host-principal-required-or-disabled'})
                return self.j(200,PredictionMarket().resolve(body.get('prediction_id',''),body.get('outcome',False)))
            if path=='/api/plugins':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                return self.j(200,{'plugins':c.plugin_allowlist,'mode':c.deployment_mode})
            if path=='/api/onboarding':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                c.providers={k:ProviderConfig(**v) for k,v in body.get('providers',{}).items()};c.roles={r:RoleConfig(**body.get('roles',{}).get(r,{})) for r in ROLES}
                scalar=('submission_mode','patch_mode','alternatives','voting_enabled','vote_mode','vote_threshold','pareto_enabled','require_human_approval_to_promote','judge_min_calibration','autonomous_loops','event_store','contribution_message_path','deployment_mode','node_id','host_custom','agent_default_capabilities','prediction_market_enabled','resource_governance','plugin_allowlist')
                for k in scalar:
                    if k in body:setattr(c,k,body[k])
                for group,keymap in [('budget',c.budget),('deployment',c.deployment),('runtime',c.runtime),('production',c.production),('eval_intelligence',c.eval_intelligence),('queue',c.queue),('dataset',c.dataset),('shadow',c.shadow),('errors',c.errors),('battle',c.battle),('methodology',c.methodology),('proposals',c.proposals),('canary',c.canary),('compatibility',c.compatibility),('telemetry',c.telemetry),('reputation',c.reputation),('resilience',c.resilience),('knowledge',c.knowledge),('marketplace',c.marketplace),('federation',c.federation),('auth',c.auth),('eval_corpus',c.eval_corpus),('cache',c.cache),('performance',c.performance),('security_hardening',c.security_hardening),('security_lab',c.security_lab),('github',c.github)]:
                    for k,v in body.get(group,{}).items():
                        if hasattr(keymap,k):setattr(keymap,k,v)
                save_config(c);store.emit('configuration_saved',actor='human',payload={'version':'3.1.0-Neo'});return self.j(200,{'ok':True,'config':c.to_json()})
            if path=='/api/graph':return self.j(200,analyze_skill_graph(_safe_path(body.get('root',''),c.workspace_roots),body.get('changed',[])))
            if path=='/api/dataset/strengthen':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                from .roles import role_provider_pool
                out=strengthen_suite(role_provider_pool(c,'critic'),[str(_safe_path(x,c.workspace_roots)) for x in body.get('skills',[])],_safe_path(body.get('suite',''),c.workspace_roots),int(body.get('cases_per_skill',c.dataset.cases_per_skill)));store.emit('dataset_strengthened',actor=body.get('actor','agent'),payload=out);return self.j(200,out)
            if path=='/api/traffic/mirror':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                mirror=TrafficMirror(store,KillSwitch(c.production.kill_switch_path),c.production.dedupe_max); out=mirror.mirror(body,int(body.get('candidate_percent',100))); return self.j(200,out)
            if path=='/api/shadow/record':
                if not c.shadow.enabled:return self.j(409,{'error':'shadow disabled'})
                row=append_request(c.shadow.request_store,body);store.emit('shadow_request_recorded',actor=body.get('agent_id','agent'),skill=body.get('skill',''),payload=row);return self.j(201,row)
            if path=='/api/shadow/run':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                if not c.shadow.enabled:return self.j(409,{'error':'shadow disabled'})
                if c.shadow.require_candidate_approval and not bool(body.get('approved',False)):return self.j(403,{'error':'shadow candidate approval required'})
                from .roles import role_provider_pool
                baseline=_safe_path(body.get('baseline_skill',''),c.workspace_roots);candidate=_safe_path(body.get('candidate_skill',''),c.workspace_roots);requests=body.get('requests') or load_requests(c.shadow.request_store,c.shadow.max_requests);cases=[]
                for r in requests[:c.shadow.max_requests]:
                    if r.get('case'):cases.append(r['case'])
                    elif r.get('prompt'):cases.append({'id':r['id'],'prompt':r['prompt'],'success_criteria':r.get('success_criteria',[]),'constraints':r.get('constraints',[]),'mandatory':r.get('mandatory',False)})
                e=ShadowEngine(role_provider_pool(c,'worker')[0],role_provider_pool(c,'critic')[0],None);out=e.run(baseline,candidate,cases,[],body.get('mirror_id',''),max_requests=c.shadow.max_requests,min_requests=c.shadow.min_requests,alpha=c.shadow.alpha,min_effect=c.shadow.min_effect);store.emit('shadow_completed',actor='skIF',payload={'n':out['n'],'score_delta':out['score_delta'],'statistics':out.get('statistics',{})});return self.j(200,out)
            if path=='/api/errors':
                row=report_error(c.registry_dir,body.get('skill','unknown'),body.get('message',''),body.get('severity','medium'),body.get('tool',''),body.get('trajectory'));store.emit('error_reported',actor=body.get('agent_id','agent'),skill=body.get('skill',''),payload=row);return self.j(201,row)
            if path=='/api/agents/register':
                agent=str(body.get('agent_id','')); installation=str(body.get('installation_id',''));
                if not agent:return self.j(400,{'error':'agent_id required'})
                row=rep.register(agent,installation,bool(body.get('trusted',False)),body.get('metadata',{})); return self.j(201,{'registered':True,'event':row,'reputation':rep.score(agent)})
            if path=='/api/agents/reputation':
                agent=str(body.get('agent_id','')); return self.j(200,rep.score(agent))
            if path=='/api/marketplace/publish':
                if principal.kind not in ('host','agent'):return self.j(403,{'error':'host-or-agent-required'})
                if not marketplace:return self.j(409,{'error':'marketplace disabled'})
                record=body.get('record',body); publisher=str(body.get('agent_id',record.get('owner','agent'))); ps=rep.score(publisher); record['publisher_reputation']=ps['reputation']; record['publisher_trust']=('trusted' if ps['reputation']>=0.8 else 'observed'); row=marketplace.publish(record); store.emit('skill_published',actor=publisher,actor_type=principal.kind,skill=record.get('name',''),payload={'skill_id':row['skill_id'],'version':row.get('version'),'publisher_reputation':ps['reputation']}); return self.j(201,row)
            if path=='/api/marketplace/certify':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                if not marketplace:return self.j(409,{'error':'marketplace disabled'})
                return self.j(200,marketplace.certify(str(body.get('skill_id','')),body.get('metrics',{})))
            if path=='/api/marketplace/install':
                if principal.kind not in ('agent','user','host'):return self.j(403,{'error':'valid-principal-required'})
                if not marketplace:return self.j(409,{'error':'marketplace disabled'})
                sid=str(body.get('skill_id','')); found=next((x for x in marketplace.search('',100) if x.get('skill_id')==sid),None)
                if not found:return self.j(404,{'error':'skill not found'})
                if float(found.get('security_rating',0)) < c.marketplace.minimum_security:return self.j(403,{'error':'security rating below install policy','security_rating':found.get('security_rating',0),'required':c.marketplace.minimum_security})
                if c.marketplace.require_certification_for_install and found.get('certification') in ('unrated','bronze'):return self.j(403,{'error':'certification below install policy','certification':found.get('certification')})
                if found.get('provenance_status')=='rejected':return self.j(403,{'error':'provenance rejected'})
                row=marketplace.install_record(sid,str(body.get('agent_id','agent')),body.get('version',''))
                store.emit('skill_installed',actor=row['agent_id'],skill=row['skill_id'],payload=row); return self.j(200,row)
            if path=='/api/federation/register-node':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                if not federation:return self.j(409,{'error':'federation disabled'})
                return self.j(201,federation.register_node(body.get('node_id',''),body.get('origin',c.federation.origin),body.get('capabilities',[])))
            if path=='/api/federation/heartbeat':
                if principal.kind not in ('host','agent'):return self.j(403,{'error':'host-or-agent-required'})
                if not federation:return self.j(409,{'error':'federation disabled'})
                return self.j(200,federation.heartbeat(body.get('node_id','')))
            if path=='/api/federation/sign':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                if not federation:return self.j(409,{'error':'federation disabled'})
                kind=str(body.get('kind','')); artifact=federation.signer.sign(kind,body.get('payload',{}),body.get('origin') or c.federation.origin); return self.j(200,artifact)
            if path=='/api/federation/ingest':
                if principal.kind not in ('host','agent'):return self.j(403,{'error':'host-or-agent-required'})
                if not federation:return self.j(409,{'error':'federation disabled'})
                return self.j(201,federation.ingest(body.get('artifact',body)))
            if path=='/api/federation/sync':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                if not federation:return self.j(409,{'error':'federation disabled'})
                return self.j(200,federation.sync(body.get('artifacts',[])))
            if path=='/api/security/scan':
                if not security_lab:return self.j(409,{'error':'security lab disabled'})
                result=security_lab.scan(body.get('payload',body)); store.emit('security_scan',actor=body.get('agent_id','agent'),payload=result); return self.j(200,result)
            if path=='/api/security/red-team':
                if not security_lab:return self.j(409,{'error':'security lab disabled'})
                result=security_lab.red_team(body.get('targets',{}),body.get('rounds',c.security_lab.rounds));
                actor=body.get('agent_id','red-team'); store.emit('red_team_scan',actor=actor,payload={'source':'security_lab','results':result})
                if not result['passed']: store.emit('security_incident',actor=actor,payload={'source':'security_lab','results':result})
                return self.j(200,result)
            if path=='/api/security/status':
                return self.j(200,{'enabled':c.security_lab.enabled,'rounds':c.security_lab.rounds,'federation':c.federation.enabled,'marketplace':c.marketplace.enabled})
            if path=='/api/agents/guard':
                agent=str(body.get('agent_id','')); return self.j(200,agent_guard.status(agent))
            if path=='/api/community/vote':
                if principal.kind not in ('agent','host'):return self.j(403,{'error':'agent-or-host-required'})
                agent=str(body.get('agent_id',principal.subject)); key=str(body.get('idempotency_key') or f'{agent}:{body.get("skill","")}:vote:{body.get("run_id","")}:{body.get("candidate","")}: {body.get("choice","")}')
                claimed,existing=idem.claim(key,'vote')
                if not claimed:return self.j(200,existing or {'deduplicated':True})
                decision=vote_gov.decide(agent,body.get('skill',''),body.get('run_id',''),body.get('candidate'),body.get('choice'),float(body.get('confidence',0)))
                if not decision.get('accepted'):return self.j(409,decision)
                row=store.emit('community_vote',actor=agent,actor_type=principal.kind,skill=body.get('skill',''),run_id=body.get('run_id',''),payload={'candidate':body.get('candidate'),'choice':body.get('choice'),'confidence':body.get('confidence',0),'weight':decision['weight'],'reputation':decision['reputation']},idempotency_key=key);idem.complete(key,row,'vote');return self.j(201,row)
            if path=='/api/telemetry':
                if principal.kind not in ('agent','host'):return self.j(403,{'error':'agent-or-host-required'})
                body=normalize_event(body); key=body.get('idempotency_key')
                if key:
                    claimed,existing=idem.claim(str(key),'telemetry')
                    if not claimed:return self.j(200,existing or {'deduplicated':True})
                row=store.emit(body.get('event_type','usage'),actor=body.get('agent_id','agent'),skill=body.get('skill',''),run_id=body.get('run_id',''),payload=body.get('payload',{}),actor_type=principal.kind,idempotency_key=str(key or ''))
                if key:idem.complete(str(key),row,'telemetry')
                return self.j(201,row)
            if path=='/api/reviews/decide':return self.j(200,ReviewQueue(Path(c.registry_dir)/'reviews').decide(body.get('id',''),bool(body.get('approved')),body.get('actor','human'),body.get('note','')))
            if path=='/api/skills/contribution-message':
                if principal.kind not in ('host','agent'):return self.j(403,{'error':'host-or-agent-required'})
                if principal.kind!='host' and not c.workspace_roots:return self.j(403,{'error':'agent-path-access-requires-workspace_roots'})
                skill=_safe_path(body.get('skill',''),c.workspace_roots);msg=generate_contribution_message(skill);return self.j(200,{'skill':str(skill),'message':msg,'file':write_contribution_manifest(skill) if body.get('write',True) else None})
            if path=='/api/skills/propose':
                row=propose_skill(c.registry_dir,body.get('name','Unnamed skill'),body.get('description',''),body.get('source','agent'),body.get('payload',{}));store.emit('skill_proposed',actor=body.get('source','agent'),payload=row);return self.j(201,row)
            if path=='/api/skills/review':
                from .roles import role_provider_pool
                from .skill_proposals import review_and_materialize
                out=review_and_materialize(c,body.get('proposal_id',''),c.registry_dir,role_provider_pool(c,'reviewer'),role_provider_pool(c,'judge'));store.emit('skill_proposal_reviewed',actor='reviewer',payload=out);return self.j(200,out)
            if path=='/api/methodologies':
                from .methodology import curate_observation
                from .roles import role_provider_pool
                reviewer=(role_provider_pool(c,'reviewer') or role_provider_pool(c,'improver'))[0];out=curate_observation(reviewer,body.get('observation',{}),c.registry_dir,body.get('github'));store.emit('methodology_shared',actor=body.get('agent_id','agent'),payload=out);return self.j(201,out)
            if path=='/api/autonomous/run':
                from .autonomous import AutonomousResearchLoop
                from .roles import role_provider_pool
                pools={r:role_provider_pool(c,r) for r in ('reviewer','improver')}; loop=AutonomousResearchLoop(c,pools,store); out=loop.run(_safe_path(body.get('skill',''),c.workspace_roots),body.get('suite'),body.get('loops',c.autonomous_loops),bool(body.get('auto_evolve',False))); return self.j(200,out)
            if path=='/api/judges/calibrate':
                from .roles import role_provider_pool
                from .judge import calibrate_judges
                gold=Path(c.judge_gold_suite);out=calibrate_judges(role_provider_pool(c,'judge'),json.loads(gold.read_text())['cases'],c.judge_min_calibration);store.emit('judge_calibration',actor='skIF',payload=out);return self.j(200,out)
            if path=='/api/evolve-many':
                from .evolution import EvolutionEngine
                items=[{'skill':str(_safe_path(x['skill'],c.workspace_roots)),'suite':str(_safe_path(x['suite'],c.workspace_roots)),'feedback':x.get('feedback'),'patch':x.get('patch')} for x in body.get('items',[])];out=EvolutionEngine(c,c.artifacts_dir).run_many(items,promote=bool(body.get('promote',False)));return self.j(200,{'results':out})
            if path=='/api/knowledge/mesh/node':
                mesh,_,_,_,_,_,_=_neo_services(c,store,marketplace,rep,cache)
                if principal.kind not in ('host','agent'): return self.j(403,{'error':'host-or-agent-required'})
                return self.j(201,mesh.put_node(str(body.get('id')),str(body.get('kind','artifact')),body.get('payload',{}),body.get('visibility','community'),body.get('origin',c.node_id)))
            if path=='/api/knowledge/mesh/edge':
                mesh,_,_,_,_,_,_=_neo_services(c,store,marketplace,rep,cache)
                if principal.kind not in ('host','agent'): return self.j(403,{'error':'host-or-agent-required'})
                return self.j(201,mesh.put_edge(str(body.get('src')),str(body.get('relation')),str(body.get('dst')),body.get('origin',c.node_id),body.get('confidence',1.0)))
            if path=='/api/agent/team/plan':
                from .teams import AgentTeam
                if principal.kind not in ('host','agent'): return self.j(403,{'error':'host-or-agent-required'})
                team=AgentTeam(objective=body.get('objective',''),budget=float(body.get('budget',100)));
                for m in body.get('members',[]): team.add(m.get('agent_id',''),m.get('role','worker'),m.get('weight',1),m.get('capabilities',[]))
                return self.j(200,team.assign(body.get('tasks',[]),body.get('required_capabilities',[])))
            if path=='/api/resources/admit':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                _,_,resources,_,_,_,_=_neo_services(c,store,marketplace,rep,cache); return self.j(200,resources.admit(body.get('estimate',{})))
            if path=='/api/security/fuzz':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                result=SecurityControlPlane().continuous_fuzz(body.get('seed',{}),body.get('rounds',c.security_hardening.continuous_fuzz_rounds),body.get('mutations',c.security_hardening.fuzz_mutations)); store.emit('security_fuzz',actor=principal.subject,payload=result); return self.j(200,result)
            if path=='/api/security/supply-chain':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                result=SecurityControlPlane().scan_supply_chain(body.get('manifests',[])); store.emit('security_supply_chain',actor=principal.subject,payload=result); return self.j(200,result)
            if path=='/api/security/sandbox':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                result=SecurityControlPlane().scan_sandbox_escape(body.get('commands',[])); store.emit('security_sandbox',actor=principal.subject,payload=result); return self.j(200,result)
            if path=='/api/telemetry/aggregate':
                if principal.kind not in ('host','agent'):return self.j(403,{'error':'host-or-agent-required'})
                secure=SecureTelemetry(budget=PrivacyBudget(float(body.get('privacy_budget',3.0)))); return self.j(200,{'aggregate':secure.aggregate(body.get('events',[]),float(body.get('epsilon_cost',.5))),'remaining_epsilon':secure.budget.epsilon})
            if path=='/api/telemetry/selective':
                if principal.kind not in ('host','agent'):return self.j(403,{'error':'host-or-agent-required'})
                secure=SecureTelemetry(budget=PrivacyBudget(float(body.get('privacy_budget',3.0)))); return self.j(200,{'data':secure.selective_query(body.get('payload',{}),body.get('fields',[]),float(body.get('epsilon_cost',.1))),'remaining_epsilon':secure.budget.epsilon})
            if path=='/api/governance/decision':
                if principal.kind!='host':return self.j(403,{'error':'host-principal-required'})
                _,gov,_,_,_,_,_=_neo_services(c,store,marketplace,rep,cache); return self.j(201,gov.record(body.get('decision',''),body.get('subject',''),body.get('evidence',[]),body.get('policy',{}),body.get('actors',[]),body.get('confidence',0)))
            if path=='/api/skill/lineage':
                p=_safe_path(body.get('skill',''),c.workspace_roots); return self.j(200,lineage(p))
            if path=='/api/skills/router':
                if principal.kind not in ('host','agent'):return self.j(403,{'error':'host-or-agent-required'})
                _,_,_,_,_,_,agent_os=_neo_services(c,store,marketplace,rep,cache); return self.j(200,{'skills':agent_os.recommend(body.get('task',''),body.get('environment',{}),body.get('agent_id',principal.subject))})
            if path in ('/api/feedback','/api/patch','/api/evolve'):
                from .evolution import EvolutionEngine
                if principal.kind!='host' and not c.workspace_roots:
                    return self.j(403,{'error':'agent-evolution-requires-configured-workspace_roots'})
                skill=_safe_path(body.get('skill',''),c.workspace_roots);suite=_safe_path(body.get('suite',''),c.workspace_roots);out=EvolutionEngine(c,Path(c.artifacts_dir)).run(skill,suite,feedback=body.get('feedback'),agent_patch=body.get('patch'),alternatives=body.get('alternatives'),promote=bool(body.get('promote',False)) if principal.kind=='host' else False,force_approval=bool(body.get('force',False)) if principal.kind=='host' else False,generations=body.get('generations'));store.emit('evolution_requested',actor=body.get('agent_id','agent'),skill=Path(skill).name,run_id=out.get('run_id',''),payload={'accepted':out.get('accepted')});return self.j(200,out)
            return self.j(404,{'error':'not found'})
        except Exception as exc:
            try: agent_guard.record_failure(guard_key)
            except Exception: pass
            return self.j(500,{'error':str(exc)})
    def log_message(self,*_):pass

def serve(host='127.0.0.1',port=8787):
    if host not in ('127.0.0.1','localhost','::1'):print('WARNING: protect skIF behind auth/TLS.')
    ThreadingHTTPServer((host,port),H).serve_forever()
