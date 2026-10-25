from copy import deepcopy
from dataclasses import asdict
import json
from pathlib import Path
import subprocess
import sys

import pytest

from hts_core.adapters.dataset_store import digest, identity, read_json, seal
from hts_core.adapters.experiment_io import (annotation_examples, attempt_event, import_annotations,
    inspect_dataset, load_checkpoint, measure_fixture, run_fixture, save_checkpoint, save_json_new, validate_protocol)
from hts_core.application.experiment_preparation import (context_for, fixture_smoke, prepare,
                                                       require_execution_authorization)
from hts_core.domain.experiments import (ModelInput, classification_report, cluster_bootstrap_difference,
    dependency_components, latency_report, percentile, regression_report, require_split)
from hts_core.domain.experiments import validate_outputs
from hts_core.domain.metrics import BinaryCounts, average_ranks, mae, mse, pearson, spearman, weighted_mean

CORE = Path(__file__).resolve().parents[1]


@pytest.fixture
def config():
    return read_json(CORE/'configs/experiment_s5a.json')


@pytest.fixture
def artificial(tmp_path, config):
    folder = tmp_path/'data'
    sources, pairs = [], []
    for split in ('train', 'validation', 'test'):
        source = {'id': 's-'+split, 'group': 'g-'+split, 'split': split, 'revision': 1,
                  'raw_sha256': 'raw', 'normalized_sha256': 'normalized',
                  'sentences': [{'id': 'a-'+split, 'semantic': 'A esfera é azul.'}]}
        pair = {'id': 'p-'+split, 'source_id': source['id'], 'source_ids': [source['id']], 'split': split,
                'sentences': [{'id': 'b-'+split, 'semantic': 'A esfera tem cor azul.', 'ancestors': [],
                               'validated_class': None, 'semantic_target': None}]}
        sources.append(source)
        pairs.append(pair)
    folder.mkdir()
    for name, rows in [('sources.jsonl', sources), ('pairs.jsonl', pairs)]:
        (folder/name).write_text(''.join(json.dumps(row, ensure_ascii=False)+'\n' for row in rows), encoding='utf-8')
    manifest = seal(folder, {'purpose': 'frozen_operational_derivation'})
    config['dataset']['version'] = manifest['version']
    data = inspect_dataset(folder, config)
    bundle = {'schema': 'hts-annotations-1', 'dataset_version': manifest['version'], 'task': 'H2',
              'unit': 'sentence_pair', 'rubric_id': 'artificial-rubric', 'origin': 'artificial_fixture',
              'procedure_id': 'test-only-no-person', 'generator_relationship': 'artificial_fixture',
              'shared_dependencies': ['artificial fixture'], 'records': [
                  {'pair_id': 'p-train', 'source_id': 's-train', 'source_sentence_id': 'a-train',
                   'suspect_sentence_id': 'b-train', 'source_text_sha256': digest('A esfera é azul.'.encode()),
                   'suspect_text_sha256': digest('A esfera tem cor azul.'.encode()), 'status': 'labeled',
                   'target': .75, 'reason': 'literal artificial fixture, not research', 'evidence_ref': 'test_literal'}]}
    return folder, data, bundle


def test_classification_literal_oracle_absent_and_all_wrong():
    report = classification_report(['a', 'a', 'b'], ['a', 'b', 'b'], ['a', 'b', 'absent'])
    assert report['confusion'] == [[1, 1, 0], [0, 1, 0], [0, 0, 0]]
    assert report['macro_f1'] == pytest.approx(4/9)
    assert report['per_class']['absent'] == {'precision': 0, 'recall': 0, 'f1': 0, 'support': 0}
    assert classification_report(['a', 'b'], ['b', 'a'], ['a', 'b'])['macro_f1'] == 0


@pytest.mark.parametrize('truth,pred,labels', [([], [], ['a']), (['a'], [], ['a']),
    (['a'], ['b'], ['a']), ([None], ['a'], ['a']), (['a'], ['a'], ['a', 'a'])])
def test_invalid_classification(truth, pred, labels):
    with pytest.raises(ValueError):
        classification_report(truth, pred, labels)


