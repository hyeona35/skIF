# skIF 3.1 Neo Security Policy

skIF is an automation control plane. Treat Host credentials, federation keys and deployment configuration as privileged secrets.

## Security boundaries

- Host, Agent and User tokens are distinct.
- Host dashboard endpoints are Host-only.
- Agent dashboard cannot grant Host capabilities.
- Portable identity does not imply authorization.
- Federation artifacts enter quarantine before trust.
- Evaluation corpora are protected from the Skill under test.
- Prediction Market is advisory only and disabled by default.

## Defense layers

1. Input size limits
2. Rate limits and failure guards
3. Idempotency
4. Resource budgets
5. KillSwitch
6. Authentication and authorization
7. Provenance / signature verification
8. Security scans
9. Audit events
10. Deployment / promotion gates

## Untrusted Agent Runtime

Model-generated shell commands or tool trajectories must not be treated as trusted code. Use a dedicated sandbox, container or VM when running untrusted runtimes.

## Secrets

Do not place provider keys, federation private keys, cookies, access tokens or customer data in Skills, evals, methodologies, telemetry or commits.

## Vulnerability handling

Security fixes should include a regression test and a documented threat model. Do not publish exploit details that make active exploitation easier; disclose affected versions and mitigation clearly.
