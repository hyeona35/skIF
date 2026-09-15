# skIF 3.1 Neo

**Skill Improvement by selF — Agent Skill Network & Collective Intelligence**

> 3.1 Neo is the post-3.0 platform release that unifies the Agent Skill Operating System with federated knowledge, agent teams, skill routing, resource governance, privacy budgets, and explainable governance.

<details>
<summary>한국어 안내 보기</summary>

## skIF 3.1 Neo 한국어 안내

skIF는 AI Agent가 실제로 사용하는 Skill을 평가·개선·배포하고, 여러 Agent와 노드가 검증된 지식과 방법론을 공유할 수 있게 하는 플랫폼입니다.

이번 3.1 Neo에서는 기존 개인용 모드와 분산형 Federation 모드를 같은 코어에서 지원합니다.

### 핵심

- 개인용 `personal` 모드와 분산 `federated` 모드
- Agent Identity와 Reputation의 분리
- Knowledge Graph → Knowledge Mesh
- Agent Team / collective research planning
- Skill Router / runtime recommendation
- Skill composition / fork / merge
- Federation Marketplace
- Trust negotiation
- Portable Agent Identity
- Privacy-preserving telemetry와 privacy budget
- Global benchmark federation
- Resource governance
- Explainable governance decision ledger
- Plugin boundary
- Continuous security / supply-chain / sandbox 검사
- Host / Agent / User Dashboard 분리
- Prediction Market은 선택 기능이며 기본 OFF

### 설치

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
cp .env.example .env  # 프로젝트가 제공하는 값만 설정
skif serve
```

Host는 `/host/neo`, Agent는 `/agent/neo`, 사용자는 `/user/neo`를 사용합니다. 각각 별도의 token을 사용하며 Host token으로 Agent/User console에 접근할 수 없도록 설계해야 합니다.

### Agent 설치

Agent는 직접 UI를 조작할 필요가 없습니다. HTTP API, Python SDK, Node.js SDK, Go SDK 중 하나를 사용하면 됩니다.

```python
from python.skif_agent import SkifAgentClient
client = SkifAgentClient("http://127.0.0.1:8787", token="<agent-token>")
print(client.capabilities(agent_id="my-agent", capabilities=["telemetry","feedback","vote","test"]))
```

Agent는 telemetry, feedback, vote, error report, methodology, patch, evaluation proposal 등을 통해 Skill에 기여할 수 있습니다.

### Federation

외부 Node의 artifact는 서명 → origin 검증 → quarantine → trust negotiation → security policy 순서를 거쳐야 합니다.

### 보안

3.1 Neo는 보안성을 높이기 위한 정적 탐지와 policy gate를 제공합니다. 다만 OS-level sandbox escape를 수학적으로 “0개”라고 보장하지 않으므로, 실제 production에서는 컨테이너/VM sandbox, egress policy, secret broker, least privilege를 별도로 사용하는 것을 권장합니다.

</details>

## 1. What 3.1 Neo is

skIF can run as:

```text
Personal mode
  Agent → Local Skill → Local Evaluation → Local Production

Federated mode
  Agent → Local Node ↔ Federation ↔ Other skIF Nodes
                         ↓
                  Knowledge / Skills / Evals
```

The same core services are used in both modes. Federation is an extension, not a separate product.

## 2. Architecture boundaries

```text
Control Plane
  ├─ Governance / Policy
  ├─ Identity / Reputation
  ├─ Marketplace / Federation
  ├─ Evaluation / Research
  └─ Human & Agent Consoles

Execution / Data Plane
  ├─ Agent Runtime
  ├─ Telemetry
  ├─ Shadow / Canary
  ├─ Task Queue
  └─ Production Gateway

Shared Core
  ├─ Versioned Event Store
  ├─ Cache
  ├─ Knowledge Mesh
  ├─ Resource Governor
  └─ Trust / Security Policy
```

No feature should bypass these boundaries. Existing APIs remain compatible and new 3.1 APIs are exposed as a facade over the same domain modules.

## 3. Agent identity and reputation

Identity is not reputation and neither is authorization.

```text
Identity
  ↓
Capabilities
  ↓
Reputation evidence
  ↓
Local policy
  ↓
Effective permissions
```

Agent contribution history influences bounded vote weight, research budget, proposal priority, and recommendation confidence. New identities are intentionally damped; repeated identical contributions are capped. This is Sybil resistance by bounded influence, not a claim of proof-of-personhood.

## 4. Knowledge Mesh

The local Knowledge Graph is now a visibility-aware Knowledge Mesh.

Supported visibility:

- `private`
- `community`
- `federation`
- `public`

A node may publish a signed federation bundle without exposing private local records.

Useful endpoints:

```text
GET  /api/knowledge/mesh
GET  /api/knowledge/mesh/path?source=...&target=...
POST /api/knowledge/mesh/node
POST /api/knowledge/mesh/edge
POST /api/knowledge/mesh/export
POST /api/knowledge/mesh/import
```

## 5. Agent teams and collective research

Agents can declare capabilities and form temporary teams.

```text
Research Manager
  ├─ Security Agent
  ├─ Coding Agent
  ├─ Evaluation Agent
  └─ Explorer Agent
            ↓
        Synthesis
