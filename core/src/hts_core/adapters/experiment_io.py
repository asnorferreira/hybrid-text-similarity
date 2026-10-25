from dataclasses import asdict
import base64
from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter
import tracemalloc

from hts_core.adapters.dataset_store import digest, identity, read_json, read_jsonl, verify_seal
from hts_core.domain.experiments import ModelInput, dependency_components, require_split
from hts_core.adapters.contract_types import object_fields, sha256, string_list, text


from hts_core.adapters.experiment_protocol import validate_protocol


def inspect_dataset(folder, config):
    protocol_id = validate_protocol(config)
    manifest = verify_seal(folder)
    if manifest['version'] != config['dataset']['version']:
        raise ValueError('dataset difere do protocolo')
    if manifest['metadata']['purpose'] != 'frozen_operational_derivation':
        raise ValueError('finalidade de dataset incompatível')
    sources, pairs = read_jsonl(Path(folder)/'sources.jsonl'), read_jsonl(Path(folder)/'pairs.jsonl')
    groups = dependency_components(sources, pairs)
    return {'protocol_identity': protocol_id, 'manifest': manifest, 'sources': sources, 'pairs': pairs,
            'components': groups}


def annotation_examples(bundle, dataset, config, split, audit_only=False):
    validate_protocol(config)
    if type(audit_only) is not bool:
        raise ValueError('audit_only deve ser booleano')
    if audit_only:
        if split not in ('train', 'validation', 'test'):
            raise ValueError('split de auditoria inválido')
    else:
        require_split(split)
    object_fields(bundle, {'schema', 'dataset_version', 'task', 'unit', 'rubric_id', 'origin', 'procedure_id',
                          'generator_relationship', 'shared_dependencies', 'records'}, 'annotations')
    task = bundle['task']
    for field in ('schema', 'dataset_version', 'task', 'unit', 'rubric_id', 'origin', 'procedure_id', 'generator_relationship'):
        text(bundle[field], 'annotations.'+field)
    sha256(bundle['dataset_version'], 'annotations.dataset_version')
    if bundle['schema'] not in ('hts-annotations-1', 'hts-annotations-2') or task not in ('H1', 'H2') or bundle['unit'] != 'sentence_pair':
        raise ValueError('tarefa/unidade de anotação incompatível')
    if bundle['schema'] == 'hts-annotations-2' and task != 'H2':
        raise ValueError('annotations-2: eixos semânticos exigem tarefa H2')
    if bundle['dataset_version'] != dataset['manifest']['version'] or bundle['unit'] != config['tasks'][task]['unit']:
        raise ValueError('versão/unidade da anotação diverge do contrato')
    if bundle['origin'] not in ('human_independent', 'automated_weak', 'generator_dependent', 'artificial_fixture'):
        raise ValueError('origem de anotação inválida')
    if bundle['generator_relationship'] not in ('independent_declared', 'shared', 'same_generator', 'artificial_fixture'):
        raise ValueError('dependência da anotação ausente')
    relationships = {'human_independent': {'independent_declared'},
                     'automated_weak': {'independent_declared', 'shared'},
                     'generator_dependent': {'same_generator'}, 'artificial_fixture': {'artificial_fixture'}}
    if bundle['generator_relationship'] not in relationships[bundle['origin']]:
        raise ValueError('independência contraditória')
    string_list(bundle['shared_dependencies'], 'annotations.shared_dependencies', empty=True)
    if type(bundle['records']) is not list:
        raise ValueError('annotations.records: lista exigida')
    pairs = {p['id']: p for p in dataset['pairs']}
    sources = {s['id']: s for s in dataset['sources']}
    seen, outputs, counts = set(), [], {'labeled': 0, 'ambiguous': 0, 'excluded': 0, 'other_split': 0}
    text_pairs, selected_text_pairs = {}, set()
    by_split = {s: {'labeled': 0, 'ambiguous': 0, 'excluded': 0} for s in ('train', 'validation', 'test')}
    for row in bundle['records']:
        required = {'pair_id', 'source_id', 'source_sentence_id', 'suspect_sentence_id', 'source_text_sha256',
                    'suspect_text_sha256', 'status', 'target', 'reason', 'evidence_ref'}
        if bundle['schema'] == 'hts-annotations-2':
            required.add('semantic_axes')
        object_fields(row, required, 'annotation.record')
        for field in required-{'target', 'semantic_axes'}:
            text(row[field], 'annotation.'+field)
        for field in ('source_text_sha256', 'suspect_text_sha256'):
            sha256(row[field], 'annotation.'+field)
        key = tuple(row[k] for k in ('pair_id', 'source_id', 'source_sentence_id', 'suspect_sentence_id'))
        if key in seen:
            raise ValueError('anotação duplicada')
        seen.add(key)
        pair = pairs.get(row['pair_id'])
        source = sources.get(row['source_id'])
        if pair is None or source is None or row['source_id'] not in pair['source_ids'] or source['split'] != pair['split']:
            raise ValueError('IDs/ancestralidade/split de anotação inválidos')
        if pair['split'] == 'test' and not audit_only:
            raise PermissionError('importação experimental de anotação test fechada na S5A')
        a = next((s for s in source['sentences'] if s['id'] == row['source_sentence_id']), None)
        b = next((s for s in pair['sentences'] if s['id'] == row['suspect_sentence_id']), None)
        if a is None or b is None or digest(a['semantic'].encode()) != row['source_text_sha256'] or digest(b['semantic'].encode()) != row['suspect_text_sha256']:
            raise ValueError('texto/ID de sentença difere da anotação')
        if row['status'] not in counts or row['status'] == 'other_split' or not row['reason'] or not row['evidence_ref']:
            raise ValueError('decisão/motivo/evidência ausentes')
        value = row['target']
        if row['status'] != 'labeled':
            if value is not None:
                raise ValueError('ambíguo/excluído não pode ter alvo')
        elif task == 'H1':
            if value not in ('copia_exata', 'copia_editada', 'parafrase', 'sem_correspondencia_detectada'):
                raise ValueError('classe avaliativa inválida')
        else:
            if type(value) not in (int, float) or not 0 <= value <= 1:
                raise ValueError('alvo semântico deve ser finito entre zero e um')
        if bundle['schema'] == 'hts-annotations-2':
            axes = object_fields(row['semantic_axes'], {'thematic_overlap', 'propositional_relation', 'shared_content', 'context'}, 'semantic_axes')
            allowed = {'thematic_overlap': {'none', 'some', 'strong', 'uncertain'},
                       'propositional_relation': {'compatible', 'contradiction', 'unrelated', 'uncertain'},
                       'shared_content': {'none', 'partial', 'predominant', 'equivalent', 'uncertain'},
                       'context': {'sufficient', 'insufficient'}}
            for field, choices in allowed.items():
                if type(axes[field]) is not str or axes[field] not in choices:
                    raise ValueError('semantic_axes.'+field+': enum inválido')
            if axes['context'] == 'insufficient' and row['status'] == 'labeled':
                raise ValueError('contexto insuficiente exige alvo nulo/ambiguidade ou exclusão')
            if row['status'] == 'labeled' and (axes['propositional_relation'] != 'compatible' or axes['shared_content'] != 'equivalent') and value == 1:
                raise ValueError('nota 1 exige equivalência sem contradição')
            if axes['shared_content'] == 'equivalent' and axes['propositional_relation'] in ('contradiction', 'unrelated'):
                raise ValueError('eixos de equivalência contraditórios')
        counts[row['status']] += 1
        actual_split = pair['split']
        split_counts = by_split.setdefault(actual_split, {'labeled': 0, 'ambiguous': 0, 'excluded': 0})
        split_counts[row['status']] += 1
        textual_key = (row['source_text_sha256'], row['suspect_text_sha256'])
        if textual_key in text_pairs and text_pairs[textual_key] != (row['status'], value):
            raise ValueError('anotações de textos repetidos conflitantes: adjudicação explícita exigida')
        text_pairs[textual_key] = (row['status'], value)
        if pair['split'] != split:
            counts['other_split'] += 1
            continue
        if row['status'] == 'labeled':
            selected_text_pairs.add(textual_key)
            if not audit_only:
                outputs.append({'input': ModelInput(a['semantic'], b['semantic']), 'target': value,
                                'trace': {'observation': key, 'split': split, 'component': dataset['components'][pair['id']],
                                          'text_pair_identity': identity(textual_key)}})
    counts.update({'by_split': by_split, 'unique_text_pairs_all_records': len(text_pairs),
                   'repeated_text_pairs_all_records': len(bundle['records'])-len(text_pairs),
                   'unique_labeled_text_pairs_selected_split': len(selected_text_pairs),
                   'independent_observations_claimed': False})
    return outputs, counts


