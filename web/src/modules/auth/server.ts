import { createHash, createHmac, randomBytes, randomUUID, timingSafeEqual } from 'node:crypto';
import { z } from 'zod';
import { database } from '../comparison/infra/repository';
import { hashPassword, verifyPassword } from './password';

export class HttpError extends Error {
  constructor(public status: number, message: string) { super(message); }
}
export const credentials = z.strictObject({ email: z.email().max(254).transform(s => s.toLowerCase()),
  password: z.string().min(12).max(128) });
export const cookieName = 'hts_session';
const lifetime = 8 * 60 * 60;
export const digest = (value: string) => createHash('sha256').update(value).digest('hex');
const csrfFor = (token: string) => createHmac('sha256', token).update('hts-csrf-v1').digest('base64url');
type User = { _id: string; email: string; password_hash: string; created_at: Date };
type Session = { _id: string; owner_id: string; expires_at: Date };
type Bucket = { _id: string; count: number; expires_at: Date };
export type Identity = { user: { id: string; email: string }; csrf: string; token: string };
let indexes: Promise<unknown> | undefined;
async function ready() {
  const db = await database();
  indexes ??= Promise.all([
    db.collection<User>('users').createIndex({ email: 1 }, { unique: true }),
    db.collection<Session>('sessions').createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 }),
    db.collection<Bucket>('rate_limits').createIndex({ expires_at: 1 }, { expireAfterSeconds: 0 }),
  ]).catch(error => { indexes = undefined; throw error; });
  await indexes;
  return db;
}
export function appOrigin() {
  const url = new URL(process.env.HTS_APP_ORIGIN ?? 'http://127.0.0.1:3000');
  const local = ['localhost', '127.0.0.1', '[::1]'].includes(url.hostname);
  const internalCI = process.env.HTS_HTTP_DEV === '1' && url.hostname === 'web';
  if (url.origin !== url.href.replace(/\/$/, '') || url.username || url.password ||
      !['http:', 'https:'].includes(url.protocol) || (url.protocol === 'http:' && !local && !internalCI)) {
    throw new Error('origem da aplicação inválida');
  }
  return url.origin;
}
function tokenFrom(request: Request) {
  const values = (request.headers.get('cookie') ?? '').split(';').map(s => s.trim()).filter(s => s.startsWith(cookieName + '='));
  if (values.length !== 1) return null;
  const value = values[0].slice(cookieName.length + 1);
  return /^[A-Za-z0-9_-]{43}$/.test(value) ? value : null;
}
export function assertOrigin(request: Request) {
  if (request.headers.get('origin') !== appOrigin() || request.headers.get('x-hts-request') !== '1' ||
      request.headers.get('sec-fetch-site') === 'cross-site') throw new HttpError(403, 'origem da requisição recusada');
}
export async function rateLimit(key: string, limit: number, seconds = 60) {
  const db = await ready();
  const bucket = Math.floor(Date.now() / (seconds * 1000));
  const value = await db.collection<Bucket>('rate_limits').findOneAndUpdate({ _id: `${digest(key)}:${bucket}` },
    { $inc: { count: 1 }, $setOnInsert: { expires_at: new Date((bucket + 2) * seconds * 1000) } },
    { upsert: true, returnDocument: 'after' });
  if (!value || value.count > limit) throw new HttpError(429, 'limite de requisições atingido; aguarde antes de tentar novamente');
}
export async function authenticate(request: Request, mutation = false): Promise<Identity> {
  if (mutation) assertOrigin(request);
  const token = tokenFrom(request);
  if (!token) throw new HttpError(401, 'autenticação necessária');
  const db = await ready();
  const session = await db.collection<Session>('sessions').findOne({ _id: digest(token), expires_at: { $gt: new Date() } });
  const user = session && await db.collection<User>('users').findOne({ _id: session.owner_id });
  if (!user) throw new HttpError(401, 'sessão inválida ou expirada');
  const csrf = csrfFor(token);
  if (mutation) {
    const supplied = request.headers.get('x-csrf-token') ?? '';
    if (!/^[A-Za-z0-9_-]{43}$/.test(supplied) || !timingSafeEqual(Buffer.from(csrf), Buffer.from(supplied))) {
      throw new HttpError(403, 'proteção da sessão recusou a requisição');
    }
  }
  return { user: { id: user._id, email: user.email }, csrf, token };
}
export function sessionCookie(token: string, maxAge = lifetime) {
  return `${cookieName}=${token}; Path=/; HttpOnly; SameSite=Strict; Max-Age=${maxAge}${appOrigin().startsWith('https:') ? '; Secure' : ''}`;
}
export async function enter(request: Request, body: unknown, register: boolean) {
  assertOrigin(request);
  const input = credentials.safeParse(body);
  if (!input.success) throw new HttpError(400, 'informe e-mail válido e senha de 12 a 128 caracteres, sem campos extras');
  await rateLimit('auth-global', 60, 900);
  await rateLimit('auth:' + input.data.email, 10, 900);
  const db = await ready();
  let user = await db.collection<User>('users').findOne({ email: input.data.email });
  if (register) {
    if (user) throw new HttpError(409, 'não foi possível cadastrar com esse e-mail');
    user = { _id: randomUUID(), email: input.data.email, password_hash: await hashPassword(input.data.password), created_at: new Date() };
    try { await db.collection<User>('users').insertOne(user); }
    catch (error) {
      if (error && typeof error === 'object' && 'code' in error && error.code === 11000) throw new HttpError(409, 'não foi possível cadastrar com esse e-mail');
      throw error;
    }
  } else {
    const candidate = user?.password_hash ?? await hashPassword('conta-ausente-' + randomBytes(16).toString('hex'));
    if (!await verifyPassword(input.data.password, candidate) || !user) throw new HttpError(401, 'e-mail ou senha inválidos');
  }
  const old = tokenFrom(request);
  if (old) await db.collection<Session>('sessions').deleteOne({ _id: digest(old) });
  const token = randomBytes(32).toString('base64url');
  await db.collection<Session>('sessions').insertOne({ _id: digest(token), owner_id: user._id, expires_at: new Date(Date.now() + lifetime * 1000) });
  return { body: { user: { id: user._id, email: user.email }, csrf: csrfFor(token) }, cookie: sessionCookie(token) };
}
export async function leave(request: Request) {
  const identity = await authenticate(request, true);
  await (await ready()).collection<Session>('sessions').deleteOne({ _id: digest(identity.token) });
  return sessionCookie('', 0);
}
export async function boundedBody(request: Request, limit: number) {
  const length = request.headers.get('content-length');
  if (length && (!/^\d+$/.test(length) || Number(length) > limit)) throw new HttpError(413, 'limite do corpo excedido');
  const chunks: Uint8Array[] = [];
  const reader = request.body?.getReader();
  let total = 0;
  if (reader) {
    while (true) {
      const { value, done } = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > limit) { await reader.cancel(); throw new HttpError(413, 'limite do corpo excedido'); }
      chunks.push(value);
    }
  }
  return Buffer.concat(chunks);
}
export function json(value: unknown, status = 200, headers: Record<string, string> = {}) {
  return Response.json(value, { status, headers: { 'cache-control': 'no-store', vary: 'Cookie', ...headers } });
}
export function failure(error: unknown) {
  if (error instanceof HttpError) return json({ detail: error.message }, error.status,
    error.status === 429 ? { 'retry-after': '60' } : {});
  return json({ detail: 'serviço temporariamente indisponível' }, 503);
}
