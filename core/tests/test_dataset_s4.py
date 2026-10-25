from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

import pytest

from hts_core.adapters.dataset_formats import render
from hts_core.adapters.dataset_llm import generate_candidate, request_spec, validate_cached
from hts_core.adapters.dataset_review import freeze, import_review, prepare_review
from hts_core.adapters.dataset_store import canonical, digest, export_bundle, identity, import_bundle, read_json, read_jsonl, seal, verify_seal, write_json, write_jsonl, write_new
from hts_core.adapters.dataset_validation import evaluation_inputs, validate_data, validate_training_idf
from hts_core.application.dataset_pipeline import build_local, build_training_idf
from hts_core.domain.dataset import edit_characters, reorder_indices, reuse_fraction, source_groups, split_groups
from hts_core.domain.text import clean_extracted, split_sentences

CORE = Path(__file__).resolve().parents[1]


@pytest.fixture(scope='module')
def dataset(tmp_path_factory):
    root = tmp_path_factory.mktemp('s4-development')
    corpus = root/'corpus'
    corpus.mkdir()
    documents = []
    for i in range(20):
        label = chr(97 + i) * 8
        text = ' '.join(f'O {label} descreve fenômenos {label} da região {label} com exemplo {ending}.'
                        for ending in ('primeiro', 'segundo', 'terceiro', 'quarto'))
        filename = f'raw/{i}.wiki'
        write_new(corpus/filename, text.encode())
        documents.append({'pageid': i, 'revid': i + 100, 'title': f'Fixture {i}', 'url': 'https://example.invalid/development',
                          'history_url': 'https://example.invalid/development/history', 'license': 'project-authored-test-fixture',
                          'retrieved_at': '2026-10-24T00:00:00+00:00', 'file': filename, 'sha256': digest(text.encode())})
    write_json(corpus/'manifest.json', {'documents': documents})
    config = read_json(CORE/'configs/dataset_pilot.json')
    config.update(segment_sentences=4, themes={f'Fixture {i}': str(i % 2) for i in range(20)})
    path = root/'dataset'
    build_local(config, corpus, path)
    return path


def clone_unsealed(dataset, tmp_path):
    destination = tmp_path/'candidate'
    destination.mkdir(parents=True)
    for name in verify_seal(dataset)['files']:
        write_new(destination/name, (dataset/name).read_bytes())
    return destination


def replace_jsonl(folder, name, values):
    # Adulteração deliberada de fixture, nunca de evidência ou dataset real.
    (folder/name).write_bytes(b''.join(canonical(v) for v in values))


def test_group_split_keeps_families_and_hamilton_counts():
    groups = {str(i): str(i) for i in range(20)}
    assigned = split_groups(groups, 7)
    assert [sum(v == s for v in assigned.values()) for s in ('train', 'validation', 'test')] == [14, 3, 3]
    groups['duplicate'] = '0'
    assigned = split_groups(groups, 7)
    assert assigned['duplicate'] == assigned['0']


def test_grouping_same_page_exact_and_near_links():
    sources = [{'id': 'a', 'provider': 'wiki', 'pageid': 1, 'text': 'um dois tres quatro cinco seis sete'},
               {'id': 'b', 'provider': 'wiki', 'pageid': 1, 'text': 'outro texto'},
               {'id': 'c', 'provider': 'wiki', 'pageid': 2, 'text': 'um dois tres quatro cinco seis sete'}]
    groups, alerts = source_groups(sources)
    assert groups == {'a': 'a', 'b': 'a', 'c': 'a'}
    assert {a['reason'] for a in alerts} == {'page', 'exact'}
    near = [{'id': 'a', 'provider': 'wiki', 'pageid': 1, 'text': 'um dois tres quatro cinco seis sete'},
            {'id': 'b', 'provider': 'wiki', 'pageid': 2, 'text': 'um dois tres quatro cinco seis sete oito'}]
    assert source_groups(near, threshold=.7)[0] == {'a': 'a', 'b': 'a'}
    assert source_groups(near, threshold=.8)[0] == {'a': 'a', 'b': 'b'}


