from hts_core.adapters.contract_types import number, object_fields, sha256, string_list, text
from hts_core.adapters.dataset_store import identity


def validate_protocol(config):
    object_fields(config, {'schema', 'revision', 'status', 'dataset', 'hypotheses', 'tasks', 'baselines',
                          'seeds', 'execution', 'h3', 'training', 'test_policy'}, 'protocol')
    if config['schema'] != 'hts-experiment-protocol-1' or config['status'] != 'candidate':
        raise ValueError('schema/estado do protocolo inválido; S5A aceita protocolo candidato')
    number(config['revision'], 'revision', minimum=1, integer=True)
    object_fields(config['dataset'], {'version', 'idf_identity', 'idf_policy'}, 'dataset')
    for field in ('version', 'idf_identity'):
        sha256(config['dataset'][field], 'dataset.'+field)
    text(config['dataset']['idf_policy'], 'dataset.idf_policy')
    object_fields(config['hypotheses'], {'H1', 'H2', 'H3'}, 'hypotheses')
    object_fields(config['tasks'], {'H1', 'H2', 'H3'}, 'tasks')
    allowed_metrics = {'H1': {'macro_f1', 'confusion_matrix'},
                       'H2': {'spearman', 'pearson', 'mae', 'mse', 'r2'},
                       'H3': {'p50', 'p95', 'failure_rate'}}
    for name, task in config['tasks'].items():
        text(config['hypotheses'][name], 'hypotheses.'+name)
        object_fields(task, {'unit', 'target', 'metrics', 'blockers', 'approved_contract_id'}, 'tasks.'+name)
        text(task['target'], name+'.target')
        string_list(task['metrics'], name+'.metrics', allowed_metrics[name])
        required_metrics = {'H1': {'macro_f1'}, 'H2': {'spearman'}, 'H3': {'p95', 'failure_rate'}}[name]
        if not required_metrics <= set(task['metrics']):
            raise ValueError(name+': métricas primárias obrigatórias ausentes')
        string_list(task['blockers'], name+'.blockers')
        if task['unit'] != ('request' if name == 'H3' else 'sentence_pair'):
            raise ValueError('unidade do protocolo candidato incompatível')
        if task['approved_contract_id'] is not None:
            raise PermissionError('S5A não presume aprovação científica em campo isolado')
    if type(config['baselines']) is not list or not config['baselines']:
        raise ValueError('baselines: lista não vazia exigida')
    names = []
    for baseline in config['baselines']:
        object_fields(baseline, {'name', 'implementation', 'output', 'configuration', 'model_revision', 'classification_rule'}, 'baseline')
        for field in ('name', 'output', 'configuration', 'classification_rule'):
            text(baseline[field], 'baseline.'+field)
        names.append(baseline['name'])
        planned = baseline['name'] in ('learned_fusion', 'siamese')
        if planned:
            if baseline['implementation'] is not None or 'pending' not in baseline['configuration']:
                raise ValueError('baseline planejado exige implementation=null e motivo pending')
        else:
            text(baseline['implementation'], 'baseline.implementation')
        if baseline['model_revision'] is not None:
            revision = text(baseline['model_revision'], 'baseline.model_revision')
            if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
                raise ValueError('revisão de modelo deve ser commit hexadecimal fixo')
    string_list(names, 'baseline.names')
    if set(names) != {'E1_tfidf', 'E2_signature', 'E3_sbert', 'E4_alignment', 'fixed_fusion', 'learned_fusion', 'siamese'}:
        raise ValueError('baseline.names: inventário S5A incompleto/desconhecido')
    by_name = {b['name']: b for b in config['baselines']}
    if by_name['E3_sbert']['model_revision'] is None or by_name['fixed_fusion']['model_revision'] != by_name['E3_sbert']['model_revision']:
        raise ValueError('baselines semânticos existentes exigem a mesma revisão fixa')
    if type(config['seeds']) is not list or not config['seeds']:
        raise ValueError('seeds: lista não vazia exigida')
    for seed in config['seeds']:
        number(seed, 'seed', integer=True)
    if len(config['seeds']) != len(set(config['seeds'])):
        raise ValueError('seeds duplicadas')
    object_fields(config['execution'], {'stage', 'modes', 'prediction_splits'}, 'execution')
    if config['execution'] != {'stage': 'S5A', 'modes': ['preflight', 'fixture'], 'prediction_splits': ['train', 'validation']}:
        raise PermissionError('execução fora do alcance S5A')
    object_fields(config['test_policy'], {'performance_access', 'release'}, 'test_policy')
    if config['test_policy'] != {'performance_access': 'closed', 'release': 'requires_later_stage_and_bound_protocol_target_models_config_metrics_seeds_repetitions_authorization'}:
        raise PermissionError('proteção do teste ausente')
    _training(config['training'])
    _h3(config['h3'])
    return identity(config)


