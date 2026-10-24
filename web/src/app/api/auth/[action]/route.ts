import { authenticate, boundedBody, enter, failure, json, leave, rateLimit, HttpError } from '../../../../modules/auth/server';

export const runtime = 'nodejs';
export async function GET(request: Request, context: { params: Promise<{ action: string }> }) {
  try {
    if ((await context.params).action !== 'session') throw new HttpError(404, 'rota não encontrada');
    const value = await authenticate(request);
    await rateLimit('session:' + value.user.id, 120);
    return json({ user: value.user, csrf: value.csrf });
  } catch (error) { return failure(error); }
}
export async function POST(request: Request, context: { params: Promise<{ action: string }> }) {
  try {
    const { action } = await context.params;
    if (action === 'logout') return json({ signed_out: true }, 200, { 'set-cookie': await leave(request) });
    if (!['login', 'register'].includes(action)) throw new HttpError(404, 'rota não encontrada');
    if (request.headers.get('content-type')?.split(';')[0].trim() !== 'application/json') throw new HttpError(415, 'envie JSON UTF-8');
    let body: unknown;
    try { body = JSON.parse(new TextDecoder('utf-8', { fatal: true }).decode(await boundedBody(request, 4096))); }
    catch (error) { if (error instanceof HttpError) throw error; throw new HttpError(400, 'JSON inválido'); }
    const result = await enter(request, body, action === 'register');
    return json(result.body, action === 'register' ? 201 : 200, { 'set-cookie': result.cookie });
  } catch (error) { return failure(error); }
}
