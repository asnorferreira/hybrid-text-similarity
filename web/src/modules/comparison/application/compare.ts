import { createHash, randomUUID } from 'node:crypto';
import { CoreClient, FlowError } from '../infra/core-client';
import { ComparisonRepository, DocumentInput } from '../infra/repository';
import { requestSchema } from '../domain/contracts';

export class CompareFiles {
  constructor(private core = new CoreClient(), private repository = new ComparisonRepository()) {}
  async run(source: File, suspect: File, mode: 'hybrid' | 'lexical' = 'hybrid', id: string = randomUUID()) {
    for (const file of [source, suspect]) {
      if (file.size > 5242880 || !file.name || file.name.length > 255) throw new FlowError('invalid_input', 'limite de arquivo/nome excedido', 413);
    }
    const texts = await Promise.all([this.core.extract(source), this.core.extract(suspect)]);
    const result = await this.core.compare(requestSchema.parse({ contract_version: '1.0', source: { text: texts[0] }, suspect: { text: texts[1] }, mode }));
    const docs: DocumentInput[] = await Promise.all([source, suspect].map(async (file, i) => ({ role: i === 0 ? 'source' as const : 'suspect' as const,
      filename: file.name, text: texts[i], sha256: createHash('sha256').update(Buffer.from(await file.arrayBuffer())).digest('hex') })));
    try { await this.repository.save(id, docs, result); }
    catch { throw new FlowError('resource_unavailable', 'persistência indisponível; registros parciais podem existir', 503); }
    return { id, result };
  }
}
