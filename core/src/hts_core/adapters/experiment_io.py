from dataclasses import asdict
from datetime import datetime, timezone
import json
from pathlib import Path
from time import perf_counter
import tracemalloc

from hts_core.adapters.dataset_store import digest, identity, read_json, read_jsonl, verify_seal
from hts_core.domain.experiments import ModelInput, dependency_components, require_split


def validate_protocol(config):
    required = {'schema', 'revision', 'status', 'dataset', 'hypotheses', 'tasks', 'baselines', 'seeds',
                'execution', 'h3', 'training', 'test_policy'}
    if set(config) != required or config['schema'] != 'hts-experiment-protocol-1' or config['status'] != 'candidate':
        raise ValueError('schema/estado do protocolo inválido; S5A aceita protocolo candidato')
    if type(config['revision']) is not int or config['revision'] < 1:
        raise ValueError('revisão inválida')
    if set(config['hypotheses']) != {'H1', 'H2', 'H3'} or any(not isinstance(v, str) or not v.strip() for v in config['hypotheses'].values()):
        raise ValueError('hipóteses incompletas')
    if set(config['tasks']) != {'H1', 'H2', 'H3'}:
        raise ValueError('tarefas incompletas')
    for name, task in config['tasks'].items():
        if set(task) != {'unit', 'target', 'metrics', 'blockers', 'approved_contract_id'}:
            raise ValueError('schema de tarefa inválido')
        if not task['unit'] or not task['metrics'] or not isinstance(task['blockers'], list):
            raise ValueError('unidade/métricas/impedimentos ausentes')
        if type(task['target']) is not str or not task['target'] or any(type(b) is not str or not b for b in task['blockers']):
            raise ValueError('alvo/impedimentos inválidos')
        if task['unit'] != ('request' if name == 'H3' else 'sentence_pair'):
            raise ValueError('unidade do protocolo candidato incompatível')
        if task['approved_contract_id'] is not None:
            raise PermissionError('S5A não presume aprovação científica em campo isolado')
        allowed = {'macro_f1', 'confusion_matrix'} if name == 'H1' else {'spearman', 'pearson', 'mae', 'mse', 'r2'} if name == 'H2' else {'p50', 'p95', 'failure_rate'}
        if not set(task['metrics']) <= allowed:
            raise ValueError('métrica sem implementação contratada')
    if not config['baselines'] or len({b['name'] for b in config['baselines']}) != len(config['baselines']):
        raise ValueError('baselines ausentes/duplicados')
    if not config['seeds'] or any(type(s) is not int or s < 0 for s in config['seeds']) or len(set(config['seeds'])) != len(config['seeds']):
        raise ValueError('seeds devem ser inteiros únicos não negativos')
    if config['execution'] != {'stage': 'S5A', 'modes': ['preflight', 'fixture'], 'prediction_splits': ['train', 'validation']}:
        raise PermissionError('execução fora do alcance S5A')
    if config['test_policy'] != {'performance_access': 'closed', 'release': 'requires_later_stage_and_bound_protocol_target_models_config_metrics_seeds_repetitions_authorization'}:
        raise PermissionError('proteção do teste ausente')
    training = config['training']
    if set(training) != {'architecture', 'reference_parameters', 'project_parameters', 'budget', 'selection', 'stop', 'attempts', 'status'} or training['status'] != 'blocked':
        raise ValueError('contrato de preparação de treino inválido')
    if type(training['attempts']) is not int or training['attempts'] != 1:
        raise ValueError('S5A prepara uma tentativa futura; não realiza busca')
    if training['budget'] is not None or training['selection'] is not None or training['stop'] is not None:
        raise PermissionError('orçamento/seleção/parada reais dependem de protocolo posterior')
    if set(config['dataset']) != {'version', 'idf_identity', 'idf_policy'} or any(type(v) is not str or not v for v in config['dataset'].values()):
        raise ValueError('identidades dataset/IDF ausentes')
    for key in ('version', 'idf_identity'):
        value = config['dataset'][key]
        if len(value) != 64 or any(c not in '0123456789abcdef' for c in value):
            raise ValueError('identidade de dados/IDF deve ser SHA256')
    h3 = config['h3']
    if set(h3) != {'proposal', 'adopted_goal_seconds', 'goal_rationale', 'measurement', 'memory'} or h3['adopted_goal_seconds'] is not None:
        raise ValueError('meta H3 ainda não adotada')
    proposal = h3['proposal']
    for key in ('concurrency', 'warmups', 'measured_requests', 'cold_start_processes'):
        if type(proposal[key]) is not int or proposal[key] < 1:
            raise ValueError('parâmetro H3 proposto deve ser inteiro positivo')
    for key in ('http_p95_seconds', 'timeout_seconds'):
        if type(proposal[key]) not in (int, float) or not 0 < proposal[key] < float('inf'):
            raise ValueError('tempo H3 proposto inválido')
    return identity(config)


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


