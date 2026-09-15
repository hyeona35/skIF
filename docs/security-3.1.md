# 3.1 Neo Security Hardening Matrix

| Surface | Primary defense | Secondary defense |
|---|---|---|
| Host console | Host token | Host-only route policy |
| Agent console | Agent token | Capability checks |
| User console | User token | Read-only API policy |
| Federation signing | Host-only endpoint | Signing key + quarantine |
| Eval corpus | Host trust boundary | Lifecycle + poisoning/leakage detection |
| Telemetry | Redaction / DP | Privacy budget / encryption |
| Runtime commands | Trusted config | External sandbox required for hostile runtimes |
| Queue | Resource limits | Recovery / idempotency |
| Marketplace | Provenance / security rating | Certification / publisher reputation |
| Knowledge Mesh | Visibility + origin | Trusted-origin import policy |
| Predictions | Feature flag | Advisory-only policy |

## Residual risk

No application-level scanner can prove that an arbitrary OS-level Agent runtime is free of sandbox escape vulnerabilities. A container/VM boundary and outbound network policy remain mandatory for hostile workloads.
