import assert from 'node:assert/strict';
import { createTestUser } from './test-client';
import { ComparisonRepository, database, closeDatabase, PersistenceConflict } from '../src/modules/comparison/infra/repository';
import { savedSchema } from '../src/modules/comparison/domain/envelope';

async function main() {
  const user=await createTestUser(), form=new FormData();
  form.set('contract_version','1.0'); form.set('mode','hybrid');
  form.set('source_text','A pesquisa compara documentos em português.');
  form.set('suspect_text','A pesquisa compara documentos em português.');
  const response=await user.request('/api/comparisons',{method:'POST',body:form});
  assert.equal(response.status,200);
  const saved=savedSchema.parse(await response.json());
  assert.equal(saved.result.trained_models?.models.length,3);
  const db=await database();
  const stored=await db.collection('comparisons').findOne({key:saved.id,owner_id:user.owner});
  assert.ok(stored);
  const documents=await db.collection('documents').find({comparison_id:saved.id,owner_id:user.owner}).toArray();
  const altered=structuredClone(saved.result);
  altered.trained_models!.config_sha256='0'.repeat(64);
  await assert.rejects(new ComparisonRepository().save(saved.id,user.owner,
    documents.map(d=>({role:d.role,filename:d.filename,text:d.text,sha256:d.sha256})),altered,
    {viewMode:'hybrid',inputHash:stored.input_sha256,started:performance.now(),parsingMs:0,compareMs:0,core:[]}),PersistenceConflict);
  assert.deepEqual((await new ComparisonRepository().read(saved.id,user.owner))?.result,saved.result);
  console.log(JSON.stringify({purpose:'development_integration',trained_models_persisted:true,config_conflict_rejected:true,previous_result_preserved:true}));
}
main().finally(closeDatabase);