def test_regression_oracles_ties_constants():
    assert average_ranks([10, 10, 30]) == [1.5, 1.5, 3]
    assert spearman([1, 1, 2, 2], [4, 4, 1, 1]) == pytest.approx(-1)
    assert pearson([1, 2, 3], [3, 2, 1]) == pytest.approx(-1)
    report = regression_report([1, 2, 3, 4], [1.5, 2, 2.5, 4])
    assert report['mse'] == .125 and report['mae'] == .25
    assert report['r2']['value'] == .9
    constant = regression_report([1, 2], [0, 0])
    assert constant['spearman']['status'] == 'undefined' and constant['spearman']['value'] is None
    assert regression_report([1, 1], [1, 1])['r2']['value'] is None
    assert regression_report([1], [1])['pearson']['status'] == 'undefined'


@pytest.mark.parametrize('value', [float('nan'), float('inf'), -float('inf'), True, '1'])
@pytest.mark.parametrize('metric', [mae, mse, pearson, spearman])
def test_nonfinite_metrics_rejected(value, metric):
    with pytest.raises(ValueError):
        metric([1, value], [2, 3])


def test_weights_and_boolean_counts_rejected():
    with pytest.raises(ValueError):
        BinaryCounts(True, 0, 0, 0)
    with pytest.raises(ValueError):
        weighted_mean([1, 2], [2, -1])


def test_latency_oracle_includes_failed_attempts():
    report = latency_report([{'status': 'ok', 'seconds': 1}, {'status': 'ok', 'seconds': 3},
                             {'status': 'timeout', 'seconds': 30}])
    assert report['successful_seconds'] == {'p50': 2, 'p95': 2.9}
    assert report['failure_rate'] == pytest.approx(1/3)
    assert report['all_attempts_seconds'] == [1, 3, 30]
    assert latency_report([{'status': 'error', 'seconds': .1}])['successful_seconds'] is None
    with pytest.raises(ValueError):
        percentile([float('nan')], .5)


def test_bootstrap_cluster_oracle_and_single_component_refusal():
    report = cluster_bootstrap_difference(['a', 'b'], ['a', 'b'], ['b', 'a'], ['x', 'y'], ['a', 'b'], 17, 30)
    assert report['difference'] == 1
    assert set(report['draws']) <= {.5, 1}
    assert report == cluster_bootstrap_difference(['a', 'b'], ['a', 'b'], ['b', 'a'], ['x', 'y'], ['a', 'b'], 17, 30)
    with pytest.raises(ValueError, match='dois componentes'):
        cluster_bootstrap_difference(['a', 'b'], ['a', 'b'], ['b', 'a'], ['x', 'x'], ['a', 'b'], 17, 30)


def test_multisource_components_merge_and_reject_cross_split():
    sources = [{'id': name, 'group': name, 'split': 'train'} for name in ['a', 'b', 'c']]
    pairs = [{'id': 'p1', 'source_id': 'a', 'source_ids': ['a', 'b'], 'split': 'train', 'sentences': []},
             {'id': 'p2', 'source_id': 'b', 'source_ids': ['b'], 'split': 'train',
              'sentences': [{'ancestors': [{'source_id': 'c'}]}]}]
    assert dependency_components(sources, pairs) == {'p1': 'a', 'p2': 'a'}
    sources[2]['split'] = 'test'
    with pytest.raises(ValueError, match='splits'):
        dependency_components(sources, pairs)


def test_same_family_cannot_cross_splits():
    with pytest.raises(ValueError, match='família'):
        dependency_components([{'id': 'a', 'group': 'shared', 'split': 'train'},
                               {'id': 'b', 'group': 'shared', 'split': 'test'}], [])


def test_prediction_shape_scalar_and_finite_contract():
    assert validate_outputs([0, .5, 1], 3, 'H2') == [0, .5, 1]
    for values in [[.1], [[.1], [.2]], [True, .2], [float('nan'), .2], [1.1, .2]]:
        with pytest.raises(ValueError):
            validate_outputs(values, 2, 'H2')
    with pytest.raises(ValueError):
        validate_outputs(['C5'], 1, 'H1', ['parafrase'])


def test_model_input_has_only_text_and_predictor_never_receives_metadata():
    row = ModelInput('Texto A.', 'Texto B.')
    assert set(asdict(row)) == {'source_text', 'suspect_text'}
    assert run_fixture([row], lambda source_text, suspect_text: source_text+'|'+suspect_text) == ['Texto A.|Texto B.']
    with pytest.raises(ValueError, match='metadados'):
        run_fixture([{'source_text': 'A', 'suspect_text': 'B', 'target': 1, 'id': 'secret'}], lambda **kw: 1)
    with pytest.raises(TypeError):
        ModelInput('A', 'B', target=1)


