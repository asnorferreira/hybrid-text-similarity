import { CompareRequest, errorSchema, extractionSchema, requestSchema, responseSchema } from '../domain/contracts';
import { CoreMeasurement, coreMeasurement } from '../domain/envelope';

export class FlowError extends Error {
  constructor(public state: string, message: string, public status = 400) { super(message); }
}

export class CoreClient {
  private recorded: CoreMeasurement[] = [];
  measurements() { return this.recorded.map(value => ({ ...value, stages_ms: { ...value.stages_ms } })); }
  constructor(private base = process.env.CORE_URL ?? 'http://127.0.0.1:5000', private transport: typeof fetch = fetch) {}

  private async call(path: string, init: RequestInit, role: 'source' | 'suspect' | null = null) {
    let response: Response;
    try { response = await this.transport(this.base + path, { ...init, signal: AbortSignal.timeout(180000) }); }
    catch { throw new FlowError('resource_unavailable', 'core indisponível ou prazo de resposta excedido', 503); }
    const stages: Record<string, number> = {};
    for (const part of (response.headers.get('server-timing') ?? '').split(',')) {
      const match = part.trim().match(/^(resources|compare|enrich|parse|preprocess|lexical|embeddings|matrices|alignment|pairs);dur=(\d+(?:\.\d+)?)$/);
      if (match && Number.isFinite(Number(match[2]))) stages[match[1]] = Number(match[2]);
    }
    const rss = response.headers.get('x-hts-process-peak-rss-kib');
    let extraction = null;
    try { extraction = coreMeasurement.shape.extraction.parse(JSON.parse(response.headers.get('x-hts-extraction-notes') ?? 'null')); }
    catch { extraction = null; }
    this.recorded.push({ operation: path.endsWith('extract') ? 'extract' : 'compare', stages_ms: stages,
      document_role: role, extraction,
      resource_state: ['cached', 'cold_or_concurrent'].includes(response.headers.get('x-hts-resource-state') ?? '') ? response.headers.get('x-hts-resource-state') : null,
      process_lifetime_peak_rss_kib: rss && /^\d+$/.test(rss) && Number.isSafeInteger(Number(rss)) ? Number(rss) : null });
    let value: unknown;
    try { value = await response.json(); }
    catch { throw new FlowError('resource_unavailable', 'resposta do core sem JSON válido', 502); }
    if (!response.ok) {
      const parsed = errorSchema.safeParse(value);
      if (!parsed.success) throw new FlowError('resource_unavailable', 'erro do core incompatível com o contrato', 502);
      const error = parsed.data;
      throw new FlowError(error.state, error.detail, response.status);
    }
    return value;
  }

  async compare(input: CompareRequest) {
    const body = requestSchema.parse(input);
    const parsed = responseSchema.safeParse(await this.call('/v1/compare', { method: 'POST', headers: { 'content-type': 'application/json' }, body: JSON.stringify(body) }));
    if (!parsed.success) throw new FlowError('resource_unavailable', 'resultado do core incompatível com o contrato', 502);
    return parsed.data;
  }

  async extract(file: File, role: 'source' | 'suspect' | null = null) {
    const form = new FormData();
    form.set('contract_version', '1.0'); form.set('file', file);
    const parsed = extractionSchema.safeParse(await this.call('/v1/extract', { method: 'POST', body: form }, role));
    if (!parsed.success) throw new FlowError('resource_unavailable', 'extração do core incompatível com o contrato', 502);
    return parsed.data.text;
  }
}
