import { expect, test, Page } from '@playwright/test';
import { readFile } from 'node:fs/promises';
import { join } from 'node:path';
import { compare, register } from './helpers';

const folder=process.env.HTS_EQUIVALENCE_DIR ?? '../core/tests/fixtures/equivalence';
async function texts(page: Page, source: string, suspect: string) {
  await page.getByRole('button',{name:'Texto colado',exact:true}).click();
  await page.getByLabel('Texto fonte',{exact:true}).fill(source);
  await page.getByLabel('Texto analisado',{exact:true}).fill(suspect);
  await page.getByLabel('Método / apresentação').selectOption('hybrid');
}
async function response(page: Page) {
  const pending=page.waitForResponse(r=>r.url().endsWith('/api/comparisons')&&r.request().method()==='POST');
  await page.getByRole('button',{name:'Comparar conteúdos'}).click();
  const result=await pending;
  expect(result.status()).toBe(200);
  await expect(page.getByRole('heading',{name:'Relações entre os conteúdos'})).toBeVisible();
  return result.json();
}
test('E2E-01 formatos DOCX/PDF e TXT/TXT preservam o resultado',async ({page})=>{
  await register(page);
  const compareFiles=async (a:string,b:string)=>{
    await page.goto('/');
    await page.getByLabel('Arquivo fonte',{exact:true}).setInputFiles(join(folder,'formats','R1-source.'+a));
    await page.getByLabel('Arquivo analisado',{exact:true}).setInputFiles(join(folder,'formats','R1-suspect.'+b));
    return response(page);
  };
  const first=await compareFiles('docx','pdf'), second=await compareFiles('txt','txt');
  for (const key of ['index','matrices','matches','summary']) expect(first.result[key]).toEqual(second.result[key]);
});
for (const relation of ['R1','R2','R3','R4']) test(`E2E-02 ${relation}: classe e explicação por sentença`,async ({page})=>{
  const pairs=JSON.parse(await readFile(join(folder,'pairs.json'),'utf8')).pairs;
  const pair=pairs[relation];
  await register(page); await texts(page,pair.source,pair.suspect);
  const saved=await response(page);
  expect(saved.result.matches[0].decision.label).toBe(pair.expected_hybrid);
  const displayed: Record<string, string> = { R1: 'Cópia exata', R2: 'Cópia editada',
    R3: 'Paráfrase', R4: 'Sem correspondência detectada' };
  await expect(page.locator('.matches tbody tr').first().getByRole('cell').nth(1)).toHaveText(displayed[relation]);
  await expect(page.getByRole('heading',{name:'Par selecionado: F1 × A1'})).toBeVisible();
  await expect(page.locator('.selected-pair')).toContainText('L=');
  await expect(page.locator('.matches')).toContainText('F1 → A1');
});
for (const id of ['E2E-03','E2E-05','E2E-08']) test(`${id}: modelos, probabilidade separada e impressão`,async ({page})=>{
  await register(page);
  await texts(page,'A pesquisadora compara os documentos em português.','A pesquisadora compara os documento em português.');
  const saved=await response(page);
  expect(saved.result.trained_models.models).toHaveLength(3);
  const section=page.getByRole('region',{name:'Modelos treinados',exact:true});
  await expect(section).toBeVisible();
  await expect(section).toContainText('Probabilidade de derivação');
  await expect(section).toContainText('separadas do índice');
  for (const model of saved.result.trained_models.models) {
    await expect(section).toContainText(model.name);
    await expect(section).toContainText(model.version);
    await expect(section).toContainText(model.sha256);
  }
  if (id==='E2E-08') {
    await page.emulateMedia({media:'print'});
    await expect(section).toBeVisible();
    await expect(section).toContainText('Data desta comparação:');
    await expect(page.getByRole('button',{name:'Imprimir relatório'})).toBeHidden();
    await page.pdf({path:join(process.env.HTS_E2E_OUTPUT ?? 'artifacts/e2e','modelos-print.pdf'),format:'A4'});
  }
});
test('E2E-06 limites de texto e upload sem resultado no histórico',async ({page})=>{
  await register(page);
  await texts(page,'a'.repeat(30001),'A pesquisa compara documentos.');
  await compare(page,422);
  await expect(page.locator('main .error[role="alert"]')).toBeVisible();
  expect((await (await page.request.get('/api/comparisons')).json()).items).toEqual([]);
  await page.getByRole('button',{name:'Dois arquivos',exact:true}).click();
  await page.getByLabel('Arquivo fonte',{exact:true}).setInputFiles({name:'grande.txt',mimeType:'text/plain',buffer:Buffer.alloc(5242881,97)});
  await page.getByLabel('Arquivo analisado',{exact:true}).setInputFiles({name:'valido.txt',mimeType:'text/plain',buffer:Buffer.from('A pesquisa compara documentos.')});
  await compare(page,413);
  await expect(page.locator('main .error[role="alert"]')).toBeVisible();
  expect((await (await page.request.get('/api/comparisons')).json()).items).toEqual([]);
});
for (const text of ['هذه جملة عربية واضحة.', '这是一个清楚的句子。']) test(`E2E-07 Unicode preservado no texto e mapa: ${text}`,async ({page})=>{
  await register(page);
  await texts(page,text,text);
  const saved=await response(page);
  expect(saved.result.source.length).toBeGreaterThanOrEqual(1);
  await expect(page.getByRole('region',{name:'Sentenças: Fonte',exact:true})).toContainText(text);
  await expect(page.getByRole('button',{name:/^Selecionar F1, A1,/})).toBeVisible();
});
