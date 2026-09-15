import { SkifClient } from '../../node/skif-sdk/index.js';

const skif = new SkifClient({ token: process.env.SKIF_API_TOKEN });
await skif.telemetry('usage', { agent_id: 'example-agent', skill: 'demo', payload: { outcome: 'success' } });
await skif.feedback({
  agent_id: 'example-agent',
  skill: './examples/demo_skill',
  suite: './evals/demo.json',
  feedback: { message: 'The skill should clarify missing parameters before acting.' }
});
