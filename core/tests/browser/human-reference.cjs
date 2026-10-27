const {test} = require('node:test');
const assert = require('node:assert/strict');
const fs = require('node:fs/promises');
const {chromium} = require('/app/web/node_modules/playwright');
const base = process.env.HTS_BROWSER_FIXTURE || '/evidence/browser-fixture';
async function setup(t, engine=chromium) {
 const browser = await engine.launch({headless:true,args:engine===chromium?['--no-sandbox']:[]});
 t.after(()=>browser.close());
 const context = await browser.newContext({acceptDownloads:true});
 const page = await context.newPage();
 const errors=[],network=[];
 page.on('pageerror',e=>errors.push(String(e)));
 page.on('request',r=>{if(/^https?:/.test(r.url()))network.push(r.url());});
 await page.goto('file://'+base+'/A1.html');
 t.after(()=>{assert.deepEqual(errors,[]);assert.deepEqual(network,[]);});
 return page;
}
async function download(page, selector){const promise=page.waitForEvent('download');await page.locator(selector).click();const file=await promise;return {value:JSON.parse(await fs.readFile(await file.path(),'utf8')),name:file.suggestedFilename()};}

test('empty start, safe text, accessible navigation, no network',async t=>{
 const page=await setup(t);
 assert.equal(await page.locator('#text-a').textContent(),'Texto artificial com ação, UTF-8 e </script><img src=x onerror=alert(1)>.');
 assert.equal(await page.locator('img').count(),0);
 assert.equal(await page.locator('#H1-status').inputValue(),'');
 assert.equal(await page.locator('#human').inputValue(),'');
 assert.equal(await page.locator('#H1-target').isDisabled(),true);
 assert.match(await page.locator('#progress').textContent(),/0 de 2/);
 await page.locator('#export').click();
 assert.match(await page.locator('#notice').textContent(),/Par 1/);
 await page.locator('#next').click();assert.match(await page.locator('#pair-title').textContent(),/Par 2 de 2/);
 await page.locator('#jump').selectOption('0');assert.match(await page.locator('#pair-title').textContent(),/Par 1 de 2/);
});

test('edit, autosave, draft download, reload and explicit resume',async t=>{
 const page=await setup(t);
 await page.locator('#H1-status').selectOption('labeled');
 await page.locator('#H1-target').selectOption('parafrase');
 await page.locator('#H1-reason').fill('Justificativa artificial com ação.');
 await page.locator('#H1-quote_a').fill('Texto artificial');
 const draft=await download(page,'#draft');
 assert.equal(draft.value.complete,false);assert.equal(draft.value.completed_at,null);
 assert.equal(draft.value.records[0].H1.target,'parafrase');assert.equal(draft.value.declaration.human,null);
 await page.reload();assert.equal(await page.locator('#H1-reason').inputValue(),'Justificativa artificial com ação.');
 await page.locator('#H1-reason').fill('Outro rascunho');
 await page.locator('#resume').setInputFiles({name:'rascunho.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(draft.value))});
 await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Arquivo retomado'));
 assert.equal(await page.locator('#H1-reason').inputValue(),'Justificativa artificial com ação.');
 await page.locator('#H1-status').selectOption('ambiguous');
 assert.equal(await page.locator('#H1-target').inputValue(),'');assert.equal(await page.locator('#H1-target').isDisabled(),true);
});

test('rejects foreign packet, duplicate IDs and invalid JSON without losing state',async t=>{
 const page=await setup(t);
 for(const source of ['A2-answers-FIXTURE.json','A1-answers-FIXTURE.json']){
  const value=JSON.parse(await fs.readFile(base+'/'+source));
  if(source.startsWith('A1'))value.records[1]=value.records[0];
  await page.locator('#resume').setInputFiles({name:'invalid.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(value))});
  await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Não foi possível'));
  assert.equal(await page.locator('#H1-status').inputValue(),'');
 }
 await page.locator('#resume').setInputFiles({name:'broken.json',mimeType:'application/json',buffer:Buffer.from('{')});
 await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Não foi possível'));
});

test('quote and coherence validation, declaration gate, final export round trip',async t=>{
 const page=await setup(t);
 const value=JSON.parse(await fs.readFile(base+'/A1-answers-FIXTURE.json'));
 value.declaration.human=null;
 value.records[0].H1.quote_a='trecho inexistente';
 await page.locator('#resume').setInputFiles({name:'fixture.json',mimeType:'application/json',buffer:Buffer.from(JSON.stringify(value))});
 await page.waitForFunction(()=>document.getElementById('notice').textContent.includes('Arquivo retomado'));
 await page.locator('#export').click();assert.match(await page.locator('#notice').textContent(),/trecho de evidência/);
 await page.locator('#H1-quote_a').fill('Texto artificial');
 await page.locator('#H2-target').selectOption('1');await page.locator('#export').click();
 assert.match(await page.locator('#notice').textContent(),/nota 1 exige/);
 await page.locator('#H2-target').selectOption('0.75');await page.locator('#export').click();
 assert.match(await page.locator('#notice').textContent(),/declaração final/);
 await page.locator('#human').selectOption('true');
 const final=await download(page,'#export');
 assert.equal(final.name,'respostas-A1.json');assert.equal(final.value.complete,true);
 assert.equal(final.value.declaration.human,true);assert.equal(final.value.records.length,2);
 assert.ok(Number.isFinite(Date.parse(final.value.completed_at)));
 await fs.writeFile('/evidence/browser-final-FIXTURE.json',JSON.stringify(final.value));
 assert.match(await page.locator('#progress').textContent(),/2 de 2/);
});

test('offline workflow at narrow viewport',async t=>{
 const page=await setup(t);
 await page.setViewportSize({width:390,height:844});
 assert.ok(await page.evaluate(()=>document.documentElement.scrollWidth<=window.innerWidth));
 await page.locator('#H1-status').selectOption('ambiguous');
 await page.locator('#H1-reason').fill('Fixture de compatibilidade.');
 const draft=await download(page,'#draft');
 assert.equal(draft.value.records[0].H1.status,'ambiguous');
});
