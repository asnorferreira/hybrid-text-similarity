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


def fixture_pipeline():
    from hts_core.adapters.idf_contract import LEXICAL_CODE
    return {'code': {key: '0'*64 for key in LEXICAL_CODE}, 'disabled': ['parser', 'ner'],
            'font_assets': {'fixture.txt': '0'*64}, 'generator_scripts': {'fixture.py': '0'*64},
            'lock_sha256': '0'*64, 'model': {'name': 'artificial', 'version': 'fixture', 'license': 'fixture'},
            'model_assets': {'fixture.bin': '0'*64}, 'packages': {'spacy': 'fixture', 'pt-core-news-sm': 'fixture', 'numpy': 'fixture'},
            'python': 'fixture', 'stopwords': [], 'text_hash_policy': 'UTF-8 source/config/lock text CRLF normalized to LF; binary assets unchanged',
            'unicode': 'fixture'}


@pytest.fixture
def artificial(tmp_path, config):
    folder = tmp_path/'data'
    sources, pairs = [], []
    for split in ('train', 'validation', 'test'):
        source = {'id': 's-'+split, 'group': 'g-'+split, 'split': split, 'revision': 1,
                  'text': 'A esfera é azul.', 'raw_sha256': digest(b'raw'),
                  'normalized_sha256': digest('A esfera é azul.'.encode()),
                  'raw_file': split+'.raw', 'normalized_file': split+'.txt',
                  'sentences': [{'id': 'a-'+split, 'semantic': 'A esfera é azul.'}]}
        pair = {'id': 'p-'+split, 'source_id': source['id'], 'source_ids': [source['id']], 'split': split,
                'sentences': [{'id': 'b-'+split, 'semantic': 'A esfera tem cor azul.', 'ancestors': [],
                               'validated_class': None, 'semantic_target': None}]}
        sources.append(source)
        pairs.append(pair)
    folder.mkdir()
    save_json_new(folder/'config.json', {'purpose': 'operational_derivation', 'seed': 20261024})
    save_json_new(folder/'pipeline.json', fixture_pipeline())
    for source in sources:
        (folder/source['raw_file']).write_bytes(b'raw')
        (folder/source['normalized_file']).write_bytes(source['text'].encode())
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
    table = {'n_docs': 1, 'df': {'esfera': 1}, 'formula': 'ln((1+N)/(1+df))+1',
             'tf': 'raw_count', 'unknown_df': 0, 'vector_normalization': 'cosine_only'}
    source = data['sources'][0]
    descriptor = {'training_sources': [{k: source[k] for k in ('id', 'revision', 'raw_sha256', 'normalized_sha256')}],
                  'allowed_split': 'train', 'table_content_sha256': identity(table),
                  'purpose': 'operational_derivation', 'construction_attestation': True,
                  'pipeline': fixture_pipeline(), 'config': read_json(folder/'config.json'),
                  'input_identity': identity([{'id': source['id'], 'text': source['text']}])}
    descriptor['identity'] = identity(descriptor); table['version'] = descriptor['identity']
    config['dataset']['idf_identity'] = table['version']
    protocol = tmp_path/'protocol.json'; save_json_new(protocol, config)
    save_json_new(tmp_path/'idf/idf.json', table); save_json_new(tmp_path/'idf/construction.json', descriptor)
    save_json_new(tmp_path/'idf/execution.json', {'dataset_version': data['manifest']['version'],
                  'constructed_utc': '2026-10-25T00:00:00+00:00', 'platform': 'artificial fixture',
                  'serialized_table_sha256': digest((tmp_path/'idf/idf.json').read_bytes())})
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


def change_path(value, path, replacement):
    for key in path[:-1]:
        value = value[key]
    value[path[-1]] = replacement


