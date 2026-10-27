import { MongoClient } from 'mongodb';
import { ComparisonResult, responseSchema } from '../domain/contracts';
import { CoreMeasurement, savedSchema, ViewMode } from '../domain/envelope';

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
export type SaveDetails = { viewMode: ViewMode; inputHash: string; started: number; parsingMs: number; compareMs: number; core: CoreMeasurement[] };
export class PersistenceConflict extends Error {}
export class ComparisonRepository {
  async save(id: string, owner: string, documents: DocumentInput[], result: ComparisonResult, details: SaveDetails) {
    const started = performance.now();
    const db = await database();
    for (const name of ['documents', 'comparisons', 'reports']) {
      await db.collection(name).createIndex({ key: 1 }, { unique: true });
    }
    await db.collection('comparisons').createIndex({ owner_id: 1, created_at: -1, key: -1 });
    const occupied = await db.collection('comparisons').findOne({ key: id });
    if (occupied && (occupied.owner_id !== owner || occupied.input_sha256 !== details.inputHash)) {
      throw new PersistenceConflict('identificador de requisição incompatível');
    }
    const previous = await this.read(id, owner);
    if (previous && (previous.result.metadata.config_sha256 !== result.metadata.config_sha256 ||
        previous.result.trained_models?.config_sha256 !== result.trained_models?.config_sha256 ||
        previous.result.metadata.idf.identity !== result.metadata.idf.identity ||
        previous.result.metadata.model?.identity !== result.metadata.model?.identity)) {
      throw new PersistenceConflict('identificador existente com configuração diferente; preserve e versione a requisição');
    }
    for (const doc of documents) {
      await db.collection('documents').updateOne({ key: `${id}:${doc.role}`, owner_id: owner, input_sha256: details.inputHash },
        { $setOnInsert: { key: `${id}:${doc.role}`, owner_id: owner, input_sha256: details.inputHash, comparison_id: id, ...doc } }, { upsert: true });
    }
    await db.collection('reports').updateOne({ key: id, owner_id: owner, input_sha256: details.inputHash },
      { $setOnInsert: { key: id, owner_id: owner, input_sha256: details.inputHash, result: responseSchema.parse(result) } }, { upsert: true });
    const engineering = { purpose: 'development_engineering', parsing_http_ms: details.parsingMs, compare_http_ms: details.compareMs,
      core: details.core, persistence_before_publish_ms: performance.now() - started, server_before_publish_ms: performance.now() - details.started,
      individual_algorithm_memory: 'not_measured', individual_algorithm_time: 'shared_pipeline_not_attributed' };
    await db.collection('comparisons').updateOne({ key: id, owner_id: owner, input_sha256: details.inputHash },
      { $setOnInsert: { key: id, owner_id: owner, input_sha256: details.inputHash, report_id: id, state: 'saved',
        created_at: new Date(), view_mode: details.viewMode, documents: documents.map(({ role, filename, sha256 }) => ({ role, filename, sha256 })), engineering } }, { upsert: true });
    return id;
  }
  async read(id: string, owner: string) {
    const db = await database();
    const comparison = await db.collection('comparisons').findOne({ key: id, owner_id: owner, state: 'saved' });
    if (!comparison) return null;
    const report = await db.collection('reports').findOne({ key: comparison.report_id, owner_id: owner });
    if (!report) throw new Error('relatório incompleto');
    return savedSchema.parse({ id, result: responseSchema.parse(report.result), created_at: comparison.created_at.toISOString(),
      documents: comparison.documents, view_mode: comparison.view_mode, engineering: comparison.engineering });
  }
  async list(owner: string, page: number) {
    const db = await database();
    const records = await db.collection('comparisons').find({ owner_id: owner, state: 'saved' })
      .sort({ created_at: -1, key: -1 }).skip((page - 1) * 10).limit(11).toArray();
    const values = await Promise.all(records.slice(0, 10).map(async record => {
      const saved = await this.read(record.key, owner);
      if (!saved) throw new Error('relatório incompleto');
      const index = saved.view_mode === 'semantic' ? saved.result.semantic_index : saved.result.index;
      return { id: saved.id, created_at: saved.created_at, view_mode: saved.view_mode, documents: saved.documents,
        state: saved.result.state, index: index?.value ?? null, policy: saved.result.metadata.policy };
    }));
    return { items: values, page, has_next: records.length > 10 };
  }
}
