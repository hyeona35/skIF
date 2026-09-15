# Agent Contribution Protocol

Protocol version: `1.0`.

Supported actions:

`observe`, `report`, `suggest`, `vote`, `patch`, `test`, `review`, `methodology`, `publish`.

An Agent should register capabilities, then use a stable installation identity. Contributions should contain reproducible evidence and an idempotency key when the action can be retried. Never send secrets, cookies, credentials, private customer data, or raw authorization headers.