@pytest.mark.parametrize('path,value', [
    (['h3', 'proposal', 'formats'], ['exe']),
    (['h3', 'proposal', 'sentence_counts_per_document'], [True, 0, -10]),
    (['baselines'], [{'name': 'incompleto'}]),
    (['training', 'architecture'], 'qualquer texto'),
    (['training', 'reference_parameters'], None),
    (['training', 'project_parameters'], []),
    (['tasks', 'H1', 'metrics'], ['macro_f1', 'macro_f1']),
    (['h3', 'proposal', 'formats'], ['txt', 'txt']),
    (['h3', 'proposal', 'sentence_counts_per_document'], [1, 1]),
    (['h3', 'proposal', 'timeout_seconds'], True),
    (['h3', 'goal_rationale'], '  '),
    (['training', 'architecture', 'pooling'], []),
    (['training', 'architecture', 'dropout'], float('inf')),
    (['training', 'architecture', 'dense_dimensions'], [True]),
    (['training', 'reference_parameters', 'epochs'], True),
    (['training', 'project_parameters', 'batch_size'], 0),
    (['dataset', 'idf_policy'], '  '),
    (['tasks', 'H2', 'metrics'], ['macro_f1']),
    (['tasks', 'H2', 'blockers'], ['  ']),
    (['seeds'], '123'),
    (['baselines', 0, 'implementation'], None),
    (['baselines', 5, 'implementation'], 'pretend_executable'),
    (['baselines', 2, 'model_revision'], None),
    (['h3', 'proposal', 'http_p95_seconds'], 100),
])
def test_protocol_audit_regressions(config, path, value):
    change_path(config, path, value)
    with pytest.raises(ValueError):
        validate_protocol(config)


@pytest.mark.parametrize('path', [[], ['dataset'], ['hypotheses'], ['tasks'], ['tasks', 'H1'],
    ['h3'], ['h3', 'proposal'], ['training'], ['training', 'architecture'],
    ['training', 'reference_parameters'], ['training', 'project_parameters'], ['baselines', 0],
    ['execution'], ['test_policy']])
@pytest.mark.parametrize('mutation', ['unknown', 'missing'])
def test_protocol_every_object_exact_fields(config, path, mutation):
    target = config
    for key in path:
        target = target[key]
    if mutation == 'unknown':
        target['uncontracted'] = 'not permitted'
    else:
        target.pop(next(iter(target)))
    with pytest.raises(ValueError):
        validate_protocol(config)


def test_protocol_valid_candidate_stays_accepted(config):
    assert validate_protocol(config) == identity(config)


@pytest.fixture
def idf_documents(artificial, config, tmp_path):
    folder, data, _ = artificial
    source = data['sources'][0]
    table = {'n_docs': 1, 'df': {'esfera': 1}, 'formula': 'ln((1+N)/(1+df))+1',
             'tf': 'raw_count', 'unknown_df': 0, 'vector_normalization': 'cosine_only'}
    descriptor = {'purpose': 'operational_derivation', 'construction_attestation': True, 'allowed_split': 'train',
                  'training_sources': [{k: source[k] for k in ('id', 'revision', 'raw_sha256', 'normalized_sha256')}],
                  'pipeline': fixture_pipeline(), 'config': read_json(folder/'config.json'),
                  'input_identity': identity([{'id': source['id'], 'text': source['text']}])}
    execution = {'dataset_version': data['manifest']['version'], 'constructed_utc': '2026-10-25T00:00:00+00:00',
                 'platform': 'fixture only, no model used', 'serialized_table_sha256': '0'*64}
    return folder, tmp_path/'idf', table, descriptor, execution


def save_idf_documents(idf, table, descriptor, execution):
    descriptor['table_content_sha256'] = identity({k: v for k, v in table.items() if k != 'version'})
    descriptor['identity'] = identity({k: v for k, v in descriptor.items() if k != 'identity'})
    table['version'] = descriptor['identity']
    save_json_new(idf/'idf.json', table)
    save_json_new(idf/'construction.json', descriptor)
    execution['serialized_table_sha256'] = digest((idf/'idf.json').read_bytes())
    save_json_new(idf/'execution.json', execution)


@pytest.mark.parametrize('case', ['valid', 'review', 'original', 'reconstructed', 'inventory'])
def test_idf_frozen_parent_uses_freeze_records_not_collection_manifest(idf_documents, case):
    from hts_core.adapters.idf_contract import validate_training_idf_contract
    folder, idf, table, descriptor, execution = idf_documents
    parent = execution['dataset_version']
    save_json_new(folder/'upstream-manifest.json', {'source': 'artificial collection, no dataset version'})
    payload = {p.name: digest(p.read_bytes()) for p in folder.iterdir() if p.name != 'manifest.json'}
    review = {'dataset_version': parent}
    proof = {'original_version': parent, 'reconstructed_version': parent, 'file_inventory_sha256': identity(payload)}
    if case == 'review': review['dataset_version'] = '1'*64
    elif case == 'original': proof['original_version'] = '1'*64
    elif case == 'reconstructed': proof['reconstructed_version'] = '1'*64
    elif case == 'inventory': proof['file_inventory_sha256'] = '1'*64
    save_json_new(folder/'review.json', review)
    save_json_new(folder/'freeze-authorization.json', {'reproduction': proof})
    files = {p.name: digest(p.read_bytes()) for p in folder.iterdir() if p.name != 'manifest.json'}
    body = {'schema': 'hts-dataset-1', 'metadata': {'purpose': 'frozen_operational_derivation', 'parent_version': parent}, 'files': files}
    (folder/'manifest.json').write_text(json.dumps({**body, 'version': identity(body)}), encoding='utf-8')
    save_idf_documents(idf, table, descriptor, execution)
    if case == 'valid':
        assert validate_training_idf_contract(folder, idf)['contract_and_input_binding'] == 'verified'
    else:
        with pytest.raises(ValueError, match='pai de congelamento'):
            validate_training_idf_contract(folder, idf)


