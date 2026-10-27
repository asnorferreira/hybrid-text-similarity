import { z } from 'zod';

export const version = z.literal('1.0');
export const requestSchema = z.strictObject({
  contract_version: version,
  source: z.strictObject({ text: z.string().min(1) }),
  suspect: z.strictObject({ text: z.string().min(1) }),
  mode: z.enum(['hybrid', 'lexical']).default('hybrid'),
});
export type CompareRequest = z.infer<typeof requestSchema>;
const score = z.number().min(0).max(1);
const index = z.strictObject({ source_to_suspect: score, suspect_to_source: score, value: z.number().min(0).max(100) });
const jsonRecord = z.record(z.string(), z.json());
const sentence = z.strictObject({ index: z.number().int().nonnegative(), raw: z.string(), semantic: z.string(),
  lexical: z.array(z.string()), words: z.number().int().nonnegative(), flags: z.array(z.string()), window: jsonRecord.nullable() });
const labels = z.enum(['copia_exata', 'copia_editada', 'parafrase', 'sem_correspondencia_detectada']);
const matrix = (entry: z.ZodNumber) => z.array(z.array(entry));
const sha256 = z.string().regex(/^[0-9a-f]{64}$/);
export const responseSchema = z.strictObject({
  trained_models: z.strictObject({ state: z.literal('calculated'), config_sha256: sha256,
    scope: z.literal('best_q5v2_pairs_exploratory_not_document_index'),
    models: z.array(z.strictObject({ name: z.string(), version: z.string(), sha256 })),
    pairs: z.array(z.strictObject({ source: z.number().int().nonnegative(), suspect: z.number().int().nonnegative(),
      h1_label: labels, h2_score: score, derivation_probability: score })) }).nullable().optional(),
  contract_version: version, state: z.enum(['calculated', 'resource_unavailable']), method: z.enum(['hybrid', 'lexical']),
  index: index.nullable(), lexical_index: index, semantic_index: index.nullable(),
  matrices: z.strictObject({ lexical: matrix(score), semantic_raw: matrix(z.number().min(-1).max(1)).nullable(),
    semantic_operational: matrix(score).nullable(), fused: matrix(score).nullable() }),
  source: z.array(sentence), suspect: z.array(sentence),
  matches: z.array(z.strictObject({ source: z.number().int(), suspect: z.number().int(), lexical: score,
    semantic_raw: z.number().min(-1).max(1), semantic_operational: score, fused: score, edit: score,
    characters: z.record(z.string(), z.number()), decision: z.strictObject({ label: labels, reason: z.string(), lexical_high: z.boolean() }) })).nullable(),
  alignment: z.strictObject({ pairs: z.array(z.strictObject({ source: z.number().int().nonnegative(), suspect: z.number().int().nonnegative(), score })),
    unmatched_source: z.array(z.number().int()), unmatched_suspect: z.array(z.number().int()), objective: z.number().nonnegative() }).nullable(),
  summary: z.strictObject({ counts: z.record(z.string(), z.number().int()), proportions: z.record(z.string(), z.number()),
    denominator: z.number().int().positive(), predominance: z.string(), inserted_segment: z.literal('indisponivel_regra_nao_definida') }).nullable(),
  metadata: z.strictObject({ policy: z.literal('q5-v2'), config_sha256: z.string(), configuration: jsonRecord, idf: jsonRecord,
    model: jsonRecord.nullable(), semantic_unavailable: z.string().nullable(), unavailable_components: z.array(z.string()), signature: jsonRecord }),
});
export type ComparisonResult = z.infer<typeof responseSchema>;
export const errorSchema = z.strictObject({ contract_version: version,
  state: z.enum(['invalid_input', 'unsupported_format', 'extraction_failed', 'no_useful_content', 'resource_unavailable']), detail: z.string() });
export const extractionSchema = z.strictObject({ contract_version: version, text: z.string() });
