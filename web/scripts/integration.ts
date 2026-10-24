import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { ComparisonRepository, closeDatabase, database } from '../src/modules/comparison/infra/repository';
import { responseSchema } from '../src/modules/comparison/domain/contracts';
import { seed } from './seed';

async function main() {
  const fixtureDir = process.env.HTS_FIXTURE_DIR ?? '/fixtures';
  const webUrl = process.env.HTS_WEB_URL ?? 'http://127.0.0.1:3000';
  const form = new FormData();
  form.set('contract_version', '1.0');
  form.set('source', new File([await readFile(join(fixtureDir, 'tipo1-perda.pdf'))], 'tipo1-perda.pdf', { type: 'application/pdf' }));
  form.set('suspect', new File([await readFile(join(fixtureDir, 'texto.docx'))], 'texto.docx'));
  const response = await fetch(webUrl + '/api/comparisons', { method: 'POST', body: form });
  const value = await response.json();
  assert.equal(response.status, 200, JSON.stringify(value));
  const result = responseSchema.parse(value.result);
  assert.equal(result.state, 'calculated');
  if (process.env.HTS_FIXTURE_MANIFEST) {
    const expected = JSON.parse(await readFile(process.env.HTS_FIXTURE_MANIFEST, 'utf8'));
    assert.equal(expected.development_only, true);
    assert.deepEqual(result.source.map(s => s.raw), expected.source);
    assert.deepEqual(result.suspect.map(s => s.raw), expected.suspect);
  }
  const read = await fetch(webUrl + '/api/comparisons/' + value.id);
  assert.equal(read.status, 200);
  assert.deepEqual((await read.json()).result, result);
  const db = await database();
  assert.equal(await db.collection('documents').countDocuments({ comparison_id: value.id }), 2);
  assert.equal(await db.collection('comparisons').countDocuments({ key: value.id }), 1);
  assert.equal(await db.collection('reports').countDocuments({ key: value.id }), 1);
  const first = await seed(), second = await seed();
  assert.deepEqual(first, second);
  const output = { development_only: true, flow: 'PDF + DOCX -> parsing -> Flask -> Next -> Mongo -> leitura',
    id: value.id, persistence: [2, 1, 1], seed_first: first, seed_second: second };
  console.log(JSON.stringify(process.env.HTS_INTEGRATION_SUMMARY === '1' ? { ...output, state: result.state,
    contract: result.contract_version, policy: result.metadata.policy, model_revision: result.metadata.model?.revision } : { ...output, result }, null, 2));
}
main().finally(closeDatabase);
