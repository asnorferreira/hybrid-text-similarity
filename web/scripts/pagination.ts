import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { createTestUser } from './test-client';
import { closeDatabase, database } from '../src/modules/comparison/infra/repository';

async function main() {
  const user = await createTestUser();
  const form = new FormData();
  form.set('contract_version', '1.0'); form.set('mode', 'lexical');
  form.set('source_text', 'Uma pesquisa compara conteúdos.'); form.set('suspect_text', 'Uma pesquisa compara conteúdos.');
  const response = await user.request('/api/comparisons', { method: 'POST', body: form });
  assert.equal(response.status, 200);
  const saved = await response.json();
  const db = await database();
  const comparison = await db.collection('comparisons').findOne({ key: saved.id, owner_id: user.owner });
  const report = await db.collection('reports').findOne({ key: saved.id, owner_id: user.owner });
  const documents = await db.collection('documents').find({ comparison_id: saved.id, owner_id: user.owner }).toArray();
  assert.ok(comparison && report && documents.length === 2);
  const copy = (record: Record<string, unknown>) => Object.fromEntries(Object.entries(record).filter(([key]) => key !== '_id'));
  const provenance = 'pagination fixture copied from executed comparison; not a new inference';
  for (let i = 0; i < 11; i++) {
    const id = 'pagination-' + randomUUID();
    await db.collection('documents').insertMany(documents.map(doc => ({ ...copy(doc), key: `${id}:${doc.role}`, comparison_id: id, provenance })));
    await db.collection('reports').insertOne({ ...copy(report), key: id, provenance });
    await db.collection('comparisons').insertOne({ ...copy(comparison), key: id, report_id: id, created_at: new Date('2023-01-01T00:00:00Z'), provenance });
  }
  const pages = [];
  for (const page of [1, 2, 3]) {
    const response = await user.request('/api/comparisons?page=' + page);
    assert.equal(response.status, 200); pages.push(await response.json());
  }
  assert.deepEqual(pages.map(page => page.items.length), [10, 2, 0]);
  assert.deepEqual(pages.map(page => page.has_next), [true, false, false]);
  const items = pages.flatMap(page => page.items);
  assert.equal(new Set(items.map(item => item.id)).size, 12);
  for (let i = 1; i < items.length; i++) {
    const previous = items[i - 1], next = items[i];
    assert.ok(previous.created_at > next.created_at || previous.created_at === next.created_at && previous.id > next.id);
  }
  const other = await createTestUser();
  assert.equal((await (await other.request('/api/comparisons')).json()).items.length, 0);
  console.log(JSON.stringify({ development_only: true, fixture: provenance, pages: [10, 2, 0], deterministic_order_and_isolation: true }));
}
main().finally(closeDatabase);