@pytest.mark.parametrize('case,fragment', [
    ('input', 'input_identity'), ('seed', 'config'), ('outside_train', 'training_sources'),
    ('revision', 'training_sources'), ('source_hash', 'training_sources'), ('tf', 'idf.tf'),
    ('normalization', 'vector_normalization'), ('formula', 'formula'), ('df_zero', 'count'),
    ('df_boolean', 'count'), ('df_above_n', 'df excede'), ('n_boolean', 'n_docs'), ('n_wrong', 'n_docs'),
    ('unknown_df_boolean', 'unknown_df'), ('unknown_df', 'unknown_df'), ('pipeline', 'pipeline'),
    ('purpose', 'finalidade'), ('allowed_split', 'allowed_split'), ('attestation', 'atestado'),
    ('execution_version', 'versão'), ('execution_platform', 'platform'), ('timestamp', 'timestamp'),
])
def test_idf_rehashed_incompatible_contract_rejected(idf_documents, case, fragment):
    from hts_core.adapters.idf_contract import validate_training_idf_contract
    folder, idf, table, descriptor, execution = idf_documents
    if case == 'input': descriptor['input_identity'] = '0'*64
    elif case == 'seed': descriptor['config']['seed'] += 1
    elif case == 'outside_train': descriptor['training_sources'][0]['id'] = 's-validation'
    elif case == 'revision': descriptor['training_sources'][0]['revision'] += 1
    elif case == 'source_hash': descriptor['training_sources'][0]['raw_sha256'] = '0'*64
    elif case == 'tf': table['tf'] = 'binary'
    elif case == 'normalization': table['vector_normalization'] = 'l2_precomputed'
    elif case == 'formula': table['formula'] = 'log(N/df)'
    elif case == 'df_zero': table['df']['esfera'] = 0
    elif case == 'df_boolean': table['df']['esfera'] = True
    elif case == 'df_above_n': table['df']['esfera'] = 2
    elif case == 'n_boolean': table['n_docs'] = True
    elif case == 'n_wrong': table['n_docs'] = 2
    elif case == 'unknown_df_boolean': table['unknown_df'] = False
    elif case == 'unknown_df': table['unknown_df'] = 1
    elif case == 'pipeline': descriptor['pipeline']['stopwords'] = ['mutated']
    elif case == 'purpose': descriptor['purpose'] = 'other'
    elif case == 'allowed_split': descriptor['allowed_split'] = 'validation'
    elif case == 'attestation': descriptor['construction_attestation'] = 1
    elif case == 'execution_version': execution['dataset_version'] = '1'*64
    elif case == 'execution_platform': execution['platform'] = True
    elif case == 'timestamp': execution['constructed_utc'] = '2026-10-25T00:00:00'
    save_idf_documents(idf, table, descriptor, execution)
    with pytest.raises(ValueError, match=fragment):
        validate_training_idf_contract(folder, idf, table['version'])


@pytest.mark.parametrize('document', ['idf.json', 'construction.json', 'execution.json'])
@pytest.mark.parametrize('mutation', ['missing_file', 'missing_field', 'unknown_field'])
def test_idf_schema_and_execution_required(idf_documents, document, mutation):
    from hts_core.adapters.idf_contract import validate_training_idf_contract
    folder, idf, table, descriptor, execution = idf_documents
    save_idf_documents(idf, table, descriptor, execution)
    path = idf/document
    if mutation == 'missing_file':
        path.unlink()
    else:
        body = read_json(path)
        if mutation == 'missing_field': body.pop(next(iter(body)))
        else: body['unknown'] = 'not permitted'
        path.write_text(json.dumps(body), encoding='utf-8')
    with pytest.raises((ValueError, FileNotFoundError)):
        validate_training_idf_contract(folder, idf)


