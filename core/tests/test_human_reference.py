"""Synthetic fixtures only: these judgments are never human study responses."""
from copy import deepcopy
import importlib.util
import json
from pathlib import Path
import zipfile

import pytest

from hts_core.application import human_reference as app
from hts_core.domain.human_reference import agreement_and_consensus
from hts_core.application.human_reference import validate_submission
from hts_core.adapters.dataset_store import identity

CORE = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('human_prepare_cli', CORE / 'scripts/prepare_s5c_reference.py')
assert spec and spec.loader
cli = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cli)


def plan():
    return {**deepcopy(app.HUMAN_DEFAULTS), 'rubric_sha256': app.sha(CORE / 'assets/rubrics/s5c-human-01.md'),
            'frozen_inputs_identity': '0' * 64}


def dataset():
    sources, pairs = [], []
    for cell in range(16):
        sid = f's{cell}'
        sources.append({'id': sid, 'split': 'test', 'sentences': [
            {'id': f'a{cell}-{n}', 'semantic': f'Fonte artificial {cell}, sentença {n}.'} for n in range(8)]})
        for p in range(6):
            pairs.append({'id': f'p{cell}-{p}', 'source_id': sid, 'split': 'test',
                          'method': f'm{cell // 4}', 'severity': cell % 4,
                          'sentences': [{'id': f'b{cell}-{p}', 'semantic': f'Suspeito artificial {cell}, versão {p}.',
                                         'ancestors': [{'source_id': sid, 'sentence_id': f'a{cell}-{p}'}]}]})
    return {'sources': sources, 'pairs': pairs, 'manifest': {'version': plan()['dataset_version']}}


def packet(assessor='A1'):
    return app.blind_packet(app.select_human_pairs(dataset(), plan()), plan(), assessor, 'Rubrica artificial de teste.')


def submission(pack):
    return {'schema': 'hts-human-response-1', 'campaign_identity': pack['campaign_identity'],
            'packet_identity': pack['packet_identity'], 'assessor_id': pack['assessor_id'], 'complete': True,
            'completed_at': '2026-10-27T09:00:00+00:00',
            'declaration': {'human': True, 'independent': True, 'no_ai': True, 'no_collaboration': True,
                            'participated_in_creation': False, 'project_relationship': 'Fixture, não pessoa real.',
                            'prior_exposure': 'none', 'exposure_details': ''},
            'records': [{'observation_id': item['observation_id'],
                         'H1': {'status': 'labeled', 'target': 'parafrase', 'reason': 'Justificativa artificial.',
                                'quote_a': item['text_a'], 'quote_b': item['text_b']},
                         'H2': {'status': 'labeled', 'target': .75, 'reason': 'Justificativa artificial.',
                                'quote_a': item['text_a'], 'quote_b': item['text_b'],
                                'axes': {'thematic_overlap': 'strong', 'propositional_relation': 'compatible',
                                         'shared_content': 'predominant', 'context': 'sufficient'}}}
                        for item in pack['items']]}


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')
    return path


def test_selection_96_is_deterministic_deduplicated_and_has_all_cells():
    data = dataset()
    selected = app.select_human_pairs(data, plan())
    data['sources'].reverse()
    data['pairs'].reverse()
    for source in data['sources']:
        source['sentences'].reverse()
    assert app.select_human_pairs(data, plan()) == selected
    assert len(selected) == len({r['observation_id'] for r in selected}) == 96
    assert len({(r['source_text_sha256'], r['suspect_text_sha256']) for r in selected}) == 96
    from collections import Counter
    cells = Counter((r['method'], r['severity']) for r in selected if r['stratum'] == 'method_severity')
    assert len(cells) == 16 and set(cells.values()) == {5}
    crosses = [r for r in selected if r['stratum'] == 'nonancestral_cross']
    assert len(crosses) == 16 and not any(r['ancestral_pair'] for r in crosses)
    extra = deepcopy(data['pairs'][0]); extra.update(id='train', split='train')
    data['pairs'].append(extra)
    assert app.select_human_pairs(data, plan()) == selected


