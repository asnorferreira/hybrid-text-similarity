import { MongoClient } from 'mongodb';
import { ComparisonResult, responseSchema } from '../domain/contracts';

let client: MongoClient | undefined;
export async function database() {
  const uri = process.env.MONGO_URI;
  if (!uri) throw new Error('banco não configurado');
  const name = process.env.MONGO_DB ?? 'hts_s2_development';
  if (!/^[a-zA-Z0-9_-]+$/.test(name)) throw new Error('nome de banco inválido');
  client ??= new MongoClient(uri, { serverSelectionTimeoutMS: 5000 });
  await client.connect();
  return client.db(name);
}
export async function closeDatabase() { await client?.close(); client = undefined; }

export type DocumentInput = { role: 'source' | 'suspect'; filename: string; text: string; sha256: string };
export class ComparisonRepository {
  async save(id: string, documents: DocumentInput[], result: ComparisonResult) {
    const db = await database();
    for (const name of ['documents', 'comparisons', 'reports']) {
      await db.collection(name).createIndex({ key: 1 }, { unique: true });
    }
    const previous = await this.read(id);
    if (previous && (previous.result.metadata.config_sha256 !== result.metadata.config_sha256 ||
        previous.result.metadata.idf.identity !== result.metadata.idf.identity ||
        previous.result.metadata.model?.identity !== result.metadata.model?.identity)) {
      throw new Error('seed/identificador existente com configuração diferente; preserve e versione o seed');
    }
    for (const doc of documents) {
      await db.collection('documents').updateOne({ key: `${id}:${doc.role}` }, { $setOnInsert: { key: `${id}:${doc.role}`, comparison_id: id, ...doc } }, { upsert: true });
    }
    await db.collection('reports').updateOne({ key: id }, { $setOnInsert: { key: id, result: responseSchema.parse(result), development: true } }, { upsert: true });
    await db.collection('comparisons').updateOne({ key: id }, { $setOnInsert: { key: id, report_id: id, state: 'saved', development: true } }, { upsert: true });
    return id;
  }
  async read(id: string) {
    const db = await database();
    const comparison = await db.collection('comparisons').findOne({ key: id });
    if (!comparison) return null;
    const report = await db.collection('reports').findOne({ key: comparison.report_id });
    if (!report) throw new Error('relatório incompleto');
    return { id, result: responseSchema.parse(report.result) };
  }
}