def save_json_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2)


def import_annotations(path, destination, dataset, config, split, audit_only=False):
    raw = Path(path).read_bytes()
    bundle = json.loads(raw)
    examples, counts = annotation_examples(bundle, dataset, config, split, audit_only=audit_only)
    if bundle['origin'] == 'artificial_fixture' and dataset['manifest']['version'] == config['dataset']['version'] and dataset['manifest']['metadata']['purpose'] == 'frozen_operational_derivation':
        raise PermissionError('anotações artificiais não podem rotular o dataset operacional')
    sources = {s['id']: s for s in dataset['sources']}
    potential = sum(len(pair['sentences']) * sum(len(sources[s]['sentences']) for s in set(pair['source_ids']))
                    for pair in dataset['pairs'] if pair['split'] == split)
    receipt = {'schema': 'hts-annotation-import-1', 'protocol_identity': validate_protocol(config),
               'annotation_identity': identity(bundle), 'dataset_version': bundle['dataset_version'],
               'task': bundle['task'], 'split': split, 'counts': counts, 'eligible': len(examples),
               'status': 'validated_not_scientifically_released', 'origin': bundle['origin'],
               'procedure_id': bundle['procedure_id'], 'rubric_id': bundle['rubric_id'],
               'generator_relationship': bundle['generator_relationship'],
               'shared_dependencies': bundle['shared_dependencies'],
               'mode': 'storage_audit_only_no_model_inputs' if audit_only else 'train_validation_selection',
               'evidence_reference_verification': 'declared_strings_not_resolved_or_content_verified',
               'original_bytes_sha256': digest(raw),
               'duplicate_text_policy': 'preserved_and_reported; not_independent; conflicts_refused; no_silent_deduplication',
               'coverage': {'labeled_sentence_pairs_selected_split': counts['by_split'][split]['labeled'],
                            'all_referenced_sentence_combinations_selected_split': potential,
                            'design': 'reported_not_claimed_exhaustive_or_probabilistic'}}
    save_json_new(destination, {'receipt': receipt, 'annotations': bundle,
                               'original_bytes_base64': base64.b64encode(raw).decode('ascii')})
    return receipt