@pytest.mark.parametrize('case', ['serialized_bytes', 'body_without_rehash', 'source_bytes'])
def test_idf_bytes_and_integrity(idf_documents, case):
    from hts_core.adapters.idf_contract import validate_training_idf_contract
    folder, idf, table, descriptor, execution = idf_documents
    save_idf_documents(idf, table, descriptor, execution)
    if case == 'source_bytes':
        (folder/'train.raw').write_bytes(b'tampered')
    elif case == 'body_without_rehash':
        table['df'] = {'other': 1}
        (idf/'idf.json').write_text(json.dumps(table), encoding='utf-8')
    else:
        with (idf/'idf.json').open('ab') as stream: stream.write(b' ')
    with pytest.raises(ValueError):
        validate_training_idf_contract(folder, idf)


def test_idf_positive_has_explicit_partial_lexical_scope(idf_documents):
    from hts_core.adapters.idf_contract import validate_training_idf_contract
    folder, idf, table, descriptor, execution = idf_documents
    save_idf_documents(idf, table, descriptor, execution)
    result = validate_training_idf_contract(folder, idf, table['version'])
    assert result['integrity'] == result['contract_and_input_binding'] == 'verified'
    assert result['lexical_recomputation'] == 'not_executed'
    assert result['current_runtime_producer_equivalence'] == 'not_checked'
    assert result['prior_lexical_recomputation_reused_as_current'] is False


@pytest.mark.parametrize('field,value', [('rubric_id', {'invalid': 'object'}), ('procedure_id', True),
    ('shared_dependencies', [None, 123]), ('reason', True), ('evidence_ref', {'not': 'a_reference'}),
    ('rubric_id', '  '), ('shared_dependencies', ['a', 'a']), ('reason', '  '), ('records', {}),
    ('pair_id', None), ('source_text_sha256', 'not a hash')])
def test_annotation_audit_type_regressions(artificial, config, field, value):
    _, data, bundle = artificial
    (bundle if field in bundle else bundle['records'][0])[field] = value
    with pytest.raises(ValueError):
        annotation_examples(bundle, data, config, 'train')


@pytest.mark.parametrize('origin,relationship', [('human_independent', 'same_generator'),
    ('automated_weak', 'artificial_fixture'), ('generator_dependent', 'independent_declared'),
    ('artificial_fixture', 'shared')])
def test_annotation_origin_contradictions(artificial, config, origin, relationship):
    _, data, bundle = artificial
    bundle.update(origin=origin, generator_relationship=relationship)
    with pytest.raises(ValueError, match='contraditória'):
        annotation_examples(bundle, data, config, 'train')


def test_annotation_counts_text_duplicates_and_split_audit(artificial, config):
    _, data, bundle = artificial
    original = bundle['records'][0]
    duplicate_pair = deepcopy(data['pairs'][0]); duplicate_pair['id'] = 'another-pair'
    data['pairs'].append(duplicate_pair); data['components']['another-pair'] = data['components']['p-train']
    duplicate = deepcopy(original); duplicate['pair_id'] = 'another-pair'
    bundle['records'].append(duplicate)
    other = {**original, **{key: original[key].replace('train', 'validation') for key in ('pair_id', 'source_id', 'source_sentence_id', 'suspect_sentence_id')}}
    bundle['records'].append(other)
    rows, counts = annotation_examples(bundle, data, config, 'train')
    assert len(rows) == 2 and counts['labeled'] == 3 and counts['other_split'] == 1
    assert counts['unique_labeled_text_pairs_selected_split'] == 1
    assert counts['repeated_text_pairs_all_records'] == 2
    assert counts['by_split']['validation']['labeled'] == 1
    duplicate['target'] = .25
    with pytest.raises(ValueError, match='conflitantes'):
        annotation_examples(bundle, data, config, 'train')


@pytest.mark.parametrize('status', ['ambiguous', 'excluded'])
def test_annotation_unlabeled_and_test_storage_only(artificial, config, status):
    _, data, bundle = artificial
    row = bundle['records'][0]
    for field in ('pair_id', 'source_id', 'source_sentence_id', 'suspect_sentence_id'):
        row[field] = row[field].replace('train', 'test')
    row.update(status=status, target=None)
    outputs, counts = annotation_examples(bundle, data, config, 'test', audit_only=True)
    assert outputs == [] and counts[status] == 1
    with pytest.raises(PermissionError):
        annotation_examples(bundle, data, config, 'test')


