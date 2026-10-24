import assert from 'node:assert/strict';
import test from 'node:test';
import { hashPassword, verifyPassword } from '../src/modules/auth/password';
import { appOrigin, assertOrigin, boundedBody, credentials, HttpError, sessionCookie } from '../src/modules/auth/server';
import { format } from '../src/components/format';
import { redact } from '../scripts/redact';
import { newRequestId, uuidFromBytes } from '../src/components/request-id';
import { sanitizeAttachments } from '../e2e/sanitize';
import { mkdtempSync, readFileSync, writeFileSync, unlinkSync, rmdirSync } from 'node:fs';
import { join } from 'node:path';
import { tmpdir } from 'node:os';

test('password hashing uses real scrypt, fresh salt and exact password without truncation', async () => {
  const password = 'Palavra pública de teste 123';
  const first = await hashPassword(password), second = await hashPassword(password);
  assert.ok(first !== second);
  assert.ok(first.startsWith('scrypt$32768$8$3$'));
  assert.ok(await verifyPassword(password, first));
  assert.ok(!await verifyPassword(password + 'x', first));
  assert.ok(!await verifyPassword('inválida', first));
  assert.ok(!await verifyPassword(password, 'registro inválido'));
  assert.ok(!credentials.safeParse({ email: 'a@exemplo.org', password: 'x'.repeat(129) }).success);
  assert.ok(!credentials.safeParse({ email: 'a@exemplo.org', password, owner_id: 'outro' }).success);
});
test('origin validation is exact and independent of supplied Host or forwarding headers', () => {
  const origin = appOrigin();
  assert.doesNotThrow(() => assertOrigin(new Request(origin, { headers: { origin, 'x-hts-request': '1' } })));
  const variants: Record<string, string>[] = [{ origin: 'https://outro.invalid', 'x-hts-request': '1' }, { origin },
    { origin, 'x-hts-request': '1', 'sec-fetch-site': 'cross-site' }];
  for (const headers of variants) {
    assert.throws(() => assertOrigin(new Request(origin, { headers })), HttpError);
  }
});
test('body limit counts actual streamed bytes even without Content-Length', async () => {
  await assert.rejects(boundedBody(new Request('http://localhost', { method: 'POST', body: '12345' }), 4), HttpError);
  assert.equal((await boundedBody(new Request('http://localhost', { method: 'POST', body: '1234' }), 4)).toString(), '1234');
});
test('presentation uses decimal half-up and preserves negative raw semantic values', () => {
  assert.equal(format(1.005), '1,01');
  assert.equal(format(.615), '0,62');
  assert.equal(format(-.125), '-0,13');
});
test('technical reporter removes test passwords, session cookies and CSRF without deleting status', () => {
  const raw = 'failed S3TEST-example_value cookie hts_session=' + 'A'.repeat(43) + ' x-csrf-token: ' + 'B'.repeat(43);
  const safe = redact(raw);
  assert.ok(safe.includes('failed') && !safe.includes('example_value') && !safe.includes('A'.repeat(43)) && !safe.includes('B'.repeat(43)));
});
test('HTTPS cookie is Secure and HTTP development exception remains loopback only', () => {
  const previous = process.env.HTS_APP_ORIGIN;
  try {
    process.env.HTS_APP_ORIGIN = 'https://localhost';
    const flags = sessionCookie('A'.repeat(43)).split(';').map(part => part.trim());
    assert.ok(flags.includes('Secure') && flags.includes('HttpOnly') && flags.includes('SameSite=Strict'));
    process.env.HTS_APP_ORIGIN = 'http://external.invalid';
    assert.throws(appOrigin);
  } finally { if (previous === undefined) delete process.env.HTS_APP_ORIGIN; else process.env.HTS_APP_ORIGIN = previous; }
});
test('request UUID uses Web Crypto random bytes and version/variant formatting without requiring randomUUID', () => {
  assert.equal(uuidFromBytes(new Uint8Array(16)), '00000000-0000-4000-8000-000000000000');
  const first = newRequestId(), second = newRequestId();
  assert.match(first, /^[0-9a-f]{8}-[0-9a-f]{4}-4[0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$/);
  assert.ok(first !== second);
});

test('automatic browser text attachments are redacted on disk and in memory, preserving diagnostic context', () => {
  const directory = mkdtempSync(join(tmpdir(), 'hts-redaction-'));
  const path = join(directory, 'error-context.md');
  try {
    const password = 'S3TEST-' + 'X'.repeat(32);
    writeFileSync(path, '# Context\n- textbox Senha: ' + password + '\n- heading: Criar conta');
    const body = { contentType: 'application/json', body: Buffer.from('{"csrf":"' + 'Y'.repeat(43) + '"}') };
    const binary = { contentType: 'image/png', body: Buffer.from([0, 1, 2]) };
    assert.equal(sanitizeAttachments([{ contentType: 'text/markdown', path }, body, binary]), 2);
    assert.equal(readFileSync(path, 'utf8'), '# Context\n- textbox Senha: [TEST PASSWORD REDACTED]\n- heading: Criar conta');
    assert.equal(body.body.toString(), '{"csrf":"[REDACTED]"}');
    assert.deepEqual(binary.body, Buffer.from([0, 1, 2]));
  } finally { unlinkSync(path); rmdirSync(directory); }
});
