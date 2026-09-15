# Contributing to skIF 3.1 Neo

## Principles

1. Keep control-plane policy separate from data-plane execution.
2. Do not duplicate business logic between Python, Go and Node.js.
3. Preserve existing event, API and Agent schema compatibility unless a migration is documented.
4. Every new privileged action needs an authorization decision and an audit event.
5. Every new expensive action needs a resource budget.
6. Never add raw secrets or user data to tests, methodology, telemetry fixtures, or examples.
7. New federation artifacts require provenance and trust validation.

## Areas

```text
sev/                 Python domain/control plane
node/                Agent integration SDK
go/                  high-throughput transport / gateway
schemas/             cross-language contracts
docs/                architecture + protocol
scripts/             release/test tooling
tests/               regression + security tests
```

## Agent contributors

Agents may contribute through the same protocol as humans:

- issue/report
- telemetry
- feedback
- vote
- patch
- test/eval
- methodology
- research proposal

Agent identity and contribution provenance must remain intact.

## Pull requests

Include:

- architecture impact
- security impact
- migration impact
- performance impact
- new tests
- documentation updates

Do not commit runtime databases, WAL/SHM files, cache files, credentials, provider responses containing secrets, or generated production traffic.

## Definition of done

A change is not done until:

- tests pass;
- relevant cross-language contract still passes;
- authorization is tested;
- idempotency is considered;
- resource limits are considered;
- docs are updated;
- migration impact is documented;
- performance regression is checked where relevant.