@pytest.mark.parametrize('fault', ['cell', 'insufficient', 'split'])
def test_selection_rejects_bad_coverage_without_expansion(fault):
    data = dataset()
    if fault == 'cell':
        data['pairs'] = [p for p in data['pairs'] if p['method'] != 'm0']
    elif fault == 'split':
        data['sources'][0]['split'] = 'train'
    else:
        for p in data['pairs']:
            p['sentences'][0]['semantic'] = 'Mesmo texto.'
        for s in data['sources']:
            for row in s['sentences']:
                row['semantic'] = 'Fonte repetida.'
    with pytest.raises(ValueError):
        app.select_human_pairs(data, plan())


def test_blind_packets_share_ids_differ_in_order_and_have_only_public_fields():
    a, b = packet(), packet('A2')
    assert a['items'] != b['items']
    assert {i['observation_id'] for i in a['items']} == {i['observation_id'] for i in b['items']}
    assert a['campaign_identity'] == b['campaign_identity'] and a['packet_identity'] != b['packet_identity']
    assert set(a) == {'schema', 'assessor_id', 'campaign_identity', 'packet_identity', 'rubric', 'items'}
    assert all(set(row) == {'observation_id', 'text_a', 'text_b'} for row in a['items'])
    a['items'][0]['text_a'] = '</script><img src=x onerror=alert(1)> & \u2028'
    html = app.render_packet(a)
    assert '</script><img' not in html and '\\u003c/script' in html and '\\u2028' in html


@pytest.mark.parametrize('key,value', [('seed', True), ('expected_cells', 15), ('target_observations', 24),
                                      ('test_predictions_authorized', 0), ('extra_field', 1), ('rubric_sha256', 'x')])
def test_plan_rejects_altered_fields(key, value):
    p = plan(); p[key] = value
    with pytest.raises(ValueError):
        app.validate_human_plan(p)


def test_check_only_and_missing_authorization_never_open_dataset(tmp_path, monkeypatch, capsys):
    p = write(tmp_path / 'plan.json', plan())
    def forbidden(*args, **kwargs):
        raise AssertionError('dataset must remain closed')
    monkeypatch.setattr(app, 'inspect_dataset', forbidden)
    cli.main(['--plan', str(p), '--check-plan-only', '--dataset', 'does-not-exist'])
    assert json.loads(capsys.readouterr().out)['labels_produced'] == 0
    with pytest.raises(SystemExit) as error:
        cli.main(['--plan', str(p), '--out', str(tmp_path / 'never')])
    assert error.value.code == 2 and not (tmp_path / 'never').exists()


@pytest.mark.parametrize('fault', ['rubric', 'H1', 'H2'])
def test_preparation_inputs_reject_changed_protocol_or_rubric(fault, tmp_path):
    p = plan()
    paths = {'H1': CORE / 'configs/experiment_s5b.r3.json', 'H2': CORE / 'configs/experiment_s5b.r4.json'}
    rubric = CORE / 'assets/rubrics/s5c-human-01.md'
    if fault == 'rubric':
        rubric = tmp_path / 'rubric'; rubric.write_text('modificada')
    else:
        value = json.loads(paths[fault].read_text()); value['seed'] = 1
        paths[fault] = write(tmp_path / 'bad.json', value)
    with pytest.raises(ValueError):
        app.validate_preparation_inputs(p, rubric, CORE / 'configs/experiment_s5a.json', paths['H1'], paths['H2'])


