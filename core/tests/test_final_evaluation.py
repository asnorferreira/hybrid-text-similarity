"""Artificial fixtures only; no scientific test pairs or human answers."""
import pytest

from hts_core.adapters.dataset_store import identity, read_json
from hts_core.application import final_evaluation as final
from hts_core.application import human_reference as human
from hts_core.domain.experiments import ModelInput
from tests.test_human_reference import campaign, dataset, submission, write  # noqa: F401


@pytest.fixture
def frozen(campaign, monkeypatch):  # noqa: F811 - imported pytest fixture, injected by name
    human.prepare_human_reference(*campaign)
    directory = campaign[8]
    root = directory.parents[1]
    answers = []
    for assessor in ('A1', 'A2'):
        value = submission(read_json(directory / 'packets' / (assessor + '.json')))
        for i, row in enumerate(sorted(value['records'], key=lambda item: item['observation_id'])):
            row['H1']['target'] = final.CLASSES[i % 4]
            row['H2']['target'] = .25 if i % 2 else .75
        answers.append(write(directory.parent / (assessor + '-FIXTURE.json'), value))
    imported = directory.parent / 'imported'
    human.audit_human_results(directory, answers, imported)
    plan = write(directory.parent / 'evaluation.json', {
        'schema': 'hts-s5c-evaluation-plan-1', 'minimum_valid': 8,
        'scope': 'finite_dependent_human_subset_no_population_inference',
        'dataset': 'core/artificial-dataset', 'reference_protocol': 'core/reference.json',
    })
    monkeypatch.setattr(final, 'inspect_dataset', lambda *args: dataset())
    monkeypatch.setattr(final, 'validate_model_plan', lambda *args: None)
    dest = directory.parent / 'frozen-reference.json'
    final.freeze_reference(root, directory, imported, plan, dest)
    instruction = write(root / 'instruction.json', {'instruction': 'Artificial evaluation fixture authorization.'})
    auth = write(root / 'authorization.json', {'action': 'evaluate_final_once', 'predictions_authorized': True,
        'reference_identity': read_json(dest)['identity'], 'split': 'test',
        'user_instruction_file': 'instruction.json', 'user_instruction_sha256': human.sha(instruction)})
    return root, directory, imported, plan, dest, auth


def predictor_factory(*args):
    def predict(inputs):
        assert type(inputs) is ModelInput
        return {'H1': {s: 'parafrase' for s in final.SYSTEMS},
                'H2': {'sbert': .5, 'siamese': .5}, 'P1': {'raw': .5, 'probability': .5, 'q5v2_derived': 0}}
    return predict


def test_frozen_fixture_evaluates_once_and_constant_correlations_are_null(frozen):
    root, directory, _, _, reference, auth = frozen
    output = root / 'evaluation-fixture'
    result = final.evaluate(reference, auth, human.sha(auth), root, output, predictor_factory=predictor_factory)
    assert result['status'] == 'complete' and result['selected'] == 96
    metrics = read_json(output / 'metrics.json')
    assert metrics['H1']['semantic']['n'] == 96
    assert metrics['H1']['semantic']['macro_f1'] == pytest.approx(.1)
    assert metrics['H2']['sbert']['spearman']['value'] is None
    assert metrics['H2']['sbert']['spearman']['reason'] == 'variância zero'
    assert metrics['P1']['raw']['n'] == 96
    assert len(list((output / 'predictions').glob('*.json'))) == 96
    assert len(metrics['strata']['method']) == 4
    with pytest.raises(FileExistsError):
        final.evaluate(reference, auth, human.sha(auth), root, root / 'other-output', predictor_factory=predictor_factory)
    assert final.claim_path(root, read_json(reference)).exists()


