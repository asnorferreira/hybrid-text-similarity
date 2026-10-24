import { ComparisonRepository } from '../../../../modules/comparison/infra/repository';
import { authenticate, failure, HttpError, json, rateLimit } from '../../../../modules/auth/server';

export const runtime = 'nodejs';
export async function GET(request: Request, context: { params: Promise<{ id: string }> }) {
  try {
    const identity = await authenticate(request);
    await rateLimit('read:' + identity.user.id, 120);
    const { id } = await context.params;
    if (!/^[a-zA-Z0-9_-]{1,100}$/.test(id) || new URL(request.url).search) throw new HttpError(400, 'identificador inválido');
    const value = await new ComparisonRepository().read(id, identity.user.id);
    return value ? json(value) : json({ detail: 'comparação não encontrada' }, 404);
  } catch (error) { return failure(error); }
}