@pytest.fixture
def campaign(tmp_path, monkeypatch):
    root = tmp_path / 'repo'; core = root / 'core'; core.mkdir(parents=True)
    # Use real renderer assets, but frozen scientific fixtures, never real test pairs.
    (core / 'assets').symlink_to(CORE / 'assets', target_is_directory=True)
    monkeypatch.setattr(app, 'CORE', core)
    frozen_file = core / 'frozen-model'; frozen_file.write_text('model fixture')
    frozen = {'schema': 'hts-s5c-frozen-inputs-1', 'files': {'core/frozen-model': app.sha(frozen_file)}}
    p = plan(); p['frozen_inputs_identity'] = identity(frozen)
    monkeypatch.setattr(app, 'validate_preparation_inputs', lambda *args: app.validate_human_plan(args[0]))
    monkeypatch.setattr(app, 'inspect_dataset', lambda *args: dataset())
    instruction = core / 'instruction'; instruction.write_text('Synthetic authorization fixture.')
    auth = {'action': 'prepare_blind_human_reference', 'plan_identity': identity(p),
            'user_instruction_file': str(instruction), 'user_instruction_sha256': app.sha(instruction),
            'predictions_authorized': False}
    args = [p, CORE / 'assets/rubrics/s5c-human-01.md', write(core / 'reference.json', {}), '', '',
            write(core / 'authorization.json', auth), '', write(core / 'frozen.json', frozen), core / 'campaign']
    return args


@pytest.mark.parametrize('fault', ['authorization', 'instruction', 'inventory', 'model'])
def test_preparation_rejects_drift_before_dataset(campaign, monkeypatch, fault):
    args = campaign
    if fault == 'authorization':
        auth = json.loads(args[5].read_text()); auth['predictions_authorized'] = True; write(args[5], auth)
    elif fault == 'instruction':
        Path(json.loads(args[5].read_text())['user_instruction_file']).write_text('changed')
    elif fault == 'inventory':
        frozen = json.loads(args[7].read_text()); frozen['files']['core/frozen-model'] = '0' * 64; write(args[7], frozen)
    else:
        (args[8].parent / 'frozen-model').write_text('changed')
    def forbidden(*args, **kwargs):
        raise AssertionError('drift must be caught before opening dataset')
    monkeypatch.setattr(app, 'inspect_dataset', forbidden)
    with pytest.raises((ValueError, PermissionError)):
        app.prepare_human_reference(*args)
    assert not args[8].exists()


def test_prepare_zip_and_import_synthetic_answers_preserves_raw_and_does_not_freeze(campaign):
    result = app.prepare_human_reference(*campaign)
    assert result['selected'] == 96 and not result['predictions'] and result['human_answers'] == 0
    directory = campaign[8]
    answers = []
    for assessor in ('A1', 'A2'):
        with zipfile.ZipFile(directory / (assessor + '.zip')) as z:
            assert z.testzip() is None
            assert set(z.namelist()) == {'avaliacao.html', 'rubrica.md', 'LEIA-ME.txt', 'integridade.json'}
        pack = json.loads((directory / 'packets' / (assessor + '.json')).read_text())
        answers.append(write(directory.parent / (assessor + '-fixture.json'), submission(pack)))
    imported = app.audit_human_results(directory, answers, directory.parent / 'imported')
    assert imported['human_independence_declared'] and not imported['identity_authenticated']
    assert not imported['reference_frozen'] and not imported['predictions']
    assert (directory.parent / 'imported/raw-1.json').read_bytes() == answers[0].read_bytes()
    with pytest.raises(FileExistsError):
        app.prepare_human_reference(*campaign)
    invalid = json.loads(answers[1].read_text()); invalid['assessor_id'] = 'A1'; write(answers[1], invalid)
    with pytest.raises(ValueError):
        app.audit_human_results(directory, answers, directory.parent / 'failed')
    assert (directory.parent / 'failed/raw-2.json').read_bytes() == answers[1].read_bytes()
    assert (directory.parent / 'failed/failure.json').exists()
    (directory / 'A1/avaliacao.html').write_text('tampered')
    with pytest.raises(ValueError, match='alterado'):
        app.audit_human_results(directory, answers, directory.parent / 'tampered')