@pytest.mark.parametrize('field,value', [('seeds', [True]), ('seeds', [1, 1]), ('status', 'approved'), ('revision', 0)])
def test_invalid_protocol(config, field, value):
    config[field] = value
    with pytest.raises(ValueError):
        validate_protocol(config)


def test_scientific_release_not_a_boolean(config):
    for field in ['training', 'calibration', 'test_access']:
        with pytest.raises(PermissionError):
            require_execution_authorization(config, 'H2', 'test', 'S5C', {field: True})
    for split in ['test', 'all', None]:
        with pytest.raises(PermissionError):
            require_split(split)
    config['tasks']['H2']['approved_contract_id'] = 'pretend approval'
    with pytest.raises(PermissionError):
        validate_protocol(config)


def test_complete_declared_release_still_cannot_open_s5a_test(config):
    bindings = {'protocol_identity': identity(config), 'dataset_version': config['dataset']['version'],
                'task': 'H2', 'unit': config['tasks']['H2']['unit'], 'target': config['tasks']['H2']['target'],
                'models': config['baselines'], 'metrics': config['tasks']['H2']['metrics'],
                'seeds': config['seeds'], 'config_identity': identity(config), 'repetitions': 1}
    with pytest.raises(PermissionError, match='executor S5A'):
        require_execution_authorization(config, 'H2', 'test', 'S5C',
                                        {'bindings': bindings, 'authorization_evidence': 'artificial_test_document'})


@pytest.mark.parametrize('field,value', [('concurrency', True), ('warmups', -1), ('timeout_seconds', float('nan'))])
def test_invalid_h3_candidate_configuration(config, field, value):
    config['h3']['proposal'][field] = value
    with pytest.raises(ValueError):
        validate_protocol(config)


def test_annotations_bind_text_and_do_not_use_construction_labels(artificial, config):
    _, data, bundle = artificial
    rows, counts = annotation_examples(bundle, data, config, 'train')
    assert rows[0]['target'] == .75 and counts['labeled'] == 1
    assert asdict(rows[0]['input']) == {'source_text': 'A esfera é azul.', 'suspect_text': 'A esfera tem cor azul.'}
    bundle['records'][0]['status'] = 'ambiguous'
    bundle['records'][0]['target'] = None
    assert annotation_examples(bundle, data, config, 'train')[0] == []


@pytest.mark.parametrize('change', ['duplicate', 'text', 'id', 'unit', 'version', 'boolean_target', 'nan', 'unlabeled_target', 'construction_class', 'test'])
def test_annotation_negative_controls(artificial, config, change):
    _, data, bundle = artificial
    row = bundle['records'][0]
    if change == 'duplicate': bundle['records'].append(deepcopy(row))
    elif change == 'text': row['source_text_sha256'] = 'wrong'
    elif change == 'id': row['source_sentence_id'] = 'unknown'
    elif change == 'unit': bundle['unit'] = 'document'
    elif change == 'version': bundle['dataset_version'] = 'wrong'
    elif change == 'boolean_target': row['target'] = True
    elif change == 'nan': row['target'] = float('nan')
    elif change == 'unlabeled_target': row['status'] = 'excluded'
    elif change == 'construction_class': bundle['task'] = 'H1'; row['target'] = 'C5'
    else:
        for field in ['pair_id', 'source_id', 'source_sentence_id', 'suspect_sentence_id']:
            row[field] = row[field].replace('train', 'test')
    with pytest.raises((ValueError, PermissionError)):
        annotation_examples(bundle, data, config, 'train')


def test_import_annotation_exclusive_destination_and_artificial_refusal(artificial, config, tmp_path):
    _, data, bundle = artificial
    source = tmp_path/'annotations.json'
    save_json_new(source, bundle)
    with pytest.raises(PermissionError, match='artificiais'):
        import_annotations(source, tmp_path/'refused.json', data, config, 'train')
    bundle['origin'] = 'automated_weak'
    bundle['generator_relationship'] = 'shared'
    save_json_new(tmp_path/'weak.json', bundle)
    receipt = import_annotations(tmp_path/'weak.json', tmp_path/'accepted.json', data, config, 'train')
    assert receipt['status'] == 'validated_not_scientifically_released'
    with pytest.raises(FileExistsError):
        import_annotations(tmp_path/'weak.json', tmp_path/'accepted.json', data, config, 'train')