def _training(training):
    object_fields(training, {'architecture', 'reference_parameters', 'project_parameters', 'budget', 'selection', 'stop', 'attempts', 'status'}, 'training')
    if training['status'] != 'blocked':
        raise ValueError('treino S5A deve permanecer bloqueado')
    number(training['attempts'], 'training.attempts', integer=True, minimum=1)
    if training['attempts'] != 1:
        raise ValueError('S5A prepara uma tentativa futura; não realiza busca')
    if any(training[key] is not None for key in ('budget', 'selection', 'stop')):
        raise PermissionError('orçamento/seleção/parada reais dependem de protocolo posterior')
    arch = object_fields(training['architecture'], {'kind', 'base_model', 'base_revision', 'pooling', 'dense_dimensions', 'dropout', 'leaky_relu_alpha', 'alignment', 'long_sentence_policy'}, 'training.architecture')
    for field in ('kind', 'base_model', 'alignment'):
        text(arch[field], 'architecture.'+field)
    if arch['base_revision'] is not None:
        revision = text(arch['base_revision'], 'architecture.base_revision')
        if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
            raise ValueError('architecture.base_revision: commit fixo exigido')
    for field in ('pooling', 'long_sentence_policy'):
        if arch[field] is not None:
            text(arch[field], 'architecture.'+field)
    if arch['dense_dimensions'] is not None:
        dims = arch['dense_dimensions']
        if type(dims) is not list or not dims:
            raise ValueError('architecture.dense_dimensions: lista exigida')
        for dim in dims:
            number(dim, 'dense_dimension', integer=True, positive=True)
    for field in ('dropout', 'leaky_relu_alpha'):
        if arch[field] is not None:
            number(arch[field], 'architecture.'+field)
            if arch[field] >= 1:
                raise ValueError('architecture.'+field+': exige [0,1)')
    ref = object_fields(training['reference_parameters'], {'source', 'epochs', 'learning_rate', 'optimizer', 'max_tokens', 'weight_decay', 'loss'}, 'training.reference_parameters')
    for field in ('source', 'optimizer', 'loss'):
        text(ref[field], 'reference_parameters.'+field)
    for field in ('epochs', 'max_tokens'):
        number(ref[field], 'reference_parameters.'+field, integer=True, positive=True)
    number(ref['learning_rate'], 'reference_parameters.learning_rate', positive=True)
    number(ref['weight_decay'], 'reference_parameters.weight_decay')
    project = object_fields(training['project_parameters'], {'batch_size', 'candidate_selection', 'early_stopping', 'weights_export'}, 'training.project_parameters')
    for field in ('candidate_selection', 'early_stopping', 'weights_export'):
        text(project[field], 'project_parameters.'+field)
    if project['batch_size'] is not None:
        number(project['batch_size'], 'project_parameters.batch_size', integer=True, positive=True)