def test_effective_edits_and_no_fake_semantic_target():
    output, record = edit_characters('A abc xyz!', 1, 7)
    assert output == 'A xxx zxx!'
    assert record['eligible'] == record['realized_count'] == 6
    assert all(op['before'] != op['after'] for op in record['operations'])
    assert edit_characters('ABC 12!', .3, 7)[1]['realized_count'] == 0
    with pytest.raises(ValueError):
        edit_characters('abc', 0, 7)


def test_multiorigin_fraction_counts_a_sentence_once():
    rows = [{'ancestors': [{'source_id': 'A'}, {'source_id': 'B'}]},
            {'ancestors': [{'source_id': 'A'}, {'source_id': 'A'}]},
            {'ancestors': [{'source_id': 'C'}]}]
    assert reuse_fraction(rows, 'A') == {'numerator': 2, 'denominator': 3}
    assert reuse_fraction(rows, 'B') == {'numerator': 1, 'denominator': 3}
    with pytest.raises(ValueError):
        reuse_fraction([], 'A')


def test_permutation_and_hashseed_processes():
    code = "import json; from hts_core.domain.dataset import reorder_indices, split_groups; print(json.dumps([reorder_indices(6,7),split_groups({str(i):str(i) for i in range(20)},7)],sort_keys=True))"
    outputs = [subprocess.check_output([sys.executable, '-c', code], env={**os.environ, 'PYTHONHASHSEED': seed, 'PYTHONPATH': str(CORE/'src')}) for seed in ('1', '917')]
    assert outputs[0] == outputs[1]
    order = reorder_indices(6, 7)
    assert sorted(order) == [0, 1, 2, 3, 4, 5] and order != [0, 1, 2, 3, 4, 5]


def test_actual_pipeline_and_independent_fraction_oracles(dataset):
    report = validate_data(dataset)
    assert report['sources'] == 20 and report['groups'] == 20
    pairs = read_jsonl(dataset/'pairs.jsonl')
    assert {p['synthetic_type'] for p in pairs} == {'C0', 'C1', 'C2', 'C3', 'C4', 'C7'}
    for p in pairs:
        expected = {'C0': 0, 'C1': 4, 'C2': 4, 'C7': 4}.get(p['synthetic_type'])
        if expected is not None:
            assert p['r'] == {'numerator': expected, 'denominator': 4}
        if p['synthetic_type'] == 'C3':
            assert p['r'] == {'numerator': {'.25': 1, '0.25': 1, '0.5': 2, '0.75': 3}[p['severity']], 'denominator': 4}
        assert all(r['semantic_target'] is None and r['validated_class'] is None for r in p['sentences'])


@pytest.mark.parametrize('corruption', ['source_split', 'patchwork', 'r', 'orphan', 'operation', 'gabarito', 'permutation'])
def test_validator_rejects_deliberate_corruption(dataset, tmp_path, corruption):
    path = clone_unsealed(dataset, tmp_path)
    sources, pairs = read_jsonl(path/'sources.jsonl'), read_jsonl(path/'pairs.jsonl')
    if corruption == 'source_split':
        sources[1].update(pageid=sources[0]['pageid'], split='test' if sources[0]['split'] != 'test' else 'train')
    elif corruption == 'patchwork':
        p = next(p for p in pairs if p['synthetic_type'] == 'C4')
        p['split'] = 'test' if p['split'] != 'test' else 'train'
    elif corruption == 'r':
        pairs[0]['r']['numerator'] += 1
    elif corruption == 'orphan':
        pairs[0]['sentences'][0]['ancestors'][0]['sentence_id'] = 'missing'
    elif corruption == 'operation':
        p = next(p for p in pairs if p['synthetic_type'] == 'C2')
        p['generation']['by_sentence'][0]['realized_count'] += 1
    elif corruption == 'gabarito':
        pairs[0]['sentences'][0]['semantic_target'] = 1.0
    else:
        p = next(p for p in pairs if p['synthetic_type'] == 'C7')
        p['generation']['permutation'] = [0, 0, 0, 0]
    replace_jsonl(path, 'sources.jsonl', sources)
    replace_jsonl(path, 'pairs.jsonl', pairs)
    with pytest.raises(ValueError):
        validate_data(path, sealed=False)