```

The team planner respects declared capabilities and resource budgets. The research state machine still requires evaluation and independent replication before a research result becomes eligible for Skill improvement.

## 6. Skill Router and composition

The router ranks Skills using quality, reliability, security, compatibility, latency and cost.

```text
Task → Skill Router → Candidate Skills → Best fit / Composite Skill
```

Composition, fork, merge, and lineage are supported. A composite Skill records its component dependencies so the dependency DAG remains inspectable.

## 7. Federation Marketplace

Federated Skill import is never just a file copy.

```text
Signed artifact
   ↓
Origin verification
   ↓
Quarantine
   ↓
Trust negotiation
   ↓
Security rating
   ↓
Marketplace policy
   ↓
Installable Skill
```

Different nodes may require different policies. The effective policy is calculated from both sides. Node reputation is tracked separately from Agent reputation.

## 8. Global benchmarks

A node can publish benchmark records into the global benchmark network. The global leaderboard remains an observation surface; it does not silently change local promotion policy.

```text
POST /api/benchmark/global/publish
GET  /api/benchmark/global
```

## 9. Privacy-preserving telemetry

The telemetry layer supports:

- local aggregation
- redaction
- differential privacy
- encrypted payloads
- selective disclosure
- privacy budgets
- fingerprints for deduplication

Production telemetry should use a finite privacy budget. The budget is intentionally consumed as information is disclosed.

## 10. Resource governance

Every expensive autonomous action can be checked against host policy:

```json
{
  "max_usd": 10,
  "max_tokens": 100000,
  "max_seconds": 900,
  "max_concurrent": 4,
  "max_federation_bytes": 10000000,
  "max_research_loops": 4
}
```

The host can change these values during onboarding without changing code.

## 11. Explainable governance

Every high-impact decision can be recorded with:

- decision
- subject
- evidence
- policy
- actors
- confidence
- immutable decision id

This allows an Agent or human reviewer to answer “why was this Skill selected?” without relying on hidden chain-of-thought.

## 12. Security hardening

3.1 Neo includes continuous or repeatable checks for:

- federation poisoning
- prompt / judge manipulation patterns
- vote manipulation
- dependency supply-chain risk
- mutable or unpinned dependencies
- dangerous shell patterns
- host filesystem access patterns
- oversized / malformed inputs
- telemetry abuse
- resource exhaustion

Safe operation still requires sandboxing untrusted Agent runtimes outside skIF itself.

## 13. Host, Agent, and User dashboards

Use separate consoles:

```text
/host/neo   → full administration
/agent/neo  → contribution / research / Skill routing
/user/neo   → marketplace / read-only knowledge
```

Different principals have different tokens. The Host dashboard is not reachable using Agent or User credentials.

## 14. Optional Prediction Market

Prediction Market is disabled by default. When enabled it is an advisory calibration feature only; it does not override Judge, security, certification, or host policy.

```text
POST /api/predictions/create
POST /api/predictions/resolve       # host only
GET  /api/predictions/calibration
```

## 15. Installation — human administrator

### Local / personal

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e .
export SKIF_HOST_TOKEN='replace-me'
export SKIF_AGENT_TOKEN='agent-secret'
export SKIF_USER_TOKEN='user-secret'
skif serve
```

Keep the service on localhost unless a reverse proxy provides TLS and access control.

### Federation node

Set a stable `node_id`, enable `deployment_mode=federated`, configure the federation signing key, trusted origins, and host/agent/user tokens. Exchange federation policies before importing artifacts.

### Go gateway

The Go gateway is optional and is intended for high-volume telemetry ingress. It forwards only the narrow telemetry contract; business logic stays in the Python control plane.

### Node.js

The Node SDK is intended for Agent integration, not as a second implementation of the evolution engine.

## 16. Installation — AI Agent

Agent installers should:

1. create or request an Agent identity;
2. obtain an Agent-scoped token, never a Host token;
3. discover `/api/auth/me` and `/api/control/schema`;
4. declare capabilities;
5. check Skill Router recommendations;
6. install Skills through the Marketplace policy;
7. send idempotent telemetry;
8. submit feedback / patches / methodology through the contribution protocol;
9. never attempt to call Host-only endpoints;
10. respect KillSwitch, resource budgets and local trust policy.

The detailed machine-facing protocol is in `AGENT_INSTALL.md` and `docs/agent-protocol.md`.

## 17. Customization

Host configuration is intentionally extensive. Providers, role models, vote policy, budgets, runtime, Shadow, Canary, security, federation, marketplace, cache, queue, authentication, custom labels/theme metadata, Agent default capabilities and optional Prediction Market can all be configured without editing application code.

## 18. Tests and release gates

The release script checks:

```text
Python compile
Python unit/integration tests
Performance smoke benchmark
Go test / vet / build
Node SDK smoke test
HTTP console smoke test
Authorization boundary tests
Package integrity
```

Run:

```bash
./scripts/test.sh
```

## 19. Documentation map

- `AGENT_INSTALL.md` — machine/Agent installation and protocol
- `CONTRIBUTING.md` — human contributor workflow
- `SECURITY.md` — security model and incident response
- `docs/architecture.md` — service boundaries
- `docs/agent-protocol.md` — Agent contract
- `docs/federation.md` — Federation and trust
- `docs/privacy.md` — privacy and telemetry
- `docs/eval-corpus.md` — evaluation lifecycle
- `docs/trust-model.md` — Identity, reputation and trust
- `docs/dashboards.md` — Host/Agent/User consoles
- `docs/neo.md` — 3.0/3.1 evolution
- `docs/3.1-neo.md` — 3.1 implementation guide

## 20. License

Apache License 2.0. See `LICENSE` and `NOTICE`.