def run_fixture(inputs, predict):
    if not inputs or any(type(row) is not ModelInput for row in inputs):
        raise ValueError('somente ModelInput, sem metadados de supervisão')
    predictions = [predict(**asdict(row)) for row in inputs]
    return predictions


def measure_fixture(operation, clock=perf_counter, rss_reader=None):
    if tracemalloc.is_tracing():
        raise RuntimeError('coletor tracemalloc já ativo; não interferir com outra medição')
    tracemalloc.start()
    try:
        start = clock()
        before_rss = rss_reader() if rss_reader is not None else None
        try:
            operation()
            status, error = 'ok', None
        except Exception as exc:
            status, error = 'error', type(exc).__name__
        elapsed = clock() - start
        after_rss = rss_reader() if rss_reader is not None else None
        from hts_core.adapters.contract_types import number
        number(elapsed, 'measurement.elapsed')
        if rss_reader is not None:
            number(before_rss, 'measurement.rss_before', integer=True)
            number(after_rss, 'measurement.rss_after', integer=True)
    finally:
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    return {'status': status, 'seconds': elapsed, 'error_type': error,
            'python_traced_current_bytes': current, 'python_traced_peak_bytes': peak,
            'rss_snapshots_bytes': [before_rss, after_rss] if rss_reader is not None else None,
            'rss_scope': 'two supplied process RSS readings; neither delta nor maximum is a measured peak; native/GPU not separated',
            'memory_scope': 'Python allocations tracked by tracemalloc; not RSS/native/GPU',
            'scope': 'software_fixture_not_H3', 'boundary': 'callable_in_process'}