def test_checkpoint_roundtrip_rejects_each_changed_context_and_tampering(config, tmp_path):
    context = context_for(config, 'fixture')
    path = tmp_path/'check.json'
    save_checkpoint(path, context, {'shape': [2, 2], 'trained_weights': False})
    assert load_checkpoint(path, context)['shape'] == [2, 2]
    for name in ['dataset_version', 'annotation_identity', 'task', 'unit', 'model_identity', 'seed', 'phase']:
        changed = {**context, name: context[name]+1 if name == 'seed' else 'changed'}
        with pytest.raises((ValueError, PermissionError)):
            load_checkpoint(path, changed)
    altered = read_json(path); altered['payload']['shape'] = [9, 9]
    path.write_text(json.dumps(altered), encoding='utf-8')
    with pytest.raises(ValueError, match='adulterado'):
        load_checkpoint(path, context)


def test_attempt_lifecycle_and_resume_no_overwrite(config, tmp_path):
    context = context_for(config, 'fixture')
    attempt_event(tmp_path, 0, context, 'started', {})
    attempt_event(tmp_path, 0, context, 'failed', {'error': 'artificial'})
    with pytest.raises(ValueError):
        attempt_event(tmp_path, 0, context, 'complete', {})
    attempt_event(tmp_path, 1, context, 'started', {'resumes_attempt': 0})
    attempt_event(tmp_path, 1, context, 'complete', {'fixture': True})


def test_instrumentation_independent_clock_and_failure():
    ticks = iter([10, 10.125])
    result = measure_fixture(lambda: bytearray(1024), clock=lambda: next(ticks))
    assert result['seconds'] == .125 and result['status'] == 'ok'
    result = measure_fixture(lambda: 1/0)
    assert result['status'] == 'error' and result['error_type'] == 'ZeroDivisionError'
    assert result['memory_scope'].startswith('Python allocations')


def test_fixture_end_to_end_serialization_no_trained_weights(config, tmp_path):
    source = tmp_path/'protocol.json'; save_json_new(source, config)
    result = fixture_smoke(source, tmp_path/'run')
    assert result['weights_created'] is False
    assert result['classification']['confusion'] == [[1, 0], [0, 1]]
    assert load_checkpoint(tmp_path/'run/checkpoint.json', result['context'])['status'] == 'fixture_complete'
    assert not list((tmp_path/'run').rglob('*.safetensors'))


def test_missing_resource_records_failed_attempt(artificial, config, tmp_path):
    folder, _, _ = artificial
    protocol = tmp_path/'config.json'; save_json_new(protocol, config)
    with pytest.raises(FileNotFoundError):
        prepare(protocol, folder, tmp_path/'missing-idf', tmp_path/'preflight')
    assert read_json(tmp_path/'preflight/attempts/000-failed.json')['state'] == 'failed'


def test_preflight_positive_small_independent_fixture(artificial, config, tmp_path):
    folder, data, _ = artificial
    table = {'n_docs': 1, 'df': {'esfera': 1}, 'formula': 'ln((1+N)/(1+df))+1'}
    source = data['sources'][0]
    descriptor = {'training_sources': [{k: source[k] for k in ('id', 'revision', 'raw_sha256', 'normalized_sha256')}],
                  'allowed_split': 'train', 'table_content_sha256': identity(table)}
    descriptor['identity'] = identity(descriptor); table['version'] = descriptor['identity']
    config['dataset']['idf_identity'] = table['version']
    protocol = tmp_path/'protocol.json'; save_json_new(protocol, config)
    save_json_new(tmp_path/'idf/idf.json', table); save_json_new(tmp_path/'idf/construction.json', descriptor)
    result = prepare(protocol, folder, tmp_path/'idf', tmp_path/'ready')
    assert result['prediction_executed'] is False and result['targets_present']['semantic_target'] == 0
    assert result['tasks']['H2']['status'] == 'blocked_for_experiment'


def test_cli_help_and_test_split_refusal():
    p = subprocess.run([sys.executable, '-m', 'hts_core.cli', 'experiment', '--help'], capture_output=True, text=True)
    assert p.returncode == 0 and 'preflight' in p.stdout
    p = subprocess.run([sys.executable, '-m', 'hts_core.cli', 'experiment', 'import-annotations',
                        '--protocol', 'unused', '--out', 'unused', '--dataset', 'unused',
                        '--annotations', 'unused', '--split', 'test'], capture_output=True, text=True)
    assert p.returncode == 2 and 'invalid choice' in p.stderr
