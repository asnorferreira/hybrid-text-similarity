import assert from 'node:assert/strict';
import { randomUUID } from 'node:crypto';
import { createTestUser, testBase } from './test-client';
import { closeDatabase, database } from '../src/modules/comparison/infra/repository';
import { digest } from '../src/modules/auth/server';
import { CoreClient, FlowError } from '../src/modules/comparison/infra/core-client';

async function main() {
  const checks: string[] = [];
  const a = await createTestUser(), b = await createTestUser();
  const origin = process.env.HTS_APP_ORIGIN ?? testBase();
  const form = (id = randomUUID(), extra?: [string, string]) => {
    const value = new FormData();
    value.set('contract_version', '1.0'); value.set('mode', 'lexical'); value.set('request_id', id);
    value.set('source_text', 'A pesquisa compara conteúdos.'); value.set('suspect_text', 'A pesquisa compara conteúdos.');
    if (extra) value.set(...extra);
    return value;
  };
  assert.equal((await fetch(testBase() + '/api/comparisons')).status, 401);
  assert.equal((await fetch(testBase() + '/api/comparisons', { method: 'POST', headers: { origin, 'x-hts-request': '1' }, body: form() })).status, 401);
  checks.push('sem sessão não lê nem compara');
  const invalidHeaders: Record<string, string>[] = [{ origin: 'https://outro.invalid' }, { 'x-csrf-token': '' }];
  for (const headers of invalidHeaders) {
    assert.equal((await a.request('/api/comparisons', { method: 'POST', headers, body: form() })).status, 403);
  }
  checks.push('origem e CSRF recusados independentemente');
  const id = randomUUID();
  assert.equal((await a.request('/api/comparisons', { method: 'POST', body: form(id) })).status, 200);
  assert.equal((await a.request('/api/comparisons', { method: 'POST', body: form(id) })).status, 200);
  assert.equal((await b.request('/api/comparisons/' + id)).status, 404);
  assert.equal((await (await b.request('/api/comparisons')).json()).items.length, 0);
  checks.push('idempotência real e B sem acesso por ID/lista');
  const changed = form(id); changed.set('suspect_text', 'Outro conteúdo diferente.');
  assert.equal((await a.request('/api/comparisons', { method: 'POST', body: changed })).status, 409);
  checks.push('mesmo ID com entrada diferente não reutiliza silenciosamente');
  for (const extra of [['owner_id', b.owner], ['r', '1'], ['origin_label', 'original']] as [string, string][]) {
    assert.equal((await a.request('/api/comparisons', { method: 'POST', body: form(randomUUID(), extra) })).status, 400);
  }
  checks.push('proprietário e gabarito do cliente recusados');
  const db = await database();
  const legacy = 'legacy-' + randomUUID();
  await db.collection('comparisons').insertOne({ key: legacy, state: 'saved', development: true, provenance: 'public S3 legacy fixture' });
  assert.equal((await a.request('/api/comparisons/' + legacy)).status, 404);
  assert.equal((await b.request('/api/comparisons/' + legacy)).status, 404);
  assert.equal(await db.collection('comparisons').countDocuments({ key: legacy, owner_id: { $exists: false } }), 1);
  checks.push('legado sem proprietário preservado e oculto');
  const sessionToken = a.cookie.slice(a.cookie.indexOf('=') + 1);
  const sessions = db.collection<{ _id: string; owner_id: string; expires_at: Date }>('sessions');
  const storedSession = await sessions.findOne({ _id: digest(sessionToken) });
  assert.ok(storedSession && !JSON.stringify(storedSession).includes(sessionToken));
  const storedUser = await db.collection<{ _id: string; password_hash: string }>('users').findOne({ _id: a.owner });
  assert.ok(storedUser?.password_hash?.startsWith('scrypt$32768$8$3$') && !('password' in storedUser));
  await sessions.updateOne({ _id: digest(sessionToken) }, { $set: { expires_at: new Date(0) } });
  assert.equal((await a.request('/api/auth/session')).status, 401);
  checks.push('sessão em hash e expiração verificada sem depender do TTL');
  assert.equal((await b.request('/api/auth/logout', { method: 'POST' })).status, 200);
  assert.equal((await b.request('/api/auth/session')).status, 401);
  checks.push('logout invalida token persistido');
  const limited = await createTestUser();
  for (let i = 0; i < 10; i++) {
    assert.equal((await limited.request('/api/comparisons', { method: 'POST', body: new FormData() })).status, 400);
  }
  assert.equal((await limited.request('/api/comparisons', { method: 'POST', body: new FormData() })).status, 429);
  checks.push('limite compartilhado por usuário aplicado no servidor');
  const loginLimited = await createTestUser();
  const loginEmail = (await (await loginLimited.request('/api/auth/session')).json()).user.email;
  for (let i = 0; i < 9; i++) {
    assert.equal((await loginLimited.request('/api/auth/login', { method: 'POST', headers: { 'content-type': 'application/json' },
      body: JSON.stringify({ email: loginEmail, password: 'S3TEST-wrong-public-password' }) })).status, 401);
  }
  assert.equal((await loginLimited.request('/api/auth/login', { method: 'POST', headers: { 'content-type': 'application/json' },
    body: JSON.stringify({ email: loginEmail, password: 'S3TEST-wrong-public-password' }) })).status, 429);
  checks.push('limite de login por conta aplicado antes do scrypt');
  const size = await createTestUser();
  const oversized = form();
  oversized.delete('source_text'); oversized.delete('suspect_text');
  oversized.set('source', new File([new Uint8Array(5242881)], 'grande.txt'));
  oversized.set('suspect', new File(['Uma pesquisa válida.'], 'ok.txt'));
  assert.equal((await size.request('/api/comparisons', { method: 'POST', body: oversized })).status, 413);
  checks.push('limite de arquivo real recusado');
  await assert.rejects(new CoreClient('http://127.0.0.1:65534').extract(new File(['Teste.'], 'ok.txt')),
    (error: unknown) => error instanceof FlowError && error.status === 503);
  checks.push('core sem conexão sinaliza indisponibilidade real');
  console.log(JSON.stringify({ development_only: true, checks, count: checks.length, credentials_logged: false }));
}
main().finally(closeDatabase);
