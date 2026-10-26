import { randomUUID, createHash } from 'node:crypto';
import { MongoClient } from 'mongodb';
import { expect, Page, test } from '@playwright/test';
import { register } from './helpers';

const origin = new URL(process.env.HTS_WEB_URL ?? 'http://127.0.0.1:3000').origin;
const input = () => ({ contract_version: '1.0', mode: 'lexical', request_id: randomUUID(),
  source_text: 'A pesquisa compara documentos em português.', suspect_text: 'A pesquisa compara documentos em português.' });
async function headers(page: Page) {
  const response = await page.request.get('/api/auth/session');
  expect(response.status()).toBe(200);
  const session = await response.json();
  return { origin, 'x-hts-request': '1', 'x-csrf-token': session.csrf as string };
}
async function noHistory(page: Page) {
  const response = await page.request.get('/api/comparisons');
  expect(response.status()).toBe(200);
  expect((await response.json()).items).toEqual([]);
}

test('RF-22: sem sessão não compara nem expõe resultados', async ({ page }) => {
  const response = await page.request.post('/api/comparisons', {
    headers: { origin, 'x-hts-request': '1' }, multipart: input() });
  expect(response.status()).toBe(401);
  const body = await response.json();
  expect(body.index ?? body.result).toBeUndefined();
  await page.goto('/results/' + randomUUID());
  await expect(page.getByRole('heading', { name: 'Entrar', exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Relações entre os conteúdos' })).toHaveCount(0);
});

test('RF-23: sessão realmente expirada é recusada antes da comparação', async ({ page }) => {
  await register(page);
  const authorized = await headers(page);
  const token = (await page.context().cookies()).find(c => c.name === 'hts_session')?.value;
  expect(token).toBeTruthy();
  const uri = process.env.HTS_E2E_MONGO_URI;
  const name = process.env.HTS_E2E_MONGO_DB;
  // Mutate only the temporary test session in an explicitly isolated CI DB.
  expect(uri).toBeTruthy();
  expect(name).toMatch(/^hts_ci_[a-z0-9_]+$/);
  const client = new MongoClient(uri!);
  try {
    await client.connect();
    const result = await client.db(name!).collection<{ _id: string; expires_at: Date }>('sessions').updateOne(
      { _id: createHash('sha256').update(token!).digest('hex') },
      { $set: { expires_at: new Date(0) } });
    expect(result.matchedCount).toBe(1);
  } finally { await client.close(); }
  const response = await page.request.post('/api/comparisons', { headers: authorized, multipart: input() });
  expect(response.status()).toBe(401);
  expect((await page.request.get('/api/comparisons')).status()).toBe(401);
  await page.reload();
  await expect(page.getByRole('heading', { name: 'Entrar', exact: true })).toBeVisible();
});

test('RF-24: sem CSRF não persiste nem fabrica comparação', async ({ page }) => {
  await register(page);
  await noHistory(page);
  const response = await page.request.post('/api/comparisons', {
    headers: { origin, 'x-hts-request': '1' }, multipart: input() });
  expect(response.status()).toBe(403);
  expect((await response.json()).result).toBeUndefined();
  await noHistory(page);
});

test('RF-25: B não abre nem recebe conteúdo do resultado de A', async ({ page, browser }) => {
  await register(page);
  const response = await page.request.post('/api/comparisons', { headers: await headers(page), multipart: input() });
  expect(response.status()).toBe(200);
  const saved = await response.json();
  const context = await browser.newContext({ baseURL: origin });
  try {
    const other = await context.newPage();
    await register(other);
    const denied = await other.request.get('/api/comparisons/' + saved.id);
    expect([403, 404]).toContain(denied.status());
    expect((await denied.json()).result).toBeUndefined();
    await noHistory(other);
    await other.goto('/results/' + saved.id);
    await expect(other.locator('main .error[role="alert"]')).toContainText('comparação não encontrada');
    await expect(other.getByRole('region', { name: 'Sentenças: Fonte', exact: true })).toHaveCount(0);
    await expect(other.getByText(input().source_text, { exact: true })).toHaveCount(0);
  } finally { await context.close(); }
});