def _h3(h3):
    object_fields(h3, {'proposal', 'adopted_goal_seconds', 'goal_rationale', 'measurement', 'memory'}, 'h3')
    if h3['adopted_goal_seconds'] is not None:
        raise ValueError('meta H3 ainda não adotada')
    for field in ('goal_rationale', 'measurement', 'memory'):
        text(h3[field], 'h3.'+field)
    p = object_fields(h3['proposal'], {'http_p95_seconds', 'concurrency', 'warmups', 'measured_requests', 'timeout_seconds', 'cold_start_processes', 'formats', 'sentence_counts_per_document'}, 'h3.proposal')
    for field in ('concurrency', 'warmups', 'measured_requests', 'cold_start_processes'):
        number(p[field], 'h3.proposal.'+field, integer=True, positive=True)
    for field in ('http_p95_seconds', 'timeout_seconds'):
        number(p[field], 'h3.proposal.'+field, positive=True)
    if p['http_p95_seconds'] > p['timeout_seconds']:
        raise ValueError('h3: meta proposta excede timeout')
    string_list(p['formats'], 'h3.proposal.formats', {'txt', 'docx', 'pdf'})
    counts = p['sentence_counts_per_document']
    if type(counts) is not list or not counts:
        raise ValueError('h3.proposal.sentence_counts_per_document: lista exigida')
    for count in counts:
        number(count, 'h3.proposal.sentence_counts_per_document', integer=True, positive=True)
    if len(counts) != len(set(counts)):
        raise ValueError('h3: quantidades de sentenças duplicadas')


