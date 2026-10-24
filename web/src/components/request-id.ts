export function uuidFromBytes(input: Uint8Array) {
  if (input.length !== 16) throw new Error('UUID requer 16 bytes');
  const bytes = new Uint8Array(input);
  bytes[6] = (bytes[6] & 15) | 64;
  bytes[8] = (bytes[8] & 63) | 128;
  const hex = [...bytes].map(value => value.toString(16).padStart(2, '0')).join('');
  return `${hex.slice(0, 8)}-${hex.slice(8, 12)}-${hex.slice(12, 16)}-${hex.slice(16, 20)}-${hex.slice(20)}`;
}
export function newRequestId() { return uuidFromBytes(crypto.getRandomValues(new Uint8Array(16))); }
