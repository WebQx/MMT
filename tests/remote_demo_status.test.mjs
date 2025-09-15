// Simple integration probe for remote backend /demo/status.
// Usage: REMOTE_API_BASE_URL=https://mmt-prod.up.railway.app node tests/remote_demo_status.test.mjs
// Exits non-zero on failure.

import { setTimeout as delay } from 'node:timers/promises';

const base = process.env.REMOTE_API_BASE_URL;
if (!base) {
  console.error('REMOTE_API_BASE_URL env not set');
  process.exit(2);
}

const url = `${base.replace(/\/$/, '')}/demo/status`;

async function main() {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 8000);
  try {
    const res = await fetch(url, { signal: controller.signal });
    if (!res.ok) {
      console.error('Non-200 status', res.status, res.statusText);
      process.exit(1);
    }
    const body = await res.json();
    if (typeof body.demo_mode !== 'boolean') {
      console.error('Response missing demo_mode boolean', body);
      process.exit(1);
    }
    console.log('OK /demo/status', JSON.stringify(body));
  } catch (e) {
    console.error('Request failed', e.message);
    process.exit(1);
  } finally {
    clearTimeout(timeout);
  }
}

main();
