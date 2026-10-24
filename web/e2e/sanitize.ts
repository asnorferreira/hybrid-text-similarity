import { readFileSync, writeFileSync } from 'node:fs';
import { redact } from '../scripts/redact';

type Attachment = { contentType: string; path?: string; body?: Buffer };
export function sanitizeAttachments(attachments: Attachment[]) {
  let changed = 0;
  for (const attachment of attachments) {
    if (!attachment.contentType.startsWith('text/') && !attachment.contentType.includes('json')) continue;
    if (attachment.path) {
      const before = readFileSync(attachment.path, 'utf8'), after = redact(before);
      if (after !== before) { writeFileSync(attachment.path, after); changed++; }
    }
    if (attachment.body) {
      const before = attachment.body.toString('utf8'), after = redact(before);
      if (after !== before) { attachment.body = Buffer.from(after); changed++; }
    }
  }
  return changed;
}
