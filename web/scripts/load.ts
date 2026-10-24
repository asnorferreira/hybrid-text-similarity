import { createHash } from 'node:crypto';
import { readFile, writeFile, mkdir, appendFile } from 'node:fs/promises';
import { dirname, join } from 'node:path';
import { createTestUser, testBase } from './test-client';

async function main() {
  const folder = process.env.HTS_FIXTURE_DIR ?? '../core/artifacts/ci/fixtures';
  const output = process.env.HTS_LOAD_OUTPUT ?? 'artifacts/load.json';
  const files = await Promise.all(['tipo1-perda.pdf', 'texto.docx'].map(async filename => ({ filename, bytes: await readFile(join(folder, filename)) })));
  await mkdir(dirname(output), { recursive: true });
  const journal = output + '.partial.jsonl';
  await writeFile(journal, JSON.stringify({ purpose: 'development_engineering_not_H3', started_utc: new Date().toISOString(), endpoint: testBase() }) + '\n', { flag: 'wx' });
  const phases = [];
  for (const concurrency of [1, 2]) {
    const clients = await Promise.all(Array.from({ length: concurrency }, () => createTestUser()));
    const call = async (client: (typeof clients)[number]) => {
      const form = new FormData(); form.set('contract_version', '1.0'); form.set('mode', 'all');
      form.set('source', new File([new Uint8Array(files[0].bytes)], files[0].filename));
      form.set('suspect', new File([new Uint8Array(files[1].bytes)], files[1].filename));
      const start = performance.now();
      try {
        const response = await client.request('/api/comparisons', { method: 'POST', body: form, signal: AbortSignal.timeout(240000) });
        const value = await response.json();
        const ok = response.status === 200 && value.result?.state === 'calculated';
        return { ms: performance.now() - start, status: response.status, ok,
          model_revision: value.result?.metadata?.model?.revision ?? null, config: value.result?.metadata?.config_sha256 ?? null,
          core: value.engineering?.core ?? null };
      } catch { return { ms: performance.now() - start, status: null, ok: false, model_revision: null, config: null, core: null }; }
    };
    const warmup = await Promise.all(clients.map(client => call(client)));
    await appendFile(journal, JSON.stringify({ concurrency, warmup }) + '\n');
    const observations: Awaited<ReturnType<typeof call>>[] = [];
    const start = performance.now();
    await Promise.all(clients.map(async (client, user) => { for (let i = 0; i < 6; i++) {
      const observation = await call(client); observations.push(observation);
      await appendFile(journal, JSON.stringify({ concurrency, user, request: i, ...observation }) + '\n');
    } }));
    const duration = performance.now() - start;
    const sorted = observations.map(value => value.ms).sort((a, b) => a - b);
    const quantile = (p: number) => sorted[Math.max(0, Math.ceil(p * sorted.length) - 1)];
    phases.push({ concurrency, warmup, observations, duration_ms: duration, completed: observations.length,
      errors: observations.filter(value => !value.ok).length, requests_per_second: observations.length / (duration / 1000),
      p50_ms: quantile(.5), p95_ms: quantile(.95), p99_ms: quantile(.99), percentile_method: 'nearest-rank; ceil(p*n)-1' });
  }
  const result = { purpose: 'development_engineering_not_H3', created_utc: new Date().toISOString(), endpoint: testBase(),
    client_node: process.version, client_platform: process.platform, measured_endpoint: 'POST /api/comparisons all',
    cache: 'one real warmup per user, shared loaded model; embeddings not cached',
    files: files.map(file => ({ filename: file.filename, bytes: file.bytes.length, sha256: createHash('sha256').update(file.bytes).digest('hex') })), phases,
    limits: 'small sample; shared computer; RSS is process lifetime peak, not per algorithm; no scientific performance target' };
  await mkdir(dirname(output), { recursive: true });
  await writeFile(output, JSON.stringify(result, null, 2), { flag: 'wx' });
  console.log(JSON.stringify({ output, purpose: result.purpose, phases: phases.map(({ concurrency, completed, errors, p50_ms, p95_ms, p99_ms }) => ({ concurrency, completed, errors, p50_ms, p95_ms, p99_ms })) }));
  if (phases.some(phase => phase.errors || phase.warmup.some(value => !value.ok))) process.exitCode = 1;
}
main();
