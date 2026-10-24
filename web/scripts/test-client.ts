import { randomBytes, randomUUID } from 'node:crypto';

export function testBase() {
  const url = new URL(process.env.HTS_WEB_URL ?? 'http://127.0.0.1:3000');
  if (!['127.0.0.1', 'localhost', 'web'].includes(url.hostname)) throw new Error('teste somente na aplicação local/interna');
  return url.origin;
}
export async function createTestUser() {
  if (process.env.MONGO_DB !== 'hts_ci_s3') throw new Error('teste somente no namespace CI S3');
  const base = testBase(), origin = process.env.HTS_APP_ORIGIN ?? base;
  const response = await fetch(base + '/api/auth/register', { method: 'POST', headers: {
    origin, 'x-hts-request': '1', 'content-type': 'application/json' },
    body: JSON.stringify({ email: `dev-${randomUUID()}@example.test`, password: randomBytes(24).toString('base64url') }) });
  if (response.status !== 201) throw new Error('cadastro de desenvolvimento não concluído');
  const value = await response.json();
  const cookie = response.headers.get('set-cookie')?.split(';')[0];
  if (!cookie || !value.csrf || !value.user?.id) throw new Error('sessão de desenvolvimento não criada');
  const request = (path: string, init: RequestInit = {}) => {
    const headers = new Headers({ cookie, origin, 'x-hts-request': '1', 'x-csrf-token': value.csrf });
    new Headers(init.headers).forEach((item, key) => headers.set(key, item));
    return fetch(base + path, { ...init, headers });
  };
  return { owner: value.user.id as string, request, cookie };
}
