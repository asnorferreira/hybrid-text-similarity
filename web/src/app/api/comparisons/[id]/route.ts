import { ComparisonRepository } from '../../../../modules/comparison/infra/repository';

export const runtime = 'nodejs';
export async function GET(_request: Request, context: { params: Promise<{ id: string }> }) {
  const { id } = await context.params;
  if (!/^[a-zA-Z0-9_-]{1,100}$/.test(id)) return Response.json({ detail: 'identificador inválido' }, { status: 400 });
  try {
    const value = await new ComparisonRepository().read(id);
    return value ? Response.json(value) : Response.json({ detail: 'comparação não encontrada' }, { status: 404 });
  } catch { return Response.json({ detail: 'persistência indisponível' }, { status: 503 }); }
}
