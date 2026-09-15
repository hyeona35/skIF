# Security / Red-Team Lab

3.1 Neo treats the security lab as a control-plane subsystem, not as a general-purpose shell runner.

It covers:

- autonomous adversarial Agents
- continuous fuzzing
- Judge / evaluator manipulation simulation
- federation poisoning and trust-policy attacks
- vote manipulation / Sybil signals
- dependency and supply-chain inspection
- sandbox escape pattern detection
- telemetry / resource-exhaustion abuse
- rollback / deployment abuse

Findings are recorded in the EventStore and can be used by promotion, certification, review and federation policies. Untrusted runtime code must still execute inside a separate OS-level sandbox/container/VM.
