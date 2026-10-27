import { ZodError } from 'zod';
import { CompareFiles } from '../../../modules/comparison/application/compare';
import { FlowError } from '../../../modules/comparison/infra/core-client';
import { authenticate, boundedBody, failure, HttpError, json, rateLimit } from '../../../modules/auth/server';
import { viewMode } from '../../../modules/comparison/domain/envelope';
import { ComparisonRepository } from '../../../modules/comparison/infra/repository';
import { AdmissionError, AdmissionQueue } from '../../../modules/comparison/infra/admission';

export const runtime = 'nodejs';
const admission = new AdmissionQueue();
export async function POST(request: Request) {
  let release: (() => void) | undefined;
  try {
    const identity = await authenticate(request, true);
    await rateLimit('compare:' + identity.user.id, 10);
    try { release = await admission.acquire(request.signal); }
    catch (error) {
      if (error instanceof AdmissionError) throw new HttpError(error.reason === 'aborted' ? 408 : 429,
        error.reason === 'aborted' ? 'requisição cancelada' : 'fila de comparações no limite; tente novamente');
      throw error;
    }
    const body = await boundedBody(request, 10551296);
    let form: FormData;
    try { form = await new Request(request.url, { method: 'POST', headers: { 'content-type': request.headers.get('content-type') ?? '' }, body: new Uint8Array(body).buffer }).formData(); }
    catch { throw new HttpError(400, 'formulário inválido'); }
    const allowed = ['source', 'suspect', 'source_text', 'suspect_text', 'contract_version', 'mode', 'request_id'];
    if ([...form.keys()].some(k => !allowed.includes(k) || form.getAll(k).length !== 1) || form.get('contract_version') !== '1.0') throw new HttpError(400, 'contrato incompatível');
    const mode = viewMode.safeParse(form.get('mode') ?? 'hybrid');
    const id = form.get('request_id');
    if (!mode.success || (id !== null && (typeof id !== 'string' || !/^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/i.test(id)))) throw new HttpError(400, 'modo ou identificador inválido');
    let source = form.get('source'), suspect = form.get('suspect');
    const sourceText = form.get('source_text'), suspectText = form.get('suspect_text');
    if (sourceText !== null || suspectText !== null) {
      if (source !== null || suspect !== null || typeof sourceText !== 'string' || typeof suspectText !== 'string') throw new HttpError(400, 'escolha dois arquivos ou dois textos');
      source = new File([sourceText], 'fonte-colada.txt', { type: 'text/plain' });
      suspect = new File([suspectText], 'analisado-colado.txt', { type: 'text/plain' });
    }
    if (!(source instanceof File) || !(suspect instanceof File)) throw new HttpError(400, 'envie dois arquivos ou dois textos');
    return json(await new CompareFiles(identity.user.id).run(source, suspect, mode.data, typeof id === 'string' ? id : undefined));
  } catch (error) {
    if (error instanceof FlowError) return json({ contract_version: '1.0', state: error.state, detail: error.message }, error.status);
    if (error instanceof ZodError) return json({ detail: 'contrato inválido' }, 400);
    return failure(error);
  } finally { release?.(); }
}
export async function GET(request: Request) {
  try {
    const identity = await authenticate(request);
    await rateLimit('read:' + identity.user.id, 120);
    const query = new URL(request.url).searchParams;
    const page = query.get('page') ?? '1';
    if ([...query.keys()].some(key => key !== 'page') || query.getAll('page').length > 1 || !/^[1-9]\d{0,3}$/.test(page)) throw new HttpError(400, 'página inválida');
    return json(await new ComparisonRepository().list(identity.user.id, Number(page)));
  } catch (error) { return failure(error); }
}
