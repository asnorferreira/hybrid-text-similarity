import assert from 'node:assert/strict';
import test from 'node:test';
import { AdmissionError, AdmissionQueue } from '../src/modules/comparison/infra/admission';

const reason = (value: string) => (error: unknown) => error instanceof AdmissionError && error.reason === value;

test('admission bounds active work and queue, preserves FIFO, release is idempotent', async () => {
  const queue = new AdmissionQueue(2, 2);
  const releaseA = await queue.acquire(), releaseB = await queue.acquire();
  const order: string[] = [];
  const c = queue.acquire().then(release => { order.push('c'); return release; });
  const d = queue.acquire().then(release => { order.push('d'); return release; });
  await assert.rejects(queue.acquire(), reason('capacity'));
  assert.deepEqual(order, []);
  releaseA(); releaseA();
  const releaseC = await c;
  assert.deepEqual(order, ['c']);
  releaseB();
  const releaseD = await d;
  assert.deepEqual(order, ['c', 'd']);
  releaseC(); releaseD();
  const next = await queue.acquire(); next();
});

test('cancelled waiter leaves room for next user and never takes a slot', async () => {
  const queue = new AdmissionQueue(1, 1);
  const release = await queue.acquire();
  const controller = new AbortController();
  const cancelled = assert.rejects(queue.acquire(controller.signal), reason('aborted'));
  controller.abort();
  await cancelled;
  const next = queue.acquire();
  release();
  (await next)();
  await assert.rejects(queue.acquire(controller.signal), reason('aborted'));
  (await queue.acquire())();
});

test('expired waiter leaves queue and later work can run', async () => {
  const queue = new AdmissionQueue(1, 1, 15);
  const release = await queue.acquire();
  await assert.rejects(queue.acquire(), reason('timeout'));
  const next = queue.acquire();
  release();
  (await next)();
});

test('deadline is enforced even when timer delivery is late; next eligible user proceeds', async () => {
  let now = 0;
  const queue = new AdmissionQueue(1, 2, 30_000, () => now);
  const release = await queue.acquire();
  const expired = assert.rejects(queue.acquire(), reason('timeout'));
  now = 30_001;
  const next = queue.acquire();
  release();
  await expired;
  (await next)();
  (await queue.acquire())();
});

test('failed work releases capacity in finally; abort after grant cannot overbook', async () => {
  const queue = new AdmissionQueue(1, 1);
  const first = await queue.acquire();
  const controller = new AbortController();
  const next = queue.acquire(controller.signal);
  first(); controller.abort();
  const release = await next;
  const last = queue.acquire();
  await assert.rejects(queue.acquire(), reason('capacity'));
  try { throw new Error('comparison failed'); }
  catch { /* The route returns the mapped error. */ }
  finally { release(); }
  (await last)();
});
