import { createHash } from 'node:crypto';
import { CompareFiles } from '../src/modules/comparison/application/compare';
import { closeDatabase, database } from '../src/modules/comparison/infra/repository';
import { appOrigin, enter } from '../src/modules/auth/server';

export async function seed(owner: string) {
  const source = new File(['A pesquisa compara conteúdos de dois arquivos. O método requer revisão.'], 'fonte-desenvolvimento.txt');
  const suspect = new File(['A pesquisa compara conteúdos de dois arquivos. Outra sentença descreve o experimento.'], 'suspeito-desenvolvimento.txt');
  const id = 'dev-s3-' + createHash('sha256').update(owner + ':q5-v2-seed-20261024-v1').digest('hex').slice(0, 20);
  await new CompareFiles(owner).run(source, suspect, 'hybrid', id);
  const db = await database();
  const counts = await Promise.all(['documents', 'comparisons', 'reports'].map(async collection => ({ collection,
    count: await db.collection(collection).countDocuments({ ...(collection === 'documents' ? { comparison_id: id } : { key: id }), owner_id: owner }) })));
  if (JSON.stringify(counts.map(item => item.count)) !== '[2,1,1]') throw new Error('seed não idempotente');
  return { id, counts, development_only: true };
}
if (process.argv[1]?.endsWith('seed.ts')) {
  const main = async () => {
    const email = process.env.HTS_SEED_EMAIL, password = process.env.HTS_SEED_PASSWORD;
    if (!email || !password) throw new Error('defina HTS_SEED_EMAIL e HTS_SEED_PASSWORD de uma conta local existente; não serão exibidos');
    const origin = appOrigin();
    const value = await enter(new Request(origin, { headers: { origin, 'x-hts-request': '1' } }), { email, password }, false);
    return seed(value.body.user.id);
  };
  main().then(value => console.log(JSON.stringify(value))).finally(closeDatabase);
}