@pytest.mark.parametrize('fault', ['draft', 'assessor', 'packet', 'campaign', 'missing', 'duplicate', 'extra',
                                  'bool', 'anchor', 'quote', 'reason', 'axes', 'context', 'one', 'conflict',
                                  'time', 'timezone', 'declaration', 'exposure'])
def test_submission_rejects_invalid_answers(fault):
    p = packet(); value = submission(p); first = value['records'][0]
    if fault == 'draft': value['complete'] = False
    elif fault in ('assessor', 'packet', 'campaign'): value[fault + '_id' if fault == 'assessor' else fault + '_identity'] = 'changed'
    elif fault == 'missing': value['records'].pop()
    elif fault == 'duplicate': value['records'][1] = deepcopy(first)
    elif fault == 'extra': first['score_system'] = .8
    elif fault == 'bool': first['H2']['target'] = True
    elif fault == 'anchor': first['H2']['target'] = .4
    elif fault == 'quote': first['H1']['quote_a'] = 'Trecho inexistente'
    elif fault == 'reason': first['H1']['reason'] = ' '
    elif fault == 'axes': first['H2']['axes']['context'] = ''
    elif fault == 'context': first['H2']['axes']['context'] = 'insufficient'
    elif fault == 'one': first['H2']['target'] = 1
    elif fault == 'conflict': first['H2']['axes'].update(shared_content='equivalent', propositional_relation='contradiction')
    elif fault == 'time': value['completed_at'] = 'fake'
    elif fault == 'timezone': value['completed_at'] = '2026-10-27T09:00:00'
    elif fault == 'declaration': value['declaration']['human'] = 'true'
    elif fault == 'exposure': value['declaration']['prior_exposure'] = 'yes'
    with pytest.raises(ValueError):
        validate_submission(value, p)


def test_ambiguity_and_honest_exposure_remain_recorded_without_independence_claim():
    p = packet(); value = submission(p)
    for task in ('H1', 'H2'):
        value['records'][0][task].update(status='ambiguous', target=None, quote_a='', quote_b='')
    value['declaration'].update(prior_exposure='yes', exposure_details='Exemplo artificial já conhecido.')
    result = validate_submission(value, p)
    assert not result['human_independence_declared'] and result['counts']['H1']['ambiguous'] == 1


def test_known_kappa_spearman_ties_consensus_and_undefined_cases():
    a = submission(packet()); b = deepcopy(a); b['assessor_id'] = 'A2'
    a['records'] = a['records'][:4]; b['records'] = b['records'][:4]
    for n, (left, right) in enumerate(zip(a['records'], b['records'])):
        left['H1']['target'] = ['copia_exata','copia_exata','parafrase','parafrase'][n]
        right['H1']['target'] = ['copia_exata','parafrase','parafrase','parafrase'][n]
        left['H2']['target'] = [0,.5,.5,1][n]; right['H2']['target'] = [1,.5,.5,0][n]
    result = agreement_and_consensus(a, b)
    assert result['H1_kappa']['value'] == pytest.approx(.5)
    assert result['H2_spearman']['value'] == pytest.approx(-1)
    assert result['H2_tied_observations'] == [2, 2]
    disagreement = [r for r in result['consensus'] if r['H1']['target'] is None]
    assert len(disagreement) == 1 and disagreement[0]['H2']['target'] == .5
    for value in (a, b):
        for row in value['records']:
            row['H1']['target'] = 'parafrase'; row['H2']['target'] = .5
    result = agreement_and_consensus(a, b)
    assert result['H2_tied_observations'] == [4, 4]
    for key in ('H1_kappa', 'H2_spearman'):
        assert result[key]['value'] is None and result[key]['reason']
    for value in (a, b):
        for row in value['records']:
            for task in ('H1', 'H2'): row[task].update(status='excluded', target=None)
    result = agreement_and_consensus(a, b)
    assert result['H1_kappa']['n'] == result['H2_spearman']['n'] == 0
    assert all(row['H1']['target'] is row['H2']['target'] is None for row in result['consensus'])