@pytest.mark.parametrize('fault', ['raw', 'agreement', 'model', 'independence', 'packet', 'plan'])
def test_freeze_refuses_drift_and_missing_independence(frozen, fault):
    root, directory, imported, plan, _, _ = frozen
    target = {'raw': imported / 'raw-1.json', 'agreement': imported / 'agreement.json',
              'model': root / 'core/frozen-model', 'packet': directory / 'packets/A1.json'}
    if fault in target:
        target[fault].write_bytes(target[fault].read_bytes() + b' ')
    elif fault == 'independence':
        data = read_json(imported / 'import-receipt.json')
        data['human_independence_declared'] = False
        write(imported / 'import-receipt.json', data)
    else:
        data = read_json(plan)
        data['minimum_valid'] = 1
        write(plan, data)
    with pytest.raises((ValueError, PermissionError)):
        final.freeze_reference(root, directory, imported, plan, root / 'bad-reference.json')
    assert not (root / 'bad-reference.json').exists()


@pytest.mark.parametrize('fault', ['unfrozen', 'identity', 'eligible', 'inventory', 'auth-hash',
                                   'auth-action', 'auth-ref', 'auth-split', 'instruction', 'auth-bool'])
def test_guards_refuse_before_predictor_construction(frozen, fault):
    root, directory, _, _, reference, auth = frozen
    digest = human.sha(auth)
    if fault in ('unfrozen', 'identity', 'eligible', 'inventory'):
        data = read_json(reference)
        if fault == 'unfrozen':
            data['reference_frozen'] = False
        elif fault == 'identity':
            data['identity'] = '0' * 64
        elif fault == 'eligible':
            data['eligibility']['H2']['n'] = 999
        else:
            (root / 'core/frozen-model').write_text('modified')
        if fault != 'identity':
            data['identity'] = identity({k: v for k, v in data.items() if k != 'identity'})
        write(reference, data)
    elif fault == 'instruction':
        (root / 'instruction.json').write_text('changed')
    elif fault == 'auth-hash':
        digest = '0' * 64
    else:
        data = read_json(auth)
        key, value = {'auth-action': ('action', 'training'), 'auth-ref': ('reference_identity', '0' * 64),
                      'auth-split': ('split', 'validation'), 'auth-bool': ('predictions_authorized', 1)}[fault]
        data[key] = value
        write(auth, data)
        digest = human.sha(auth)
    def forbidden(*args):
        raise AssertionError('guard failed before model load')
    with pytest.raises((ValueError, PermissionError)):
        final.evaluate(reference, auth, digest, root, root / 'bad-output', predictor_factory=forbidden)
    assert not final.claim_path(root, read_json(reference)).exists()


def test_failure_preserves_partial_predictions_and_claim(frozen):
    root, directory, _, _, reference, auth = frozen
    calls = []
    def factory(*args):
        def predict(inputs):
            calls.append(inputs)
            if len(calls) == 2:
                raise RuntimeError('artificial interrupted operation')
            return predictor_factory()(inputs)
        return predict
    out = root / 'failed-fixture'
    with pytest.raises(RuntimeError):
        final.evaluate(reference, auth, human.sha(auth), root, out, predictor_factory=factory)
    assert len(list((out / 'predictions').glob('*.json'))) == 1
    assert read_json(out / 'failure.json')['claim_preserved'] is True
    assert final.claim_path(root, read_json(reference)).exists()


def test_eligibility_does_not_replace_ambiguous_pairs_or_drop_absent_classes():
    rows = [{'H1': {'target': 'parafrase'}, 'H2': {'target': .5}} for _ in range(8)]
    rows.append({'H1': {'target': None}, 'H2': {'target': None}})
    gates = final.eligibility(rows)
    assert gates['H1']['n'] == 8 and gates['H1']['eligible']
    assert len(gates['H1']['absent_classes']) == 3
    assert not gates['H2']['eligible']
    rows[0]['H2']['target'] = .25
    assert final.eligibility(rows)['H2']['eligible']


@pytest.mark.parametrize('path', ['/etc/passwd', '../escape', 'a/../../escape'])
def test_repository_path_escape_is_refused(tmp_path, path):
    with pytest.raises(ValueError):
        final.checked_path(tmp_path, path)


def test_model_added_after_annotations_is_refused(tmp_path):
    plan = {'idf': 'idf.json', 'h2_protocol': 'h2.json', 'platt': 'p1.json',
            'h1': 'classifiers', 'h2_checkpoint': 'h2/selected'}
    with pytest.raises(ValueError, match='absent from preselection'):
        final.validate_model_plan(tmp_path, plan, {}, {})
