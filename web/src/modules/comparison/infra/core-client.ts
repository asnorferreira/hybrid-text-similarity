import { CompareRequest, errorSchema, extractionSchema, requestSchema, responseSchema } from '../domain/contracts';

export class FlowError extends Error {
  constructor(public state: string, message: string, public status = 400) { super(message); }
}

export class CoreClient {
  constructor(private base = process.env.CORE_URL ?? 'http://127.0.0.1:5000', private transport: typeof fetch = fetch) {}

  private async call(path: string, init: RequestInit) {
    let response: Response;
    try { response = await this.transport(this.base + path, { ...init, signal: AbortSignal.timeout(180000) }); }
    catch { throw new FlowError('resource_unavailable', 'core indisponível ou prazo de resposta excedido', 503); }
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

  async extract(file: File) {
    const form = new FormData();
    form.set('contract_version', '1.0'); form.set('file', file);
    const parsed = extractionSchema.safeParse(await this.call('/v1/extract', { method: 'POST', body: form }));
    if (!parsed.success) throw new FlowError('resource_unavailable', 'extração do core incompatível com o contrato', 502);
    return parsed.data.text;
  }
}
