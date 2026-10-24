import { test, expect } from '@playwright/test';
import { register, fillFiles } from './helpers';

const kind = process.env.HTS_FAILURE_KIND;
if (kind !== 'model' && kind !== 'core') throw new Error('defina HTS_FAILURE_KIND=model ou core para o cenário real preparado');
test(`indisponibilidade real: ${kind}`, async ({ page }) => {
  await register(page);
  await fillFiles(page);
  const responsePromise = page.waitForResponse(response => response.url().endsWith('/api/comparisons') && response.request().method() === 'POST');
  await page.getByRole('button', { name: 'Comparar conteúdos' }).click();
  const response = await responsePromise;
  if (kind === 'model') {
    expect(response.status()).toBe(200);
    const value = await response.json();
    expect(value.result.state).toBe('resource_unavailable');
    expect(value.result.index === null && value.result.semantic_index === null && value.result.matches === null).toBe(true);
    await expect(page.getByTestId('similarity-index')).toHaveText('Indisponível');
    await expect(page.getByText(/Recurso semântico indisponível/)).toBeVisible();
    await expect(page.getByRole('heading', { name: 'Relações entre os conteúdos' })).toBeVisible();
  } else {
    expect(response.status()).toBe(503);
    await expect(page.locator('main .error[role="alert"]')).toContainText('core indisponível');
    await expect(page.getByRole('heading', { name: 'Relações entre os conteúdos' })).toHaveCount(0);
  }
});
