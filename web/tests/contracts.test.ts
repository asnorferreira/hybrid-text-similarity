import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import test from 'node:test';
import { requestSchema, responseSchema } from '../src/modules/comparison/domain/contracts';
import { CoreClient } from '../src/modules/comparison/infra/core-client';

const fixtures = JSON.parse(readFileSync(new URL('../../contracts/requests.json', import.meta.url), 'utf8'));
test('shared request positives and negatives; no ground truth accepted', () => {
  for (const item of fixtures.valid) assert.equal(requestSchema.parse(item).contract_version, '1.0');
  for (const item of fixtures.invalid) assert.equal(requestSchema.safeParse(item).success, false);
});
test('client rejects incompatible response instead of ignoring it', async () => {
  const fake = (async () => Response.json({ contract_version: '2.0', state: 'calculated' })) as typeof fetch;
  await assert.rejects(new CoreClient('http://fake', fake).compare(fixtures.valid[0]));
  assert.equal(responseSchema.safeParse({ contract_version: '1.0' }).success, false);
});
test('shared response fixtures check missing fields, types, matrices and version', () => {
  const responses = JSON.parse(readFileSync(new URL('../../contracts/responses.json', import.meta.url), 'utf8'));
  for (const item of responses.valid) assert.equal(responseSchema.parse(item).contract_version, '1.0');
  for (const item of responses.invalid) assert.equal(responseSchema.safeParse(item).success, false);
});
test('invalid upstream JSON is technical unavailability, not negative evidence', async () => {
  const fake = (async () => new Response('bad gateway', { status: 502 })) as typeof fetch;
  await assert.rejects(new CoreClient('http://fake', fake).compare(fixtures.valid[0]),
    (error: unknown) => error instanceof Error && 'state' in error && error.state === 'resource_unavailable');
});
