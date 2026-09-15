# Event Schema

Every new core event carries `event_id`, `ts`, `schema_version`, `event_type`, `actor_type`, `source`, `skill`, `run_id`, `correlation_id`, `idempotency_key`, `payload`, and optional `signature`.

Unknown extension event types remain valid for forward compatibility; the envelope itself is versioned. Consumers must ignore fields they do not understand.

Idempotency is enforced at the persistence boundary for events that carry an idempotency key.