def save_checkpoint(path, context, payload):
    validate_context(context)
    if type(payload) is not dict:
        raise ValueError('checkpoint.payload: objeto exigido')
    body = {'schema': 'hts-preparation-checkpoint-1', 'context': context, 'payload': payload}
    save_json_new(path, {**body, 'identity': identity(body)})


def load_checkpoint(path, expected_context):
    validate_context(expected_context)
    record = read_json(path)
    object_fields(record, {'schema', 'context', 'payload', 'identity'}, 'checkpoint')
    validate_context(record['context'])
    if type(record['payload']) is not dict:
        raise ValueError('checkpoint.payload: objeto exigido')
    body = {k: v for k, v in record.items() if k != 'identity'}
    if record['identity'] != identity(body) or record['schema'] != 'hts-preparation-checkpoint-1' or record['context'] != expected_context:
        raise ValueError('checkpoint adulterado ou contexto incompatível')
    return record['payload']


def validate_context(context):
    required = {'protocol_identity', 'dataset_version', 'annotation_identity', 'task', 'unit',
                'model_identity', 'config_identity', 'code_identity', 'seed', 'phase'}
    object_fields(context, required, 'context')
    if type(context['seed']) is not int or context['seed'] < 0:
        raise ValueError('contexto de retomada incompleto')
    for key, value in context.items():
        if key != 'seed':
            text(value, 'context.'+key)
    if context['phase'] not in ('preflight', 'fixture'):
        raise PermissionError('checkpoint S5A não representa pesos treinados')
    for field in ('protocol_identity', 'config_identity', 'code_identity'):
        if len(context[field]) != 64 or any(c not in '0123456789abcdef' for c in context[field]):
            raise ValueError('identidade SHA256 inválida')


def attempt_event(folder, index, context, state, details):
    validate_context(context)
    if type(index) is not int or index < 0 or state not in ('started', 'complete', 'failed'):
        raise ValueError('evento de tentativa inválido')
    if type(details) is not dict:
        raise ValueError('event.details: objeto exigido')
    path = Path(folder)/f'{index:03d}-{state}.json'
    if state != 'started':
        start = read_json(Path(folder)/f'{index:03d}-started.json')
        object_fields(start, {'context', 'state', 'details', 'utc'}, 'event.start')
        validate_context(start['context'])
        if start['state'] != 'started' or type(start['details']) is not dict:
            raise ValueError('registro inicial de tentativa inválido')
        datetime.fromisoformat(text(start['utc'], 'event.utc'))
        if start['context'] != context or any((Path(folder)/f'{index:03d}-{s}.json').exists() for s in ('complete', 'failed')):
            raise ValueError('transição de tentativa incompatível')
    elif any((Path(folder)/f'{index:03d}-{s}.json').exists() for s in ('complete', 'failed')):
        raise ValueError('tentativa encerrada')
    save_json_new(path, {'context': context, 'state': state, 'details': details,
                         'utc': datetime.now(timezone.utc).isoformat()})