def test_resegmentation_rejected_before_ancestry_is_invented():
    from hts_core.application.dataset_pipeline import sentence_records
    with pytest.raises(ValueError, match='resegmentação'):
        sentence_records('Uma frase. Outra frase.', 'fixture', [[{'source_id': 'A', 'sentence_id': 'a'}]])


@pytest.mark.parametrize('kind', ['txt', 'docx', 'pdf'])
def test_formats_unicode_declared_literal_and_stable(kind):
    from hts_core.adapters.parsers import parse_document
    text = 'A informação chegou. O guarda-chuva é útil. Coração, ação e café.'
    data, _ = render(text, kind)
    assert parse_document('opaque.' + kind, data) == text
    assert render(text, kind)[0] == data


def test_unsupported_pdf_character_rejected_explicitly():
    with pytest.raises(ValueError, match='U\\+'):
        render('Um teste 🐸.', 'pdf')


def test_pdf_retains_greek_in_portuguese_content():
    from hts_core.adapters.parsers import parse_document
    text = 'A palavra δημοκρατία aparece no texto.'
    data, _ = render(text, 'pdf')
    assert parse_document('unicode.pdf', data) == text


def test_manifest_export_import_and_tampering(dataset, tmp_path):
    bundle = tmp_path/'dataset.zip'
    version = export_bundle(dataset, bundle)
    imported = import_bundle(bundle, tmp_path/'restored')
    assert imported['version'] == version
    assert validate_data(tmp_path/'restored')['pairs'] == validate_data(dataset)['pairs']
    with pytest.raises(FileExistsError):
        export_bundle(dataset, bundle)
    with pytest.raises(FileExistsError):
        write_new(tmp_path/'restored/config.json', b'overwrite')
    (tmp_path/'restored/config.json').write_bytes(b'{}')
    with pytest.raises(ValueError, match='hash'):
        verify_seal(tmp_path/'restored')


def test_review_prepared_blank_and_freeze_rejected(dataset, tmp_path):
    review = tmp_path/'review'
    result = prepare_review(dataset, review, 7)
    assert result['items'] > 0 and result['status'] == 'human_pending'
    assert all(not r[k] for r in read_jsonl(review/'items.jsonl') for k in ('decision', 'reason', 'reviewer', 'date'))
    with pytest.raises(ValueError, match='incompleta'):
        import_review(review, review/'responses.csv', tmp_path/'reviewed')
    with pytest.raises(PermissionError, match='piloto'):
        freeze(dataset, review, {'approved': True, 'reference': 'unit fixture'}, tmp_path/'frozen')


def test_idf_uses_only_training_sources_and_changes_outside_train_do_not_change_it(dataset, tmp_path):
    first = build_training_idf(dataset, tmp_path/'idf-a')
    modified = clone_unsealed(dataset, tmp_path)
    sources = read_jsonl(modified/'sources.jsonl')
    for source in sources:
        if source['split'] != 'train':
            source['title'] += ' metadata changed outside train'
            suffix = ' Conteúdo exclusivo da alteração fora do treino.'
            source['text'] += suffix
            for layer in ('raw', 'extracted', 'normalized'):
                target = modified/source[f'{layer}_file']
                target.write_bytes(target.read_bytes() + suffix.encode())
                source[f'{layer}_sha256'] = digest(target.read_bytes())
    replace_jsonl(modified, 'sources.jsonl', sources)
    seal(modified, verify_seal(dataset)['metadata'])
    second = build_training_idf(modified, tmp_path/'idf-b')
    assert first['n_docs'] == second['n_docs'] == 14
    assert (tmp_path/'idf-a/idf.json').read_bytes() == (tmp_path/'idf-b/idf.json').read_bytes()
    descriptor = read_json(tmp_path/'idf-a/construction.json')
    allowed = {s['id'] for s in sources if s['split'] == 'train'}
    assert {s['id'] for s in descriptor['training_sources']} == allowed
    assert descriptor['construction_attestation'] is True
    assert validate_training_idf(dataset, tmp_path/'idf-a')['sources'] == 14
    descriptor['training_sources'].append(next(s for s in sources if s['split'] == 'test'))
    (tmp_path/'idf-a/construction.json').write_bytes(canonical(descriptor))
    with pytest.raises(ValueError, match='dados de teste'):
        validate_training_idf(dataset, tmp_path/'idf-a')


