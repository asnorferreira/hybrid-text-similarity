export function redact(value: string) {
  return value.replace(/S3TEST-[A-Za-z0-9_-]+/g, '[TEST PASSWORD REDACTED]')
    .replace(/hts_session=[A-Za-z0-9_-]+/g, 'hts_session=[REDACTED]')
    .replace(/(x-csrf-token["'\s:]+)[A-Za-z0-9_-]+/gi, '$1[REDACTED]')
    .replace(/("csrf"\s*:\s*")[^"]+/g, '$1[REDACTED]')
    .replace(/\u001b\[[0-9;]*m/g, '');
}
