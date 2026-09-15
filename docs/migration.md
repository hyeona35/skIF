# Migration to 3.1 Neo

3.1 Neo keeps compatibility with the 2.5 Rene and 3.0 Neo persistence boundary. EventStore detects legacy event tables and preserves them while creating the current versioned schema.

Before production migration:

1. Stop autonomous research and deployment.
2. Trigger the migration snapshot helper.
3. Verify EventStore and TaskQueue health.
4. Verify Host/Agent/User token configuration.
5. Run the full release test suite.

The migration module reports `3.1Neo` as the current schema and retains explicit legacy-schema metadata.