def annotation_examples(bundle, dataset, config, split):
    validate_protocol(config)
    require_split(split)
    task = bundle.get('task')
    if set(bundle) != {'schema', 'dataset_version', 'task', 'unit', 'rubric_id', 'origin', 'procedure_id',
                       'generator_relationship', 'shared_dependencies', 'records'}:
        raise ValueError('schema de anotações inválido')
    if bundle['schema'] != 'hts-annotations-1' or task not in ('H1', 'H2') or bundle['unit'] != 'sentence_pair':
        raise ValueError('tarefa/unidade de anotação incompatível')
    if bundle['dataset_version'] != dataset['manifest']['version'] or bundle['unit'] != config['tasks'][task]['unit']:
        raise ValueError('versão/unidade da anotação diverge do contrato')
    if bundle['origin'] not in ('human_independent', 'automated_weak', 'generator_dependent', 'artificial_fixture'):
        raise ValueError('origem de anotação inválida')
    if bundle['generator_relationship'] not in ('independent_declared', 'shared', 'same_generator', 'artificial_fixture'):
        raise ValueError('dependência da anotação ausente')
    if bundle['origin'] == 'human_independent' and bundle['generator_relationship'] != 'independent_declared':
        raise ValueError('independência contraditória')
    if not isinstance(bundle['shared_dependencies'], list) or not bundle['rubric_id'] or not bundle['procedure_id']:
        raise ValueError('procedimento/rubrica/dependências ausentes')
    pairs = {p['id']: p for p in dataset['pairs']}
    sources = {s['id']: s for s in dataset['sources']}
    seen, outputs, counts = set(), [], {'labeled': 0, 'ambiguous': 0, 'excluded': 0, 'other_split': 0}
    for row in bundle['records']:
        required = {'pair_id', 'source_id', 'source_sentence_id', 'suspect_sentence_id', 'source_text_sha256',
                    'suspect_text_sha256', 'status', 'target', 'reason', 'evidence_ref'}
        if set(row) != required:
            raise ValueError('schema de anotação individual inválido')
        key = tuple(row[k] for k in ('pair_id', 'source_id', 'source_sentence_id', 'suspect_sentence_id'))
        if key in seen:
            raise ValueError('anotação duplicada')
        seen.add(key)
        pair = pairs.get(row['pair_id'])
        source = sources.get(row['source_id'])
        if pair is None or source is None or row['source_id'] not in pair['source_ids'] or source['split'] != pair['split']:
            raise ValueError('IDs/ancestralidade/split de anotação inválidos')
        if pair['split'] == 'test':
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
        counts[row['status']] += 1
        if pair['split'] != split:
            counts['other_split'] += 1
            continue
        if row['status'] == 'labeled':
            outputs.append({'input': ModelInput(a['semantic'], b['semantic']), 'target': value,
                            'trace': {'observation': key, 'split': split, 'component': dataset['components'][pair['id']]}})
    return outputs, counts


def save_json_new(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, sort_keys=True, allow_nan=False, indent=2)


