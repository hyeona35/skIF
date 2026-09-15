# Privacy-preserving telemetry

Telemetry should be processed in this order:

1. redact sensitive fields locally;
2. aggregate locally when possible;
3. add differential privacy noise for population metrics;
4. encrypt the resulting payload in transit/storage;
5. use selective disclosure for remote consumers.

Do not place secrets, raw cookies, credentials, or private customer prompts into telemetry.
