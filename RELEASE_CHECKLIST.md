# skIF 3.1 Neo Release Checklist

## Verified

- [x] Python compile
- [x] 69 Python tests passed
- [x] security audit: 0 findings
- [x] performance smoke benchmark
- [x] Go test
- [x] Go vet
- [x] Go gateway build
- [x] Node SDK smoke test
- [x] Python wheel build
- [x] Host / Agent / User dashboard authorization tests
- [x] Knowledge Mesh private-visibility isolation and bundle-digest verification
- [x] Agent cannot use federation private signing endpoint
- [x] Agent cannot strengthen trusted Eval corpus
- [x] Agent cannot execute Shadow/traffic production controls
- [x] Agent evolution constrained by workspace roots
- [x] Personal and federated configuration round-trip

## Known operational requirement

The external Agent runtime is still an untrusted execution environment. Production deployments should place hostile runtimes inside a container/VM sandbox with outbound network restrictions and separate secrets.

## Prediction Market

Disabled by default. It is advisory only and never overrides Trust, Security, Judge, Marketplace, or Host policies.
