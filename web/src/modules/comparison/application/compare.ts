import { createHash, randomUUID } from 'node:crypto';
import { CoreClient, FlowError } from '../infra/core-client';
import { ComparisonRepository, DocumentInput } from '../infra/repository';
import { requestSchema } from '../domain/contracts';
import { ViewMode } from '../domain/envelope';
import { PersistenceConflict } from '../infra/repository';

export class CompareFiles {
  constructor(private owner: string, private core = new CoreClient(), private repository = new ComparisonRepository()) {
    if (!owner) throw new Error('proprietário obrigatório');
  }
  async run(source: File, suspect: File, mode: ViewMode = 'hybrid', id: string = randomUUID()) {
    const started = performance.now();
    for (const file of [source, suspect]) {
      if (file.size > 5242880 || !file.name || file.name.length > 255 || /[\x00-\x1f/\\]/.test(file.name)) throw new FlowError('invalid_input', 'limite ou nome de arquivo inválido', 413);
    }
    const parsingStart = performance.now();
    const texts = await Promise.all([this.core.extract(source, 'source'), this.core.extract(suspect, 'suspect')]);
    const parsingMs = performance.now() - parsingStart;
    const comparisonStart = performance.now();
    const result = await this.core.compare(requestSchema.parse({ contract_version: '1.0', source: { text: texts[0] }, suspect: { text: texts[1] }, mode: mode === 'lexical' ? 'lexical' : 'hybrid' }));
    const compareMs = performance.now() - comparisonStart;
    const docs: DocumentInput[] = await Promise.all([source, suspect].map(async (file, i) => ({ role: i === 0 ? 'source' as const : 'suspect' as const,
      filename: file.name, text: texts[i], sha256: createHash('sha256').update(Buffer.from(await file.arrayBuffer())).digest('hex') })));
    const inputHash = createHash('sha256').update(JSON.stringify({ mode, files: docs.map(({ role, filename, sha256 }) => ({ role, filename, sha256 })) })).digest('hex');
    try {
      await this.repository.save(id, this.owner, docs, result, { viewMode: mode, inputHash, started, parsingMs, compareMs, core: this.core.measurements() });
      const stored = await this.repository.read(id, this.owner);
      if (!stored) throw new Error('comparação incompleta');
      return stored;
    } catch (error) {
      if (error instanceof PersistenceConflict) throw new FlowError('invalid_input', error.message, 409);
      throw new FlowError('resource_unavailable', 'persistência indisponível; registros parciais podem existir', 503);
    }
  }
}
