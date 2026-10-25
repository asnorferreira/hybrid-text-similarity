from collections import Counter
from dataclasses import asdict
from pathlib import Path

from hts_core.adapters.dataset_store import digest, identity, read_json
from hts_core.adapters.experiment_io import (attempt_event, inspect_dataset, measure_fixture,
                                           run_fixture, save_checkpoint, save_json_new, validate_protocol)
from hts_core.domain.experiments import ModelInput, classification_report


def code_identity():
    root = Path(__file__).resolve().parents[1]
    return identity({p.relative_to(root).as_posix(): digest(p.read_bytes()) for p in sorted(root.rglob('*.py'))})


def context_for(config, phase, candidates=None):
    if candidates is not None:
        from hts_core.adapters.experiment_protocol import validate_candidates
        validate_candidates(candidates, config)
    return {'protocol_identity': validate_protocol(config), 'dataset_version': config['dataset']['version'],
            'annotation_identity': 'none_no_scientific_targets', 'task': 'preparation', 'unit': 'not_training',
            'model_identity': 'none_no_model_loaded', 'config_identity': identity(config) if candidates is None else identity({'protocol': config, 'candidates': candidates}),
            'code_identity': code_identity(), 'seed': config['seeds'][0], 'phase': phase}


def prepare(protocol, dataset, idf, destination, candidates=None):
    config = read_json(protocol)
    validate_protocol(config)
    proposals = read_json(candidates) if candidates is not None else None
    context = context_for(config, 'preflight', proposals)
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=False)
    attempt_event(out/'attempts', 0, context, 'started', {'operation': 'preflight_not_prediction'})
    try:
        data = inspect_dataset(dataset, config)
        from hts_core.adapters.idf_contract import validate_training_idf_contract
        idf_report = validate_training_idf_contract(dataset, idf, config['dataset']['idf_identity'])
        report = {'schema': 'hts-preflight-1', 'context': context, 'dataset_version': data['manifest']['version'],
                  'source_splits': dict(Counter(s['split'] for s in data['sources'])),
                  'pair_splits': dict(Counter(p['split'] for p in data['pairs'])),
                  'components_by_split': {split: len({data['components'][p['id']] for p in data['pairs'] if p['split'] == split})
                                          for split in ('train', 'validation', 'test')},
                  'targets_present': {'validated_class': sum(s['validated_class'] is not None for p in data['pairs'] for s in p['sentences']),
                                      'semantic_target': sum(s['semantic_target'] is not None for p in data['pairs'] for s in p['sentences'])},
                  'tasks': {task: {'status': 'blocked_for_experiment', 'blockers': spec['blockers'],
                                   'unit': spec['unit'], 'approved_contract_id': spec['approved_contract_id']}
                            for task, spec in config['tasks'].items()},
                  'idf': idf_report, 'candidate_proposals_identity': identity(proposals) if proposals is not None else None,
                  'candidate_proposals_status': 'not_adopted_no_training_release',
                  'prediction_executed': False, 'training_executed': False, 'final_test_opened_for_performance': False}
        save_json_new(out/'preflight.json', report)
        save_checkpoint(out/'checkpoint.json', context, {'status': 'preflight_complete', 'report_identity': identity(report)})
        attempt_event(out/'attempts', 0, context, 'complete', {'report_identity': identity(report)})
        return report
    except Exception as exc:
        attempt_event(out/'attempts', 0, context, 'failed', {'error_type': type(exc).__name__, 'message': str(exc)})
        raise


def fixture_smoke(protocol, destination):
    config = read_json(protocol)
    context = context_for(config, 'fixture')
    out = Path(destination)
    out.mkdir(parents=True, exist_ok=False)
    attempt_event(out/'attempts', 0, context, 'started', {'operation': 'artificial_software_fixture'})
    try:
        inputs = [ModelInput('A esfera é azul.', 'A esfera é azul.'), ModelInput('Um triângulo.', 'Dois quadrados.')]
        predictions = run_fixture(inputs, lambda source_text, suspect_text: 'same' if source_text == suspect_text else 'different')
        report = {'scope': 'artificial_software_fixture_not_H1_H2_H3', 'inputs': [asdict(row) for row in inputs],
                  'classification': classification_report(['same', 'different'], predictions, ['same', 'different']),
                  'instrumentation': measure_fixture(lambda: bytearray(1024)), 'weights_created': False,
                  'context': context}
        save_json_new(out/'fixture.json', report)
        save_checkpoint(out/'checkpoint.json', context, {'status': 'fixture_complete', 'report_identity': identity(report)})
        attempt_event(out/'attempts', 0, context, 'complete', {'report_identity': identity(report)})
        return report
    except Exception as exc:
        attempt_event(out/'attempts', 0, context, 'failed', {'error_type': type(exc).__name__, 'message': str(exc)})
        raise


def require_execution_authorization(config, task, split, stage, release):
    validate_protocol(config)
    if task not in config['tasks']:
        raise ValueError('tarefa desconhecida')
    bindings = {'protocol_identity': identity(config), 'dataset_version': config['dataset']['version'],
                'task': task, 'unit': config['tasks'][task]['unit'], 'target': config['tasks'][task]['target'],
                'models': config['baselines'], 'metrics': config['tasks'][task]['metrics'],
                'seeds': config['seeds'], 'config_identity': identity(config),
                'repetitions': config['training']['attempts']}
    if not isinstance(release, dict) or release.get('bindings') != bindings or not release.get('authorization_evidence'):
        raise PermissionError('autorização sem vínculo ao protocolo/dataset/alvo/unidade/modelos/config/métricas/seeds/repetições')
    raise PermissionError('executor S5A não executa treino/calibração/desempenho no teste; etapa posterior requer implementação e autorização próprias')
