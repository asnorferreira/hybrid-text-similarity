import { test, expect } from '@playwright/test';
import { register, fillFiles, compare } from './helpers';

const kind = process.env.HTS_FAILURE_KIND;
if (kind !== 'model' && kind !== 'core') throw new Error('defina HTS_FAILURE_KIND=model ou core para o cenário real preparado');
test(`indisponibilidade real: ${kind}`, async ({ page }) => {
  await register(page);
  await fillFiles(page);
  const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Comparar conteúdos' }).click();
  const response = await responsePromise;
  if (kind === 'model') {
    expect(response.status()).toBe(503);
    const value = await response.json();
    expect(value.state).toBe('resource_unavailable');
    expect(value.result).toBeUndefined();
    await expect(page.locator('main .error[role="alert"]')).toContainText('recurso semântico');
    await expect(page.getByRole('heading', { name: 'Relações entre os conteúdos' })).toHaveCount(0);
    expect((await (await page.request.get('/api/comparisons')).json()).items).toEqual([]);
    await page.getByLabel('Método / apresentação').selectOption('lexical');
    await compare(page, 200);
    await expect(page.getByRole('heading', { name: 'Relações entre os conteúdos' })).toBeVisible();
  } else {
    expect(response.status()).toBe(503);
    await expect(page.locator('main .error[role="alert"]')).toContainText('core indisponível');
    await expect(page.getByRole('heading', { name: 'Relações entre os conteúdos' })).toHaveCount(0);
  }
});