def test_final_test_guard_and_inference_allowlist(dataset):
    with pytest.raises(PermissionError, match='teste final'):
        evaluation_inputs(dataset, 'test')
    data = evaluation_inputs(dataset, 'train')
    assert data and all(set(row) == {'id', 'text'} for row in data)


def test_mock_llm_cache_no_network_replay_and_wrong_prompt(tmp_path):
    spec = request_spec('fixture-model', 'fixture-revision', 'llm_direct', [{'id': 'a', 'text': 'A casa é azul.'}], {'temperature': 0})
    limits = {'approved': True, 'approval_reference': 'unit-test-only', 'max_calls': 2, 'max_attempts': 1, 'max_output_tokens': 100}
    calls = []
    def transport(request, budget):
        calls.append(1)
        return {'raw': {'fixture': True}, 'text': '{"sentences":[{"text":"A moradia é azul.","source_sentence_ids":["a"]}]}'}
    response = generate_candidate(spec, tmp_path/'cache', limits, transport)
    assert response['status'] == 'candidate' and response['synthetic_fixture'] is True
    replay = generate_candidate(spec, tmp_path/'cache', limits, transport)
    assert replay['request_id'] == response['request_id'] and len(calls) == 1
    with pytest.raises(ValueError, match='outro prompt'):
        validate_cached(response, {**spec, 'model': 'other'})
    with pytest.raises(ValueError, match='fixture'):
        validate_cached(response, spec)


def test_llm_failure_preserved_budget_enforced(tmp_path):
    spec = request_spec('fixture', 'fixture', 'llm_direct', [{'id': 'a', 'text': 'Texto.'}], {})
    limits = {'approved': True, 'approval_reference': 'unit-test-only', 'max_calls': 1, 'max_attempts': 1, 'max_output_tokens': 100}
    def failed(*args):
        raise OSError('fake boundary failure')
    response = generate_candidate(spec, tmp_path/'cache', limits, failed)
    assert response['status'] == 'failed' and response['error']['type'] == 'OSError'
    assert len(list((tmp_path/'cache').glob('*.json'))) == 1
    assert len(list((tmp_path/'cache').glob('*.request'))) == 1
    with pytest.raises(PermissionError):
        generate_candidate(spec, tmp_path/'cache', limits, failed)
    with pytest.raises(PermissionError):
        generate_candidate(spec, tmp_path/'none', {'approved': False})


def test_format_split_is_not_an_independent_observation(dataset, tmp_path):
    from hts_core.adapters.dataset_formats import add_formats
    path = tmp_path/'formatted'
    add_formats(dataset, path, limit=1)
    assert validate_data(path)['formats'] == 3
    entries = read_jsonl(path/'formats.jsonl')
    assert len({r['content_id'] for r in entries}) == 1
    bad = clone_unsealed(path, tmp_path/'modified')
    entries[0]['split'] = 'test' if entries[0]['split'] != 'test' else 'train'
    replace_jsonl(bad, 'formats.jsonl', entries)
    with pytest.raises(ValueError, match='formato em outro split'):
        validate_data(bad, sealed=False)


