import { ZodError } from 'zod';
import { CompareFiles } from '../../../modules/comparison/application/compare';
import { FlowError } from '../../../modules/comparison/infra/core-client';

export const runtime = 'nodejs';
export async function POST(request: Request) {
  try {
    if (Number(request.headers.get('content-length') ?? 0) > 10551296) throw new FlowError('invalid_input', 'limite de upload excedido', 413);
    const form = await request.formData();
    const allowed = ['source', 'suspect', 'contract_version', 'mode'];
    if ([...form.keys()].some(k => !allowed.includes(k)) || form.get('contract_version') !== '1.0') throw new FlowError('invalid_input', 'contrato incompatível');
    const source = form.get('source'), suspect = form.get('suspect'), mode = form.get('mode') ?? 'hybrid';
    if (!(source instanceof File) || !(suspect instanceof File) || !['hybrid', 'lexical'].includes(String(mode))) throw new FlowError('invalid_input', 'envie dois arquivos e modo válido');
    return Response.json(await new CompareFiles().run(source, suspect, mode as 'hybrid' | 'lexical'));
  } catch (error) {
    if (error instanceof FlowError) return Response.json({ contract_version: '1.0', state: error.state, detail: error.message }, { status: error.status });
    return Response.json({ contract_version: '1.0', state: 'invalid_input', detail: error instanceof ZodError ? 'contrato inválido' : 'requisição não processada' }, { status: 400 });
  }
}
