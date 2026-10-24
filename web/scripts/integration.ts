import assert from 'node:assert/strict';
import { readFile } from 'node:fs/promises';
import { ComparisonRepository, closeDatabase, database } from '../src/modules/comparison/infra/repository';
import { responseSchema } from '../src/modules/comparison/domain/contracts';
import { seed } from './seed';

async function main() {
  const form = new FormData();
  form.set('contract_version', '1.0');
  form.set('source', new File([await readFile('/fixtures/tipo1-perda.pdf')], 'tipo1-perda.pdf', { type: 'application/pdf' }));
  form.set('suspect', new File([await readFile('/fixtures/texto.docx')], 'texto.docx'));
  const response = await fetch('http://127.0.0.1:3000/api/comparisons', { method: 'POST', body: form });
  const value = await response.json();
  assert.equal(response.status, 200, JSON.stringify(value));
  const result = responseSchema.parse(value.result);
  assert.equal(result.state, 'calculated');
  const read = await fetch('http://127.0.0.1:3000/api/comparisons/' + value.id);
  assert.equal(read.status, 200);
  assert.deepEqual((await read.json()).result, result);
  const db = await database();
  assert.equal(await db.collection('documents').countDocuments({ comparison_id: value.id }), 2);
  assert.equal(await db.collection('comparisons').countDocuments({ key: value.id }), 1);
  assert.equal(await db.collection('reports').countDocuments({ key: value.id }), 1);
  const first = await seed(), second = await seed();
  assert.deepEqual(first, second);
  console.log(JSON.stringify({ development_only: true, flow: 'PDF + DOCX -> parsing -> Flask -> Next -> Mongo -> leitura',
    id: value.id, result, persistence: [2, 1, 1], seed_first: first, seed_second: second }, null, 2));
}
main().finally(closeDatabase);
