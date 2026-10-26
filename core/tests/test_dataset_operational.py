from copy import deepcopy
from datetime import datetime, timezone
import json

import pytest

from tests.test_dataset_s4 import dataset, clone_unsealed, replace_jsonl, CORE
from hts_core.adapters.dataset_formats import add_formats
from hts_core.adapters.dataset_llm import session_candidate_spec, record_session_candidate
from hts_core.adapters.dataset_operational import verify_source_origin, coverage
from hts_core.adapters.dataset_review import prepare_automated_review, import_automated_review, freeze
from hts_core.adapters.dataset_store import canonical, digest, identity, read_json, read_jsonl, seal, write_json, write_jsonl, write_new, export_bundle, import_bundle
from hts_core.adapters.dataset_validation import validate_data
from hts_core.application.dataset_pipeline import add_cached_candidates, build_local


@pytest.fixture(scope='module')
def operational_fixture(tmp_path_factory):
    # Tudo nesta fixture é artificial; nenhuma revisão humana/IA real é declarada.
    root = tmp_path_factory.mktemp('ARTIFICIAL-operational')
    corpus = root/'corpus'
    entries = []
    themes = {}
    for i in range(28):
        label = 'amostra' + chr(97 + i // 26) + chr(97 + i % 26)
        text = ' '.join(f'O {label} descreve fenômenos {label} da região {label} com exemplo {word}.' for word in ('primeiro', 'segundo', 'terceiro', 'quarto'))
        name = f'raw/{i}.wiki'
        write_new(corpus/name, text.encode('utf-8'))
        entries.append({'pageid': i, 'revid': i + 100, 'title': f'Fixture {i}', 'url': 'https://example.invalid/development',
                        'history_url': 'https://example.invalid/development/history', 'license': 'project-authored-test-fixture',
                        'retrieved_at': '2026-10-24T00:00:00+00:00', 'file': name, 'sha256': digest(text.encode('utf-8'))})
        themes[f'Fixture {i}'] = str(i % 2)
    write_json(corpus/'manifest.json', {'documents': entries})
    pilot_config = read_json(CORE/'configs/dataset_pilot.json')
    pilot_config.update(themes=themes, segment_sentences=4)
    synthetic = root/'synthetic'
    build_local(pilot_config, corpus, synthetic)
    folder = clone_unsealed(synthetic, root)
    config = read_json(CORE/'configs/dataset_operational.json')
    old_config = read_json(folder/'config.json')
    config.update(themes=old_config['themes'], segment_sentences=4, authorization_reference='ARTIFICIAL-UNIT-ONLY', record_contract='assessment_v2')
    (folder/'config.json').write_bytes(canonical(config))
    upstream = read_json(folder/'upstream-manifest.json')
    rights = canonical({'query': {'rightsinfo': {'text': 'project-authored-test-fixture', 'url': 'https://example.invalid/license'}}})
    write_new(folder/'provenance/rightsinfo-response.json', rights)
    upstream['rightsinfo_sha256'] = digest(rights)
    for e in upstream['documents']:
        e['license_reference'] = 'https://example.invalid/license'
        e['response_file'] = f"responses/{e['pageid']}.json"
        source_text = (folder/f"sources/wikipedia-pt-{e['pageid']}-{e['revid']}.wiki").read_text(encoding='utf-8')
        response = canonical({'query': {'pages': [{'pageid': e['pageid'], 'title': e['title'], 'revisions': [{'revid': e['revid'], 'slots': {'main': {'content': source_text}}}]}]}})
        e['response_sha256'] = digest(response)
        write_new(folder/'provenance'/e['response_file'], response)
    (folder/'upstream-manifest.json').write_bytes(canonical(upstream))
    sources = read_jsonl(folder/'sources.jsonl')
    for s in sources:
        s.update(license_status='source_verified', license_reference='https://example.invalid/license', exposure='construction_inspected_no_predictive_use')
        s['provenance_verification'] = verify_source_origin(s, folder)
    replace_jsonl(folder, 'sources.jsonl', sources)
    from hts_core.application.dataset_pipeline import initialize_pair_states
    pairs = read_jsonl(folder/'pairs.jsonl')
    for pair in pairs:
        initialize_pair_states(pair)
    replace_jsonl(folder, 'pairs.jsonl', pairs)
    seal(folder, {'purpose': 'operational_derivation', 'config_identity': identity(config)})
    selected = {}
    for s in sorted(sources, key=lambda s: s['id']):
        selected.setdefault((s['split'], s['theme']), s)
    records = []
    for number, s in enumerate(selected.values()):
        inputs = [{'id': r['id'], 'text': r['text']} for r in s['sentences'][:2]]
        parent = None
        for key, method in [('direct', 'llm_direct'), ('en', 'translate_to_en'), ('back', 'translate_to_pt'), ('c6', 'phrase_guided_rewrite')]:
            given, context = inputs, None
            if key == 'back':
                assert parent is not None
                given = [{'id': r['source_sentence_ids'][0], 'text': r['text']} for r in parent['structured']['sentences']]
                context = {'parent_cache_key': parent['cache_key']}
            if key == 'c6':
                given = inputs[:1]
                context = {'source_phrase': given[0]['text'], 'keywords': [given[0]['text'].split()[1]], 'approval_reference': 'ARTIFICIAL-UNIT-ONLY'}
            spec = session_candidate_spec(method, given, context)
            raw = json.dumps({'sentences': [{'text': (inputs[i]['text'].replace('descreve', {'direct': 'apresenta', 'en': 'registra', 'back': 'relata', 'c6': 'explica'}[key])), 'source_sentence_ids': [r['id']]} for i, r in enumerate(given)]})
            record = record_session_candidate(spec, raw, root/'cache', f'fixture-{number}-{key}')
            records.append(record)
            if key == 'en':
                parent = record
    cached = root/'cached'
    add_cached_candidates(folder, records, cached)
    formatted = root/'formatted'
    add_formats(cached, formatted)
    package = root/'package'
    prepare_automated_review(formatted, package)
    package_manifest = read_json(package/'manifest.json')
    responses = [{'id': item['id'], 'decision': 'accept', 'reason': 'ARTIFICIAL fixture; not real AI assessment',
                  'date': '2026-10-24T00:00:00+00:00', 'procedure': 'unit-fixture', 'interface': 'ARTIFICIAL',
                  'model_revision': None, 'prompt_sha256': package_manifest['files']['prompt.txt'], 'item_sha256': identity(item),
                  'generator_relation': 'artificial_fixture_not_independent', 'limitations': ['ARTIFICIAL unit test only'], 'findings': []}
                 for item in read_jsonl(package/'items.jsonl')]
    write_jsonl(root/'ARTIFICIAL-responses.jsonl', responses)
    imported = root/'review-imported'
    import_automated_review(package, root/'ARTIFICIAL-responses.jsonl', imported)
    version = read_json(formatted/'manifest.json')['version']
    auth = {'purpose': 'operational_derivation', 'approved': True, 'reference': 'ARTIFICIAL-UNIT-ONLY',
            'review_scope_accepted': True, 'source_alerts_resolved': True, 'cache_verified': True, 'reproduction_verified': True,
            'reproduction': {'original_version': version, 'reconstructed_version': version, 'hashseeds': ['1', '917'], 'isolated_public_copy': True,
                             'file_inventory_sha256': identity(read_json(formatted/'manifest.json')['files'])}}
    return formatted, imported, auth, package


def test_operational_freeze_positive_and_portable(operational_fixture, tmp_path):
    folder, review, auth, _ = operational_fixture
    result = freeze(folder, review, auth, tmp_path/'frozen')
    assert result['metadata']['purpose'] == 'frozen_operational_derivation'
    assert result['metadata']['human_review'] == 'not_performed'
    assert result['metadata']['semantic_training_ready'] is False
    assert validate_data(tmp_path/'frozen')['pairs'] == coverage(folder)['pairs']
    export_bundle(tmp_path/'frozen', tmp_path/'bundle.zip')
    restored = import_bundle(tmp_path/'bundle.zip', tmp_path/'restored')
    assert restored == result
    assert read_json(tmp_path/'restored/review.json')['modality'] == 'automated_ai'


def test_documented_exclusion_preserves_real_shaped_cache_in_new_version(operational_fixture, tmp_path):
    from hts_core.adapters.dataset_operational import excluded_pair_from_cache, validate_content_exclusion
    from hts_core.adapters.dataset_review import review_item
    folder, _, _, _ = operational_fixture
    sources = {s['id']: s for s in read_jsonl(folder/'sources.jsonl')}
    records = [read_json(p) for p in (folder/'cache').glob('*.json')]
    selected = next(r for r in records if r['request']['method'] == 'llm_direct')
    pair = excluded_pair_from_cache(selected, {r['cache_key']: r for r in records}, sources, read_json(folder/'config.json'))
    item = review_item(pair, sources)
    exclusion = {'request_id': selected['request_id'], 'pair_id': pair['id'], 'review_dataset_version': read_json(folder/'manifest.json')['version'],
                 'review_identity': 'ARTIFICIAL-review', 'item': item,
                 'response': {'id': pair['id'], 'item_sha256': identity(item), 'decision': 'reject', 'reason': 'ARTIFICIAL unit rejection, not an actual assessment',
                              'generator_relation': 'same_agent_as_generator_not_independent', 'date': '2026-10-24T00:00:00+00:00',
                              'findings': [{'source_quote': item['source_texts'][0]['text'][:20], 'output_quote': pair['text'][:20]}]}}
    assert validate_content_exclusion(exclusion, pair, sources) == exclusion
    bad = deepcopy(exclusion)
    bad['response']['findings'][0]['output_quote'] = 'NONEXISTENT-QUOTE'
    with pytest.raises(ValueError, match='trechos'):
        validate_content_exclusion(bad, pair, sources)
    parent = tmp_path/'parent'
    parent.mkdir()
    manifest = read_json(folder/'manifest.json')
    pairs = [p for p in read_jsonl(folder/'pairs.jsonl') if p['synthetic_type'] not in {'C5', 'C6'}]
    for name in manifest['files']:
        if not name.startswith(('cache/', 'formats/')) and name not in {'pairs.jsonl', 'formats.jsonl', 'format-failures.json', 'validation.json', 'llm-rejections.json', 'content-exclusions.json'}:
            write_new(parent/name, (folder/name).read_bytes())
    write_jsonl(parent/'pairs.jsonl', pairs)
    seal(parent, {'purpose': 'operational_derivation'})
    result = add_cached_candidates(parent, records, tmp_path/'with-exclusion', [exclusion])
    assert result['metadata']['cache_rejections'] == 0
    assert result['metadata']['documented_content_exclusions'] == 1
    assert pair['id'] not in {p['id'] for p in read_jsonl(tmp_path/'with-exclusion/pairs.jsonl')}
    assert (tmp_path/'with-exclusion/cache'/f"{selected['request_id']}.json").read_bytes() == (folder/'cache'/f"{selected['request_id']}.json").read_bytes()
    assert validate_data(tmp_path/'with-exclusion')['pairs'] == len(read_jsonl(folder/'pairs.jsonl')) - 1


@pytest.mark.parametrize('mutation', ['cache', 'formats'])
def test_frozen_version_refuses_mutation_before_creating_destination(operational_fixture, tmp_path, mutation):
    folder, review, auth, _ = operational_fixture
    freeze(folder, review, auth, tmp_path/'frozen')
    with pytest.raises(PermissionError, match='congelada'):
        if mutation == 'cache':
            add_cached_candidates(tmp_path/'frozen', [], tmp_path/'invalid-child')
        else:
            add_formats(tmp_path/'frozen', tmp_path/'invalid-child')
    assert not (tmp_path/'invalid-child').exists()


def test_frozen_states_are_individual_and_migration_is_lossless(operational_fixture, tmp_path):
    folder, review_folder, auth, _ = operational_fixture
    frozen = tmp_path/'frozen'
    freeze(folder, review_folder, auth, frozen)
    assert (frozen/'construction-pairs.jsonl').read_bytes() == (folder/'pairs.jsonl').read_bytes()
    responses = {r['id'] for r in read_json(review_folder/'review.json')['responses']}
    pairs = read_jsonl(frozen/'pairs.jsonl')
    assert {p['id'] for p in pairs if p['content_assessment']['status'] == 'accept'} == responses
    assert any(p['content_assessment']['status'] == 'not_assessed' for p in pairs)
    assert all(p['human_review'] == 'not_performed' for p in pairs)
    assert all(r['validation'] == 'structural' for p in pairs for r in p['sentences'])
    assert validate_data(frozen)['pairs'] == len(pairs)
    invalid = clone_unsealed(frozen, tmp_path)
    pairs[0]['content_assessment']['status'] = 'not_assessed' if pairs[0]['id'] in responses else 'accept'
    replace_jsonl(invalid, 'pairs.jsonl', pairs)
    seal(invalid, read_json(frozen/'manifest.json')['metadata'])
    with pytest.raises(ValueError, match='avaliação individual'):
        validate_data(invalid)


def test_real_requirements_honor_minimum_in_config(operational_fixture, tmp_path):
    from hts_core.adapters.dataset_operational import verify_operational_requirements
    folder, _, auth, _ = operational_fixture
    invalid = clone_unsealed(folder, tmp_path)
    config = read_json(invalid/'config.json')
    config['generated_policy']['minimum_pairs_per_method_split_theme'] = 2
    (invalid/'config.json').write_bytes(canonical(config))
    seal(invalid, {'purpose': 'operational_derivation'})
    with pytest.raises(ValueError, match='mínimo=2, real=1'):
        verify_operational_requirements(invalid, auth)


@pytest.mark.parametrize('field,value', [('maximum_sources', 1), ('maximum_records', 1), ('source_sentences', 3)])
def test_generation_contract_enforces_limits_and_input_count(operational_fixture, field, value):
    from hts_core.adapters.dataset_operational import verify_generation_contract
    folder, _, _, _ = operational_fixture
    policy = deepcopy(read_json(folder/'config.json')['generated_policy'])
    policy[field] = value
    with pytest.raises(ValueError, match='limite|quantidade'):
        verify_generation_contract(folder, read_jsonl(folder/'sources.jsonl'), policy)


def test_backtranslation_fallback_requires_final_method_rejection(operational_fixture, tmp_path):
    from hts_core.adapters.dataset_operational import verify_generation_contract
    folder, _, _, _ = operational_fixture
    sources = read_jsonl(folder/'sources.jsonl')
    cells = {}
    for source in sorted(sources, key=lambda s: s['id']):
        cells.setdefault((source['split'], source['theme']), []).append(source)
    first, replacement = next(cell[:2] for cell in cells.values() if len(cell) > 1)
    target = clone_unsealed(folder, tmp_path)
    inputs = [{'id': r['id'], 'text': r['text']} for r in replacement['sentences'][:2]]
    parent = None
    for method in ('translate_to_en', 'translate_to_pt'):
        context = {'parent_cache_key': parent['cache_key']} if parent else None
        spec = session_candidate_spec(method, inputs, context)
        raw = json.dumps({'sentences': [{'text': r['text'], 'source_sentence_ids': [r['id']]} for r in inputs]})
        parent = record_session_candidate(spec, raw, target/'cache', 'ARTIFICIAL-fallback-' + method)
    policy = read_json(folder/'config.json')['generated_policy']
    with pytest.raises(ValueError, match='fallback'):
        verify_generation_contract(target, sources, policy)
    original = next(read_json(p) for p in (folder/'cache').glob('*.json')
                    if read_json(p)['request']['method'] == 'translate_to_pt'
                    and read_json(p)['request']['input'][0]['id'] == first['sentences'][0]['id'])
    exclusion = {'request_id': original['request_id'], 'item': {'source_id': first['id'], 'method': 'llm_direct'}}
    (target/'content-exclusions.json').write_bytes(canonical([exclusion]))
    with pytest.raises(ValueError, match='fallback'):
        verify_generation_contract(target, sources, policy)
    exclusion['item']['method'] = 'backtranslation'
    (target/'content-exclusions.json').write_bytes(canonical([exclusion]))
    verify_generation_contract(target, sources, policy)


@pytest.mark.parametrize('corruption', ['unknown', 'duplicate', 'missing', 'version', 'text', 'selection', 'required_field', 'modality', 'reject', 'ambiguous', 'prompt', 'purpose', 'reproduction', 'reproduction_version', 'forged_coverage', 'forged_text', 'forged_id'])
def test_operational_freeze_negative_controls(operational_fixture, tmp_path, corruption):
    folder, imported, authorization, _ = operational_fixture
    review, auth = read_json(imported/'review.json'), deepcopy(authorization)
    if corruption == 'unknown':
        review['responses'][0]['id'] = 'missing'
    elif corruption == 'duplicate':
        review['responses'].append(review['responses'][0])
    elif corruption == 'missing':
        review['responses'].pop()
    elif corruption == 'version':
        review['dataset_version'] = 'wrong'
    elif corruption == 'text':
        review['items'][0]['transformed_text'] = 'Changed text.'
    elif corruption == 'selection':
        review['selection']['expected_ids'].pop()
    elif corruption == 'required_field':
        review['responses'][0].pop('limitations')
    elif corruption == 'modality':
        review['modality'] = 'human_individual'
    elif corruption in {'reject', 'ambiguous'}:
        review['responses'][0]['decision'] = corruption
    elif corruption == 'prompt':
        review['responses'][0]['prompt_sha256'] = 'wrong'
    elif corruption == 'purpose':
        auth['purpose'] = 'semantic_training'
    elif corruption == 'reproduction':
        auth['reproduction'] = {}
    elif corruption == 'reproduction_version':
        auth['reproduction']['reconstructed_version'] = 'wrong'
    elif corruption == 'forged_coverage':
        removed = review['items'].pop(0)['id']
        review['responses'] = [r for r in review['responses'] if r['id'] != removed]
        review['selection']['expected_ids'].remove(removed)
    elif corruption == 'forged_text':
        review['items'][0]['transformed_text'] = 'Forged content with consistent self hashes.'
    else:
        previous = review['items'][0]['id']
        review['items'][0]['id'] = 'NONEXISTENT-ID'
        review['selection']['expected_ids'] = ['NONEXISTENT-ID' if i == previous else i for i in review['selection']['expected_ids']]
        next(r for r in review['responses'] if r['id'] == previous)['id'] = 'NONEXISTENT-ID'
    if corruption.startswith('forged_'):
        for row in review['responses']:
            row['item_sha256'] = identity(next(i for i in review['items'] if i['id'] == row['id']))
        review['items_sha256'] = digest(b''.join(canonical(i) for i in review['items']))
        pm = review['package_manifest']
        pm['files']['items.jsonl'] = review['items_sha256']
        pm['files']['selection.json'] = identity(review['selection'])
        pm['version'] = identity({k: v for k, v in pm.items() if k != 'version'})
    review['source_responses_text'] = ''.join(canonical(r).decode('utf-8') for r in review['responses'])
    review['source_responses_sha256'] = digest(review['source_responses_text'].encode('utf-8'))
    review['identity'] = identity({k: v for k, v in review.items() if k != 'identity'})
    write_json(tmp_path/'review/review.json', review)
    with pytest.raises((ValueError, PermissionError)):
        freeze(folder, tmp_path/'review', auth, tmp_path/'must-not-freeze')
    assert not (tmp_path/'must-not-freeze').exists()
