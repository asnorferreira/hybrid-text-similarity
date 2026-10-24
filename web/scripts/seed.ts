import { createHash } from 'node:crypto';
import { CompareFiles } from '../src/modules/comparison/application/compare';
import { closeDatabase, database } from '../src/modules/comparison/infra/repository';

export async function seed() {
  const source = new File(['A pesquisa compara conteúdos de dois arquivos. O método requer revisão.'], 'fonte-desenvolvimento.txt');
  const suspect = new File(['A pesquisa compara conteúdos de dois arquivos. Outra sentença descreve o experimento.'], 'suspeito-desenvolvimento.txt');
  const id = 'dev-s2-' + createHash('sha256').update('q5-v2-seed-20261024-v1').digest('hex').slice(0, 20);
  await new CompareFiles().run(source, suspect, 'hybrid', id);
  const db = await database();
  const counts = await Promise.all(['documents', 'comparisons', 'reports'].map(async collection => ({ collection,
    count: await db.collection(collection).countDocuments(collection === 'documents' ? { comparison_id: id } : { key: id }) })));
  if (JSON.stringify(counts.map(item => item.count)) !== '[2,1,1]') throw new Error('seed não idempotente');
  return { id, counts, development_only: true };
}
if (process.argv[1]?.endsWith('seed.ts')) {
  seed().then(value => console.log(JSON.stringify(value))).finally(closeDatabase);
}
