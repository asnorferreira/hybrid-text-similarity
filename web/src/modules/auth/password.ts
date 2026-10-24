import { randomBytes, scrypt, timingSafeEqual } from 'node:crypto';

const parameters = { N: 32768, r: 8, p: 3, maxmem: 64 * 1024 * 1024 };
function derive(password: string, salt: string): Promise<Buffer> {
  return new Promise((resolve, reject) => scrypt(password, salt, 64, parameters,
    (error, key) => error ? reject(error) : resolve(key)));
}
export async function hashPassword(password: string) {
  const salt = randomBytes(32).toString('base64url');
  return ['scrypt', parameters.N, parameters.r, parameters.p, salt, (await derive(password, salt)).toString('base64url')].join('$');
}
export async function verifyPassword(password: string, encoded: string) {
  const [algorithm, n, r, p, salt, hash, extra] = encoded.split('$');
  if (algorithm !== 'scrypt' || n !== '32768' || r !== '8' || p !== '3' || extra ||
      !/^[A-Za-z0-9_-]{43}$/.test(salt ?? '') || !/^[A-Za-z0-9_-]{86}$/.test(hash ?? '')) return false;
  return timingSafeEqual(await derive(password, salt), Buffer.from(hash, 'base64url'));
}
