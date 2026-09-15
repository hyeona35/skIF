# skIF 3.1 Neo Architecture

skIF 3.1 Neo is the federated Agent Skill Network / collective-intelligence platform layer. The same domain core supports both personal and federated deployments.

```text
Host Control Plane ── policy / release / quarantine / security / governance
Agent Control Plane ── contribution / research / routing / telemetry
User Portal ── browse / discover / marketplace / public knowledge
          │
          ▼
Identity + Capabilities ── Reputation ── Authorization ── Trust Negotiation
          │
          ├─ Marketplace / Registry / Certification
          ├─ Federation / Quarantine / Knowledge Mesh
          ├─ Eval Corpus / Benchmark / Research OS
          ├─ Evolution / Shadow / Canary / Production
          ├─ Security / Red Team / Supply Chain
          └─ Skill Router / Composition / Fork / Merge
          │
          ▼
EventStore + TaskQueue + Cache + Resource Governor + Privacy Layer
```

## Language boundaries

Python owns canonical policy, evaluation, orchestration and persistence adapters. Go provides optional high-volume ingress/transport. Node.js provides Agent integration and SDK surfaces. No secondary language is allowed to silently fork governance logic.

## Trust boundaries

Identity, reputation, authorization and federation trust are separate concepts. Portable credentials never grant remote administrator privileges. Federation artifacts pass provenance/signature verification and quarantine before local trust can promote them.

## Security boundary

External Agent runtimes are untrusted. skIF performs policy checks and static/adversarial analysis, but OS-level isolation must be supplied by a container, VM or equivalent sandbox in production.