def validate_candidates(candidate, config):
    protocol_id = validate_protocol(config)
    object_fields(candidate, {'schema', 'status', 'reference_protocol_identity', 'primary_metrics', 'h1', 'h2',
                              'siamese', 'budget', 'checkpoint_requirements', 'statistics', 'h3_acceptance'}, 'candidates')
    if candidate['schema'] != 'hts-experiment-candidates-1' or candidate['status'] != 'candidate_not_adopted_not_executable_training':
        raise ValueError('candidates: estado/schema inválidos')
    if candidate['reference_protocol_identity'] != protocol_id:
        raise ValueError('candidates: protocolo de referência divergente')
    if candidate['primary_metrics'] != {'H1': 'macro_f1', 'H2': 'spearman', 'H3': ['p95', 'failure_rate']}:
        raise ValueError('candidates: métricas primárias incompatíveis')
    h1 = object_fields(candidate['h1'], {'unit', 'classes', 'features_by_system', 'classifier', 'eligibility', 'failures', 'blockers'}, 'candidates.h1')
    string_list(h1['classes'], 'h1.classes', {'copia_exata', 'copia_editada', 'parafrase', 'sem_correspondencia_detectada'})
    if len(h1['classes']) != 4 or h1['unit'] != 'sentence_pair':
        raise ValueError('h1: universo/unidade incompatível')
    object_fields(h1['features_by_system'], {'lexical', 'semantic', 'fixed_fusion'}, 'h1.features')
    allowed_features = {'lexical_cosine', 'semantic_cosine_raw', '0.4*lexical_cosine+0.6*max(0,semantic_cosine_raw)'}
    for features in h1['features_by_system'].values():
        string_list(features, 'h1.features', allowed_features)
        if len(features) != 1:
            raise ValueError('h1: proposta usa um escalar por sistema')
    classifier = object_fields(h1['classifier'], {'kind', 'penalty', 'C', 'max_iter', 'seed', 'fit_split', 'selection_split', 'class_weight'}, 'h1.classifier')
    if classifier['kind'] != 'multinomial_logistic_regression' or classifier['penalty'] != 'l2' or classifier['class_weight'] is not None:
        raise ValueError('h1: classificador candidato incompatível')
    if classifier['fit_split'] != 'train' or classifier['selection_split'] != 'validation':
        raise PermissionError('h1: teste fechado')
    number(classifier['C'], 'h1.C', positive=True)
    number(classifier['max_iter'], 'h1.max_iter', positive=True, integer=True)
    number(classifier['seed'], 'h1.seed', integer=True)
    for field in ('eligibility', 'failures'):
        text(h1[field], 'h1.'+field)
    string_list(h1['blockers'], 'h1.blockers')
    h2 = object_fields(candidate['h2'], {'unit', 'construct', 'range', 'annotation_schema', 'contradiction_policy', 'baseline_diagnostics', 'blockers'}, 'candidates.h2')
    if h2['unit'] != 'sentence_pair' or h2['annotation_schema'] != 'hts-annotations-2' or type(h2['range']) is not list or len(h2['range']) != 2:
        raise ValueError('h2: unidade/schema/faixa incompatível')
    for item in h2['range']:
        number(item, 'h2.range')
    if h2['range'] != [0, 1]:
        raise ValueError('h2.range incompatível')
    for field in ('construct', 'contradiction_policy', 'baseline_diagnostics'):
        text(h2[field], 'h2.'+field)
    string_list(h2['blockers'], 'h2.blockers')
    siamese = object_fields(candidate['siamese'], {'base', 'revision', 'license', 'sharing', 'pooling', 'embedding_dimension', 'pair_features', 'dense_dimensions', 'head', 'layer_norm_epsilon', 'leaky_relu_alpha', 'dropout', 'loss', 'optimizer', 'learning_rate', 'weight_decay', 'long_sentences', 'input', 'output', 'source_status'}, 'candidates.siamese')
    for field in set(siamese)-{'embedding_dimension', 'dense_dimensions', 'layer_norm_epsilon', 'leaky_relu_alpha', 'dropout', 'learning_rate', 'weight_decay'}:
        text(siamese[field], 'siamese.'+field)
    revision = siamese['revision']
    if len(revision) != 40 or any(c not in '0123456789abcdef' for c in revision):
        raise ValueError('siamese.revision: commit fixo exigido')
    number(siamese['embedding_dimension'], 'embedding_dimension', integer=True, positive=True)
    dims = siamese['dense_dimensions']
    if type(dims) is not list or len(dims) != 3:
        raise ValueError('siamese.dense_dimensions: três dimensões exigidas')
    for dim in dims:
        number(dim, 'dense_dimension', integer=True, positive=True)
    if dims[0] != 2*siamese['embedding_dimension'] or dims[-1] != 1:
        raise ValueError('siamese: concat simétrica/saída escalar incompatível')
    for field in ('layer_norm_epsilon', 'learning_rate'):
        number(siamese[field], 'siamese.'+field, positive=True)
    for field in ('leaky_relu_alpha', 'dropout', 'weight_decay'):
        number(siamese[field], 'siamese.'+field)
    if siamese['dropout'] >= 1 or siamese['leaky_relu_alpha'] >= 1:
        raise ValueError('siamese: dropout/alfa fora de [0,1)')
    budget = object_fields(candidate['budget'], {'device', 'threads', 'microbatch', 'gradient_accumulation', 'maximum_epochs', 'maximum_optimizer_updates', 'maximum_wall_seconds', 'process_rss_limit_bytes', 'attempts', 'early_stopping_patience_epochs', 'selection', 'stop', 'rationale'}, 'candidates.budget')
    for field in set(budget)-{'device', 'selection', 'stop', 'rationale'}:
        number(budget[field], 'budget.'+field, integer=True, positive=True)
    if budget['device'] != 'cpu' or budget['attempts'] != 1:
        raise ValueError('budget: CPU/uma tentativa propostos')
    for field in ('selection', 'stop', 'rationale'):
        text(budget[field], 'budget.'+field)
    string_list(candidate['checkpoint_requirements'], 'checkpoint_requirements')
    stats = object_fields(candidate['statistics'], {'recommendation', 'alternatives', 'current_components_per_split'}, 'statistics')
    text(stats['recommendation'], 'statistics.recommendation')
    string_list(stats['alternatives'], 'statistics.alternatives')
    number(stats['current_components_per_split'], 'statistics.components', integer=True, positive=True)
    h3 = object_fields(candidate['h3_acceptance'], {'http_p95_goal_seconds', 'maximum_failure_rate', 'criterion', 'status'}, 'h3_acceptance')
    number(h3['http_p95_goal_seconds'], 'h3_acceptance.goal', positive=True)
    number(h3['maximum_failure_rate'], 'h3_acceptance.failures')
    if h3['maximum_failure_rate'] > 1 or h3['status'] != 'proposal_not_adopted':
        raise ValueError('h3_acceptance: taxa/estado incompatível')
    text(h3['criterion'], 'h3_acceptance.criterion')
    return identity(candidate)
