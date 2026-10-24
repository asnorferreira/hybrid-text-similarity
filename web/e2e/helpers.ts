import { randomBytes, randomUUID } from 'node:crypto';
import { expect, Page } from '@playwright/test';

export async function register(page: Page) {
  const email = `browser-${randomUUID()}@example.test`, password = 'S3TEST-' + randomBytes(24).toString('base64url');
  await page.goto('/');
  await page.getByRole('button', { name: 'Criar conta', exact: true }).click();
  await page.getByLabel('E-mail', { exact: true }).fill(email);
  await page.getByLabel('Senha', { exact: true }).fill(password);
  const registered = page.waitForResponse(response => response.url().endsWith('/api/auth/register') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Cadastrar e entrar' }).click();
  expect((await registered).status()).toBe(201);
  await expect(page.getByRole('heading', { name: 'Nova comparação', exact: true })).toBeVisible();
  return { email, password };
}
export async function compare(page: Page, expectedStatus: number) {
  const response = page.waitForResponse(response => response.url().endsWith('/api/comparisons') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Comparar conteúdos' }).click();
  expect((await response).status()).toBe(expectedStatus);
}
export async function fillFiles(page: Page) {
  const folder = process.env.HTS_FIXTURE_DIR ?? '../core/artifacts/ci/fixtures';
  await page.getByLabel('Arquivo fonte', { exact: true }).setInputFiles(folder + '/tipo1-perda.pdf');
  await page.getByLabel('Arquivo analisado', { exact: true }).setInputFiles(folder + '/texto.docx');
}