def import_annotations(path, destination, dataset, config, split):
    bundle = read_json(path)
    examples, counts = annotation_examples(bundle, dataset, config, split)
    if bundle['origin'] == 'artificial_fixture' and dataset['manifest']['version'] == config['dataset']['version'] and dataset['manifest']['metadata']['purpose'] == 'frozen_operational_derivation':
        raise PermissionError('anotações artificiais não podem rotular o dataset operacional')
    sources = {s['id']: s for s in dataset['sources']}
    potential = sum(len(pair['sentences']) * sum(len(sources[s]['sentences']) for s in set(pair['source_ids']))
                    for pair in dataset['pairs'] if pair['split'] == split)
    receipt = {'schema': 'hts-annotation-import-1', 'protocol_identity': validate_protocol(config),
               'annotation_identity': identity(bundle), 'dataset_version': bundle['dataset_version'],
               'task': bundle['task'], 'split': split, 'counts': counts, 'eligible': len(examples),
               'status': 'validated_not_scientifically_released', 'origin': bundle['origin'],
               'coverage': {'labeled_sentence_pairs_selected_split': len(examples),
                            'all_referenced_sentence_combinations_selected_split': potential,
                            'design': 'reported_not_claimed_exhaustive_or_probabilistic'}}
    save_json_new(destination, {'receipt': receipt, 'annotations': bundle})
    return receipt


def run_fixture(inputs, predict):
    if not inputs or any(type(row) is not ModelInput for row in inputs):
        raise ValueError('somente ModelInput, sem metadados de supervisão')
    predictions = [predict(**asdict(row)) for row in inputs]
    return predictions


def measure_fixture(operation, clock=perf_counter):
    if tracemalloc.is_tracing():
        raise RuntimeError('coletor tracemalloc já ativo; não interferir com outra medição')
    tracemalloc.start()
    start = clock()
    try:
        operation()
        status, error = 'ok', None
    except Exception as exc:
        status, error = 'error', type(exc).__name__
    finally:
        elapsed = clock() - start
        current, peak = tracemalloc.get_traced_memory()
        tracemalloc.stop()
    return {'status': status, 'seconds': elapsed, 'error_type': error,
            'python_traced_current_bytes': current, 'python_traced_peak_bytes': peak,
            'memory_scope': 'Python allocations tracked by tracemalloc; not RSS/native/GPU',
            'scope': 'software_fixture_not_H3', 'boundary': 'callable_in_process'}


def save_checkpoint(path, context, payload):
    validate_context(context)
    body = {'schema': 'hts-preparation-checkpoint-1', 'context': context, 'payload': payload}
    save_json_new(path, {**body, 'identity': identity(body)})


def load_checkpoint(path, expected_context):
    validate_context(expected_context)
    record = read_json(path)
    if set(record) != {'schema', 'context', 'payload', 'identity'}:
        raise ValueError('schema de checkpoint inválido')
    body = {k: v for k, v in record.items() if k != 'identity'}
    if record['identity'] != identity(body) or record['schema'] != 'hts-preparation-checkpoint-1' or record['context'] != expected_context:
        raise ValueError('checkpoint adulterado ou contexto incompatível')
    return record['payload']


def validate_context(context):
    required = {'protocol_identity', 'dataset_version', 'annotation_identity', 'task', 'unit',
                'model_identity', 'config_identity', 'code_identity', 'seed', 'phase'}
    if set(context) != required or type(context['seed']) is not int or context['seed'] < 0:
        raise ValueError('contexto de retomada incompleto')
    if any(type(v) is not str or not v for k, v in context.items() if k != 'seed'):
        raise ValueError('identidades/unidade/fase de retomada ausentes')
    if context['phase'] not in ('preflight', 'fixture'):
        raise PermissionError('checkpoint S5A não representa pesos treinados')
    for field in ('protocol_identity', 'config_identity', 'code_identity'):
        if len(context[field]) != 64 or any(c not in '0123456789abcdef' for c in context[field]):
            raise ValueError('identidade SHA256 inválida')


def attempt_event(folder, index, context, state, details):
    validate_context(context)
    if type(index) is not int or index < 0 or state not in ('started', 'complete', 'failed'):
        raise ValueError('evento de tentativa inválido')
    path = Path(folder)/f'{index:03d}-{state}.json'
    if state != 'started':
        start = read_json(Path(folder)/f'{index:03d}-started.json')
        if start['context'] != context or any((Path(folder)/f'{index:03d}-{s}.json').exists() for s in ('complete', 'failed')):
            raise ValueError('transição de tentativa incompatível')
    elif any((Path(folder)/f'{index:03d}-{s}.json').exists() for s in ('complete', 'failed')):
        raise ValueError('tentativa encerrada')
    save_json_new(path, {'context': context, 'state': state, 'details': details,
                         'utc': datetime.now(timezone.utc).isoformat()})
