import { defineConfig } from '@playwright/test';

const baseURL = process.env.HTS_WEB_URL ?? 'http://127.0.0.1:3000';
if (!['127.0.0.1', 'localhost', 'web'].includes(new URL(baseURL).hostname)) throw new Error('E2E somente em aplicação local/interna');
export default defineConfig({ testDir: './e2e', workers: 1, retries: 0, timeout: 90000,
  expect: { timeout: 15000 }, outputDir: (process.env.HTS_E2E_OUTPUT ?? 'artifacts/e2e') + '/work',
  reporter: [['./e2e/reporter.ts']], use: { baseURL,
    browserName: 'chromium', trace: 'off', screenshot: 'off', video: 'off', viewport: { width: 1280, height: 900 } } });
