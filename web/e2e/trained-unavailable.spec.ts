import { expect, test } from '@playwright/test';
import { register, compare } from './helpers';

test('E2E-04: artefato treinado ausente com flag ativa retorna indisponibilidade explícita',async ({page})=>{
  await register(page);
  await page.getByRole('button',{name:'Texto colado',exact:true}).click();
  await page.getByLabel('Texto fonte',{exact:true}).fill('A pesquisa compara documentos em português.');
  await page.getByLabel('Texto analisado',{exact:true}).fill('A pesquisa compara documentos em português.');
  const pending=page.waitForResponse(r=>r.url().endsWith('/api/comparisons')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Comparar conteúdos'}).click();
  const response=await pending;
  expect(response.status()).toBe(503);
  expect((await response.json()).result).toBeUndefined();
  await expect(page.locator('main .error[role="alert"]')).toContainText('indisponível');
  await expect(page.getByRole('heading',{name:'Relações entre os conteúdos'})).toHaveCount(0);
  expect((await (await page.request.get('/api/comparisons')).json()).items).toEqual([]);
  await page.getByLabel('Método / apresentação').selectOption('lexical');
  await compare(page,200);
  await expect(page.getByRole('heading',{name:'Relações entre os conteúdos'})).toBeVisible();
});
