# @skif/sdk

Tiny zero-dependency Node.js client for agents using skIF.

```js
import { SkifClient } from '@skif/sdk';
const skif = new SkifClient({ token: process.env.SKIF_API_TOKEN });
await skif.telemetry('usage', { agent_id: 'my-agent', skill: 'demo', payload: { ok: true } });
await skif.feedback({ agent_id: 'my-agent', skill: 'demo', suite: 'evals/demo.json', feedback: { message: '...' } });
```