def test_import_preserves_exact_original_bytes_and_declares_evidence_scope(artificial, config, tmp_path):
    import base64
    _, data, bundle = artificial
    bundle.update(origin='automated_weak', generator_relationship='shared')
    raw = json.dumps(bundle, ensure_ascii=False, indent=3).replace('\n', '\r\n').encode('utf-8')
    path = tmp_path/'original.json'; path.write_bytes(raw)
    receipt = import_annotations(path, tmp_path/'receipt.json', data, config, 'train')
    assert receipt['original_bytes_sha256'] == digest(raw)
    assert base64.b64decode(read_json(tmp_path/'receipt.json')['original_bytes_base64']) == raw
    assert receipt['evidence_reference_verification'] == 'declared_strings_not_resolved_or_content_verified'
    assert receipt['eligible'] == 1 and receipt['status'] == 'validated_not_scientifically_released'
    with pytest.raises(FileExistsError):
        import_annotations(path, tmp_path/'receipt.json', data, config, 'train')


def test_semantic_axes_separate_contradiction_from_unrelated(artificial, config):
    _, data, bundle = artificial
    bundle['schema'] = 'hts-annotations-2'
    row = bundle['records'][0]
    row['semantic_axes'] = {'thematic_overlap': 'strong', 'propositional_relation': 'contradiction',
                            'shared_content': 'partial', 'context': 'sufficient'}
    assert annotation_examples(bundle, data, config, 'train')[0][0]['target'] == .75
    row['target'] = 1
    with pytest.raises(ValueError, match='contradição'):
        annotation_examples(bundle, data, config, 'train')
    row['target'] = .5; row['semantic_axes']['context'] = 'insufficient'
    with pytest.raises(ValueError, match='insuficiente'):
        annotation_examples(bundle, data, config, 'train')
    row.update(status='ambiguous', target=None)
    assert annotation_examples(bundle, data, config, 'train')[0] == []


def test_semantic_axes_maximum_requires_compatible_relation(artificial, config):
    _, data, bundle = artificial
    bundle['schema'] = 'hts-annotations-2'
    row = bundle['records'][0]
    row['target'] = 1
    row['semantic_axes'] = {'thematic_overlap': 'strong', 'propositional_relation': 'uncertain',
                            'shared_content': 'equivalent', 'context': 'sufficient'}
    with pytest.raises(ValueError, match='nota 1'):
        annotation_examples(bundle, data, config, 'train')
    row['semantic_axes']['propositional_relation'] = 'compatible'
    assert annotation_examples(bundle, data, config, 'train')[0][0]['target'] == 1


def test_h3_joint_acceptance_failure_denominator_and_memory_clock():
    from hts_core.domain.experiments import latency_acceptance
    attempts = [{'status': 'ok', 'seconds': .01}] + [{'status': 'timeout', 'seconds': 30}]*9
    result = latency_acceptance(attempts, 2, 0)
    assert result['accepted'] is False and result['attempts'] == 10 and result['failure_rate'] == .9
    assert latency_acceptance([{'status': 'ok', 'seconds': .2}], 2, 0)['accepted'] is True
    assert latency_acceptance([{'status': 'error', 'seconds': 0}], 2, 0)['successful_seconds'] is None
    clock = iter([10, 10.25]); rss = iter([100, 120])
    measured = measure_fixture(lambda: None, clock=lambda: next(clock), rss_reader=lambda: next(rss))
    assert measured['seconds'] == .25 and measured['rss_snapshots_bytes'] == [100, 120]
    assert 'neither' in measured['rss_scope']


def test_lexical_projection_ignores_unrelated_modules_and_detects_relevant_change():
    from hts_core.adapters.idf_contract import lexical_projection
    a = fixture_pipeline(); b = deepcopy(a)
    b['code']['unrelated/new_module.py'] = '1'*64
    assert lexical_projection(a) == lexical_projection(b)
    b['code']['domain/preprocess.py'] = '2'*64
    assert lexical_projection(a) != lexical_projection(b)


