import type { FullResult, Reporter, TestCase, TestResult, TestStep } from '@playwright/test/reporter';
import { mkdirSync, writeFileSync } from 'node:fs';
import { join } from 'node:path';
import { redact } from '../scripts/redact';
import { sanitizeAttachments } from './sanitize';

const xml = (text: string) => redact(text).replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');
export default class SafeReporter implements Reporter {
  private cases: string[] = [];
  private failures = 0;
  private skipped = 0;
  onStepBegin(test: TestCase, result: TestResult, step: TestStep) {
    if (step.category === 'test.step') console.log('stage: ' + redact(step.title));
  }
  onStepEnd(test: TestCase, result: TestResult, step: TestStep) {
    if (step.category === 'test.step') console.log(`stage end: ${redact(step.title)}; ${step.duration} ms; ${step.error ? 'failed' : 'completed'}`);
  }
  onTestEnd(test: TestCase, result: TestResult) {
    const sanitized = sanitizeAttachments(result.attachments);
    if (sanitized) console.log(`Sanitized ${sanitized} text attachments before retaining test evidence.`);
    const error = result.status === 'passed' ? '' : result.status === 'skipped' ? '<skipped/>' :
      `<failure message="${xml(result.error?.message ?? result.status)}">${xml(result.error?.stack ?? result.error?.message ?? result.status)}</failure>`;
    if (result.status === 'skipped') this.skipped++;
    else if (result.status !== 'passed') this.failures++;
    this.cases.push(`<testcase name="${xml(test.titlePath().join(' / '))}" time="${result.duration / 1000}">${error}</testcase>`);
    console.log(`${result.status}: ${test.title}`);
    if (error && result.error) console.log(redact(result.error.message ?? 'erro sem detalhe'));
  }
  onEnd(result: FullResult) {
    const folder = process.env.HTS_E2E_OUTPUT ?? 'artifacts/e2e';
    mkdirSync(folder, { recursive: true });
    writeFileSync(join(folder, `${process.env.HTS_E2E_REPORT ?? 'system'}.xml`),
      `<?xml version="1.0" encoding="UTF-8"?><testsuites><testsuite tests="${this.cases.length}" failures="${this.failures}" skipped="${this.skipped}">${this.cases.join('')}</testsuite></testsuites>`);
    console.log(`E2E ${result.status}: ${this.cases.length} casos; ${this.failures} falhas; ${this.skipped} skips. Sem traces/cookies/credenciais nos artifacts.`);
  }
}