def test_fixed_collection_mock_records_real_boundary_failure(tmp_path):
    from hts_core.adapters.dataset_collect import collect_fixed
    rights = {'query': {'rightsinfo': {'text': 'fixture license', 'url': 'https://example.invalid/license'}}}
    def mock(params):
        if params.get('meta'):
            return canonical(rights)
        return canonical({'query': {'pages': [{'pageid': 9, 'title': 'Fixture', 'revisions': [{
            'revid': 11, 'timestamp': '2026-10-24T00:00:00Z', 'slots': {'main': {'content': 'Texto público de fixture.'}}}]}]}})
    result = collect_fixed([{'pageid': 9, 'revid': 11}], tmp_path/'good', mock, pause=0)
    assert result['collected'] == 1
    assert read_json(tmp_path/'good/manifest.json')['documents'][0]['sha256'] == hashlib.sha256('Texto público de fixture.'.encode()).hexdigest()
    with pytest.raises(ValueError, match='incompleta'):
        collect_fixed([{'pageid': 99, 'revid': 11}], tmp_path/'bad', mock, pause=0)
    assert read_json(tmp_path/'bad/collection-failures.json')[0]['type'] == 'ValueError'


def test_full_generation_requires_explicit_decision(dataset, tmp_path):
    config = read_json(dataset/'config.json')
    config['purpose'] = 'experimental_candidate'
    with pytest.raises(PermissionError, match='contrato experimental'):
        build_local(config, tmp_path/'no-corpus', tmp_path/'not-generated')
    assert not (tmp_path/'not-generated').exists()


def test_paid_api_not_required_and_not_authorized_by_default(tmp_path):
    spec = request_spec('not-authorized', 'not-authorized', 'llm_direct', [{'id': 'a', 'text': 'Texto.'}], {})
    with pytest.raises(PermissionError, match='orçamento'):
        generate_candidate(spec, tmp_path/'disabled', {'approved': False})


def test_codex_session_fixture_is_distinct_from_api_and_not_reusable_as_real(tmp_path):
    from hts_core.adapters.dataset_llm import record_session_candidate, session_candidate_spec
    spec = session_candidate_spec('llm_direct', [{'id': 'a', 'text': 'A casa é azul.'}])
    raw = '{"sentences":[{"text":"A moradia é azul.","source_sentence_ids":["a"]}]}'
    record = record_session_candidate(spec, raw, tmp_path, 'fixture-codex', synthetic_fixture=True)
    assert record['status'] == 'candidate' and record['request']['provider'] == 'Codex-session'
    assert record['usage'] is None and record['cost'] is None
    with pytest.raises(ValueError, match='fixture'):
        validate_cached(record, spec)


def test_eight_item_review_pilot_keeps_responses_blank(dataset, tmp_path):
    package = tmp_path/'eight'
    result = prepare_review(dataset, package, 7, pilot_count=8)
    assert result['items'] == 8
    assert all(not row['decision'] for row in read_jsonl(package/'items.jsonl'))
    assert all(row['source_id'] in {s['source_id'] for s in row['source_texts']} for row in read_jsonl(package/'items.jsonl'))
    assert 'Fonte focal:' in (package/'revisao.html').read_text(encoding='utf-8')
    assert '<script' not in (package/'revisao.html').read_text(encoding='utf-8')


def test_fraction_for_patchwork_each_source_is_verified(dataset, tmp_path):
    path = clone_unsealed(dataset, tmp_path)
    pairs = read_jsonl(path/'pairs.jsonl')
    pair = next(p for p in pairs if p['synthetic_type'] == 'C4')
    other = next(s for s in pair['source_ids'] if s != pair['source_id'])
    pair['r_by_source'][other]['numerator'] += 1
    replace_jsonl(path, 'pairs.jsonl', pairs)
    with pytest.raises(ValueError, match='r por fonte'):
        validate_data(path, sealed=False)