def test_candidate_proposals_are_bound_and_not_training_release(config):
    from hts_core.adapters.experiment_protocol import validate_candidates
    candidate = read_json(CORE/'configs/experiment_candidates_s5a.json')
    assert validate_candidates(candidate, config) == identity(candidate)
    context = context_for(config, 'preflight', candidate)
    changed = deepcopy(candidate); changed['budget']['maximum_wall_seconds'] += 1
    assert context != context_for(config, 'preflight', changed)
    candidate['h1']['features_by_system']['lexical'] = ['synthetic_class']
    with pytest.raises(ValueError):
        validate_candidates(candidate, config)


@pytest.mark.parametrize('path,value', [(['budget', 'maximum_wall_seconds'], True),
    (['budget', 'attempts'], 2), (['siamese', 'dense_dimensions'], [3, 128, 1]),
    (['h1', 'classifier', 'fit_split'], 'test'), (['h3_acceptance', 'maximum_failure_rate'], float('nan')),
    (['h2', 'range'], [False, True]), (['reference_protocol_identity'], '0'*64)])
def test_invalid_candidate_supplement(config, path, value):
    from hts_core.adapters.experiment_protocol import validate_candidates
    candidate = read_json(CORE/'configs/experiment_candidates_s5a.json')
    change_path(candidate, path, value)
    with pytest.raises((ValueError, PermissionError)):
        validate_candidates(candidate, config)


def test_audit_only_import_test_annotations_cannot_create_inference_inputs(artificial, config, tmp_path):
    _, data, bundle = artificial
    bundle.update(origin='automated_weak', generator_relationship='shared')
    for field in ('pair_id', 'source_id', 'source_sentence_id', 'suspect_sentence_id'):
        bundle['records'][0][field] = bundle['records'][0][field].replace('train', 'test')
    path = tmp_path/'test-audit.json'; save_json_new(path, bundle)
    receipt = import_annotations(path, tmp_path/'stored.json', data, config, 'test', audit_only=True)
    assert receipt['eligible'] == 0 and receipt['counts']['by_split']['test']['labeled'] == 1
    assert receipt['coverage']['labeled_sentence_pairs_selected_split'] == 1
    assert receipt['mode'] == 'storage_audit_only_no_model_inputs'
    with pytest.raises(PermissionError):
        import_annotations(path, tmp_path/'forbidden.json', data, config, 'test')


def test_annotation_cli_positive_fixture_and_failure_exit(artificial, config, tmp_path):
    folder, _, bundle = artificial
    bundle.update(origin='automated_weak', generator_relationship='shared')
    protocol = tmp_path/'protocol.json'; annotation = tmp_path/'annotation.json'
    save_json_new(protocol, config); save_json_new(annotation, bundle)
    command = [sys.executable, '-m', 'hts_core.cli', 'experiment', 'import-annotations', '--protocol', str(protocol),
               '--dataset', str(folder), '--annotations', str(annotation), '--split', 'train', '--out', str(tmp_path/'receipt.json')]
    first = subprocess.run(command, capture_output=True, text=True)
    assert first.returncode == 0 and 'validated_not_scientifically_released' in first.stdout
    second = subprocess.run(command, capture_output=True, text=True)
    assert second.returncode == 2 and 'FileExistsError' in second.stderr


def test_idf_rejects_boolean_revision_even_if_equal_to_integer(idf_documents):
    from hts_core.adapters.idf_contract import validate_training_idf_contract
    folder, idf, table, descriptor, execution = idf_documents
    descriptor['training_sources'][0]['revision'] = True
    save_idf_documents(idf, table, descriptor, execution)
    with pytest.raises(ValueError, match='revision'):
        validate_training_idf_contract(folder, idf)


def test_measurement_clock_failure_does_not_leak_global_tracer():
    import tracemalloc
    with pytest.raises(ZeroDivisionError):
        measure_fixture(lambda: None, clock=lambda: 1/0)
    assert tracemalloc.is_tracing() is False


def test_preflight_uses_shared_idf_contract_and_records_failed_attempt(idf_documents, config, tmp_path):
    folder, idf, table, descriptor, execution = idf_documents
    descriptor['input_identity'] = '0'*64
    save_idf_documents(idf, table, descriptor, execution)
    config['dataset']['idf_identity'] = table['version']
    protocol = tmp_path/'bad-protocol.json'; save_json_new(protocol, config)
    with pytest.raises(ValueError, match='input_identity'):
        prepare(protocol, folder, idf, tmp_path/'failed')
    event = read_json(tmp_path/'failed/attempts/000-failed.json')
    assert event['state'] == 'failed' and event['details']['error_type'] == 'ValueError'
    assert not (tmp_path/'failed/preflight.json').exists()
