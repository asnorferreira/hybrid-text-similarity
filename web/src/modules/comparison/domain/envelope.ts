import { z } from 'zod';
import { responseSchema } from './contracts';

export const viewMode = z.enum(['hybrid', 'lexical', 'semantic', 'all']);
export type ViewMode = z.infer<typeof viewMode>;
const duration = z.number().nonnegative();
export const coreMeasurement = z.strictObject({ operation: z.enum(['extract', 'compare']),
  document_role: z.enum(['source', 'suspect']).nullable(),
  extraction: z.strictObject({ format: z.enum(['pdf', 'docx', 'txt']), cleanup_changed: z.boolean(),
    soft_hyphen_observed: z.boolean(), hyphen_linebreak_observed: z.boolean() }).nullable(),
  stages_ms: z.record(z.string(), duration), resource_state: z.string().nullable(),
  process_lifetime_peak_rss_kib: z.number().int().nonnegative().nullable() });
export type CoreMeasurement = z.infer<typeof coreMeasurement>;
export const engineeringSchema = z.strictObject({ purpose: z.literal('development_engineering'),
  parsing_http_ms: duration, compare_http_ms: duration, core: z.array(coreMeasurement),
  persistence_before_publish_ms: duration, server_before_publish_ms: duration,
  individual_algorithm_memory: z.literal('not_measured'), individual_algorithm_time: z.literal('shared_pipeline_not_attributed') });
export const savedSchema = z.strictObject({ id: z.string(), result: responseSchema, created_at: z.string(), view_mode: viewMode,
  documents: z.array(z.strictObject({ role: z.enum(['source', 'suspect']), filename: z.string(), sha256: z.string() })),
  engineering: engineeringSchema });
export type SavedComparison = z.infer<typeof savedSchema>;
