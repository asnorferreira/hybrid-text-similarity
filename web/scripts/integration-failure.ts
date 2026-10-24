import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { readFile } from 'node:fs/promises';
import { CompareFiles } from '../src/modules/comparison/application/compare';
import { FlowError } from '../src/modules/comparison/infra/core-client';
import { closeDatabase, ComparisonRepository, database } from '../src/modules/comparison/infra/repository';

async function main() {
  assert.equal(process.env.MONGO_DB, 'hts_ci_s2', 'somente namespace isolado CI');
  assert.equal(new URL(process.env.MONGO_URI ?? '').hostname, 'mongo', 'somente Mongo interno CI');
  const db = await database();
  const id = 'partial-' + randomUUID();
  const info = (await db.listCollections({ name: 'reports' }).toArray())[0];
  const previous = info && 'options' in info ? info.options?.validator ?? {} : {};
  const source = new File([await readFile('/fixtures/tipo1-perda.pdf')], 'tipo1-perda.pdf');
  const suspect = new File([await readFile('/fixtures/texto.docx')], 'texto.docx');
  await db.command({ collMod: 'reports', validator: { $and: [previous, { key: { $ne: id } }] } });
  try {
    await assert.rejects(new CompareFiles().run(source, suspect, 'hybrid', id),
      (error: unknown) => error instanceof FlowError && error.state === 'resource_unavailable' && error.status === 503);
    assert.equal(await db.collection('documents').countDocuments({ comparison_id: id }), 2);
    assert.equal(await db.collection('reports').countDocuments({ key: id }), 0);
    assert.equal(await new ComparisonRepository().read(id), null);
  } finally {
    await db.command({ collMod: 'reports', validator: previous });
  }
  await new CompareFiles().run(source, suspect, 'hybrid', id);
  assert.ok(await new ComparisonRepository().read(id));
  assert.equal(await db.collection('documents').countDocuments({ comparison_id: id }), 2);
  assert.equal(await db.collection('reports').countDocuments({ key: id }), 1);
  assert.equal(await db.collection('comparisons').countDocuments({ key: id }), 1);
  console.log(JSON.stringify({ development_only: true, fault: 'reports validator rejected only this test id',
    failure_signaled: true, partial_documents: 2, incomplete_comparison_not_exposed: true, retry_counts: [2, 1, 1], validator_restored: true }));
}
main().finally(closeDatabase);
