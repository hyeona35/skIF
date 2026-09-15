# 3.1 Neo Architecture Contract

## Control plane

Policy, governance, registry, trust, evaluation, research orchestration and consoles.

## Data plane

Runtime traces, telemetry, shadow traffic, production traffic and execution jobs.

## Shared infrastructure

EventStore, TaskQueue, Knowledge Mesh, Cache, Resource Governor, Identity and provenance.

## Language boundaries

### Python

Canonical implementation for evaluation, policy, orchestration and persistence adapters.

### Go

Transport and ingress only. Go must not reimplement governance rules.

### Node.js

Agent SDK and integration only. Node must use the documented API/schema instead of maintaining a second domain model.

## Plugin boundary

Providers, runtimes, storage, federation transports and security scanners should implement stable plugin contracts instead of editing the core coordinator.

## Compatibility rule

Existing 1.x–3.0 API shapes remain accepted unless a migration explicitly says otherwise.
